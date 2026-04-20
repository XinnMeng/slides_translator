from __future__ import annotations

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
