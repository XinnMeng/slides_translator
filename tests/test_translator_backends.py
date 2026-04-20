from __future__ import annotations

import sys
import types

from pptx_translator.translator import ArgosTranslateBackend, LibreTranslateBackend, build_backend


class DummyResponse:
    def __init__(self, status_code: int, text: str, data: dict | None = None):
        self.status_code = status_code
        self.text = text
        self._data = data or {}

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300

    def json(self):
        return self._data


def test_build_backend_selects_argos() -> None:
    backend = build_backend(
        backend="argos",
        libretranslate_url="https://example.invalid/translate",
        libretranslate_api_key=None,
        argos_auto_install=False,
        argos_pivot_lang="en",
    )
    assert isinstance(backend, ArgosTranslateBackend)


def test_libretranslate_falls_back_from_form_to_json(monkeypatch) -> None:
    calls: list[dict] = []

    def fake_post(url, timeout, **kwargs):
        calls.append(kwargs)
        if "data" in kwargs:
            return DummyResponse(400, "bad form payload")
        return DummyResponse(200, "ok", data={"translatedText": "Hello world"})

    monkeypatch.setattr("requests.post", fake_post)

    backend = LibreTranslateBackend(endpoint="https://example.invalid/translate")
    out = backend.translate_text("Hallo Welt", source_lang="de", target_lang="en")

    assert out == "Hello world"
    assert len(calls) == 2
    assert "data" in calls[0]
    assert "json" in calls[1]


class FakeTranslation:
    def __init__(self, fn):
        self._fn = fn

    def translate(self, text: str) -> str:
        return self._fn(text)


class FakeLanguage:
    def __init__(self, code: str):
        self.code = code
        self._translations = {}

    def set_translation(self, to_lang: "FakeLanguage", fn):
        self._translations[to_lang.code] = FakeTranslation(fn)

    def get_translation(self, to_lang: "FakeLanguage" | None):
        if to_lang is None:
            return None
        return self._translations.get(to_lang.code)


def _install_fake_argos(monkeypatch, languages: list[FakeLanguage]) -> None:
    translate_mod = types.ModuleType("argostranslate.translate")
    translate_mod.get_installed_languages = lambda: languages

    package_mod = types.ModuleType("argostranslate.package")
    package_mod.update_package_index = lambda: None
    package_mod.get_available_packages = lambda: []
    package_mod.install_from_path = lambda _path: None

    root_mod = types.ModuleType("argostranslate")
    root_mod.translate = translate_mod
    root_mod.package = package_mod

    monkeypatch.setitem(sys.modules, "argostranslate", root_mod)
    monkeypatch.setitem(sys.modules, "argostranslate.translate", translate_mod)
    monkeypatch.setitem(sys.modules, "argostranslate.package", package_mod)


def test_argos_direct_model_exists(monkeypatch) -> None:
    ja = FakeLanguage("ja")
    zh = FakeLanguage("zh")
    ja.set_translation(zh, lambda text: f"直接:{text}")

    _install_fake_argos(monkeypatch, [ja, zh])

    backend = ArgosTranslateBackend(auto_install_package=False, pivot_language="en")
    out = backend.translate_text("こんにちは", source_lang="ja", target_lang="zh")

    assert out == "直接:こんにちは"


def test_argos_pivot_translation_used(monkeypatch) -> None:
    ja = FakeLanguage("ja")
    en = FakeLanguage("en")
    zh = FakeLanguage("zh")

    ja.set_translation(en, lambda text: f"EN({text})")
    en.set_translation(zh, lambda text: f"ZH({text})")

    _install_fake_argos(monkeypatch, [ja, en, zh])

    backend = ArgosTranslateBackend(auto_install_package=False, pivot_language="en")
    out = backend.translate_text("こんにちは", source_lang="ja", target_lang="zh")

    assert out == "ZH(EN(こんにちは))"
