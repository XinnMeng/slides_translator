from __future__ import annotations

import sys
import types

from pptx_translator.translator import check_argos_model_availability


class FakeLanguage:
    def __init__(self, code: str):
        self.code = code
        self._pairs = {}

    def set_pair(self, other: "FakeLanguage"):
        self._pairs[other.code] = object()

    def get_translation(self, other):
        if other is None:
            return None
        return self._pairs.get(other.code)


def _install_fake_translate_module(monkeypatch, languages: list[FakeLanguage]) -> None:
    translate_mod = types.ModuleType("argostranslate.translate")
    translate_mod.get_installed_languages = lambda: languages

    root_mod = types.ModuleType("argostranslate")
    root_mod.translate = translate_mod

    monkeypatch.setitem(sys.modules, "argostranslate", root_mod)
    monkeypatch.setitem(sys.modules, "argostranslate.translate", translate_mod)


def test_check_argos_model_direct(monkeypatch) -> None:
    ja = FakeLanguage("ja")
    zh = FakeLanguage("zh")
    ja.set_pair(zh)
    _install_fake_translate_module(monkeypatch, [ja, zh])

    ok, msg = check_argos_model_availability("ja", "zh")
    assert ok
    assert "Direct Argos model available" in msg


def test_check_argos_model_pivot(monkeypatch) -> None:
    ja = FakeLanguage("ja")
    en = FakeLanguage("en")
    zh = FakeLanguage("zh")
    ja.set_pair(en)
    en.set_pair(zh)
    _install_fake_translate_module(monkeypatch, [ja, en, zh])

    ok, msg = check_argos_model_availability("ja", "zh", pivot_lang="en")
    assert ok
    assert "pivot models available" in msg
