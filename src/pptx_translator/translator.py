from __future__ import annotations

import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass

import requests

from .models import TextItem, Translation, TranslationBatchResult, text_item_id

logger = logging.getLogger(__name__)


class TranslatorBackend(ABC):
    @abstractmethod
    def translate_text(self, text: str, source_lang: str, target_lang: str) -> str:
        raise NotImplementedError

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

            if source_lang == "de" and looks_english(original):
                translations.append(Translation(id=key, translated_text=original))
                continue

            try:
                translated_text = self.translate_text(original, source_lang=source_lang, target_lang=target_lang)
            except Exception as exc:
                logger.warning("Translation failed for item %s; keeping original. Error: %s", key, exc)
                translated_text = original

            translations.append(Translation(id=key, translated_text=translated_text))

        return TranslationBatchResult(translations=translations)


@dataclass
class LibreTranslateBackend(TranslatorBackend):
    endpoint: str
    api_key: str | None = None
    timeout_seconds: int = 30

    def _request_translate(self, text: str, source_lang: str, target_lang: str) -> str:
        payload = {
            "q": text,
            "source": source_lang,
            "target": target_lang,
            "format": "text",
        }
        if self.api_key:
            payload["api_key"] = self.api_key

        # Many LibreTranslate deployments expect form data. Try form first,
        # then JSON as fallback for compatible forks.
        attempts = [
            ("form", {"data": payload}),
            ("json", {"json": payload}),
        ]

        last_error: Exception | None = None
        for mode, kwargs in attempts:
            response = requests.post(self.endpoint, timeout=self.timeout_seconds, **kwargs)
            if response.ok:
                data = response.json()
                translated = data.get("translatedText")
                if not isinstance(translated, str):
                    raise ValueError(f"Unexpected translation response format: {data}")
                return translated

            logger.error(
                "LibreTranslate %s request failed. status=%s body=%s",
                mode,
                response.status_code,
                response.text,
            )
            last_error = RuntimeError(f"LibreTranslate {mode} request failed with status {response.status_code}")

        if last_error is not None:
            raise last_error
        raise RuntimeError("LibreTranslate request failed")

    def translate_text(self, text: str, source_lang: str, target_lang: str) -> str:
        return self._request_translate(text=text, source_lang=source_lang, target_lang=target_lang)


@dataclass
class ArgosTranslateBackend(TranslatorBackend):
    auto_install_package: bool = False

    def _load_translation(self, source_lang: str, target_lang: str):
        try:
            import argostranslate.package
            import argostranslate.translate
        except Exception as exc:
            raise RuntimeError(
                "Argos Translate is not installed. Install dependency `argostranslate`."
            ) from exc

        installed_languages = argostranslate.translate.get_installed_languages()

        from_lang = next((lang for lang in installed_languages if lang.code == source_lang), None)
        to_lang = next((lang for lang in installed_languages if lang.code == target_lang), None)

        if from_lang and to_lang:
            translation = from_lang.get_translation(to_lang)
            if translation:
                return translation

        if not self.auto_install_package:
            raise RuntimeError(
                f"No Argos package installed for {source_lang}->{target_lang}. "
                "Install a language package or run with auto-install enabled."
            )

        # Optional online install path for convenience.
        argostranslate.package.update_package_index()
        available_packages = argostranslate.package.get_available_packages()
        package_to_install = next(
            (
                pkg
                for pkg in available_packages
                if pkg.from_code == source_lang and pkg.to_code == target_lang
            ),
            None,
        )
        if package_to_install is None:
            raise RuntimeError(f"No Argos package found for {source_lang}->{target_lang}")

        downloaded_path = package_to_install.download()
        argostranslate.package.install_from_path(downloaded_path)

        installed_languages = argostranslate.translate.get_installed_languages()
        from_lang = next((lang for lang in installed_languages if lang.code == source_lang), None)
        to_lang = next((lang for lang in installed_languages if lang.code == target_lang), None)
        if not from_lang or not to_lang:
            raise RuntimeError(f"Argos package install did not provide {source_lang}->{target_lang}")

        translation = from_lang.get_translation(to_lang)
        if not translation:
            raise RuntimeError(f"Argos package installed but translation missing for {source_lang}->{target_lang}")

        return translation

    def translate_text(self, text: str, source_lang: str, target_lang: str) -> str:
        translation = self._load_translation(source_lang=source_lang, target_lang=target_lang)
        return translation.translate(text)


def build_backend(
    backend: str,
    libretranslate_url: str,
    libretranslate_api_key: str | None,
    argos_auto_install: bool,
) -> TranslatorBackend:
    if backend == "argos":
        return ArgosTranslateBackend(auto_install_package=argos_auto_install)
    if backend == "libretranslate":
        return LibreTranslateBackend(endpoint=libretranslate_url, api_key=libretranslate_api_key)
    raise ValueError(f"Unsupported backend: {backend}")


def looks_english(text: str) -> bool:
    if any(ch in text for ch in "äöüÄÖÜß"):
        return False
    letters = re.findall(r"[A-Za-z]", text)
    if not letters:
        return True
    ascii_ratio = len(letters) / max(len(text), 1)
    return ascii_ratio > 0.5
