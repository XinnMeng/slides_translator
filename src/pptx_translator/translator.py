from __future__ import annotations

import logging
import re
from abc import ABC, abstractmethod

import requests

from .models import TextItem, Translation, TranslationBatchResult, text_item_id

logger = logging.getLogger(__name__)


class TranslatorBackend(ABC):
    @abstractmethod
    def translate_items(
        self,
        items: list[TextItem],
        source_lang: str,
        target_lang: str,
    ) -> TranslationBatchResult:
        raise NotImplementedError


class LibreTranslateTranslator(TranslatorBackend):
    """
    Free translator backend using LibreTranslate-compatible HTTP API.

    Default endpoint points at the public LibreTranslate instance.
    You can override endpoint/api_key in CLI for self-hosted deployments.
    """

    def __init__(
        self,
        endpoint: str = "https://libretranslate.com/translate",
        api_key: str | None = None,
        timeout_seconds: int = 30,
    ) -> None:
        self.endpoint = endpoint
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    @staticmethod
    def _looks_english(text: str) -> bool:
        # Simple heuristic: if there are no German umlauts/ß and mostly ASCII letters,
        # likely already English and safe to keep.
        if any(ch in text for ch in "äöüÄÖÜß"):
            return False
        letters = re.findall(r"[A-Za-z]", text)
        if not letters:
            return True
        ascii_ratio = len(letters) / max(len(text), 1)
        return ascii_ratio > 0.5

    def _translate_text(self, text: str, source_lang: str, target_lang: str) -> str:
        payload = {
            "q": text,
            "source": source_lang,
            "target": target_lang,
            "format": "text",
        }
        if self.api_key:
            payload["api_key"] = self.api_key

        response = requests.post(self.endpoint, json=payload, timeout=self.timeout_seconds)
        response.raise_for_status()
        data = response.json()
        translated = data.get("translatedText")
        if not isinstance(translated, str):
            raise ValueError(f"Unexpected translation response format: {data}")
        return translated

    def translate_items(
        self,
        items: list[TextItem],
        source_lang: str,
        target_lang: str,
    ) -> TranslationBatchResult:
        translations: list[Translation] = []

        for item in items:
            key = text_item_id(item.ref)
            original = item.text

            # Keep likely-English segments unchanged where possible.
            if source_lang == "de" and self._looks_english(original):
                translations.append(Translation(id=key, translated_text=original))
                continue

            try:
                translated_text = self._translate_text(original, source_lang=source_lang, target_lang=target_lang)
            except Exception as exc:
                logger.warning("Translation failed for item %s; keeping original. Error: %s", key, exc)
                translated_text = original

            translations.append(Translation(id=key, translated_text=translated_text))

        return TranslationBatchResult(translations=translations)
