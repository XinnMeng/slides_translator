from __future__ import annotations

import logging
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


def normalize_lang_code(lang: str) -> str:
    mapping = {
        "zh-CN": "zh",
        "zh-Hans": "zh",
    }
    return mapping.get(lang, lang)


@dataclass
class ArgosTranslateBackend(TranslatorBackend):
    auto_install_package: bool = False
    pivot_language: str = "en"

    def _import_argos_modules(self):
        try:
            import argostranslate.package as argos_package
            import argostranslate.translate as argos_translate
        except Exception as exc:
            raise RuntimeError("Argos Translate is not installed. Install dependency `argostranslate`.") from exc
        return argos_package, argos_translate

    @staticmethod
    def _find_language(installed_languages, code: str):
        return next((lang for lang in installed_languages if lang.code == code), None)

    def _install_pair_if_needed(self, argos_package, source_lang: str, target_lang: str) -> None:
        if not self.auto_install_package:
            raise RuntimeError(
                f"No Argos package installed for {source_lang}->{target_lang}. "
                "Install language packages or run with auto-install enabled."
            )

        argos_package.update_package_index()
        available_packages = argos_package.get_available_packages()
        package_to_install = next(
            (pkg for pkg in available_packages if pkg.from_code == source_lang and pkg.to_code == target_lang),
            None,
        )
        if package_to_install is None:
            raise RuntimeError(f"No Argos package found for {source_lang}->{target_lang}")

        downloaded_path = package_to_install.download()
        argos_package.install_from_path(downloaded_path)

    def _ensure_direct_translation(self, argos_package, argos_translate, source_lang: str, target_lang: str):
        installed_languages = argos_translate.get_installed_languages()
        from_lang = self._find_language(installed_languages, source_lang)
        to_lang = self._find_language(installed_languages, target_lang)

        translation = from_lang.get_translation(to_lang) if (from_lang and to_lang) else None
        if translation:
            return translation

        self._install_pair_if_needed(argos_package, source_lang, target_lang)

        installed_languages = argos_translate.get_installed_languages()
        from_lang = self._find_language(installed_languages, source_lang)
        to_lang = self._find_language(installed_languages, target_lang)
        translation = from_lang.get_translation(to_lang) if (from_lang and to_lang) else None
        if not translation:
            raise RuntimeError(f"Argos package installed but translation missing for {source_lang}->{target_lang}")
        return translation

    def translate_text(self, text: str, source_lang: str, target_lang: str) -> str:
        source_norm = normalize_lang_code(source_lang)
        target_norm = normalize_lang_code(target_lang)
        pivot_norm = normalize_lang_code(self.pivot_language)

        argos_package, argos_translate = self._import_argos_modules()

        installed_languages = argos_translate.get_installed_languages()
        from_lang = self._find_language(installed_languages, source_norm)
        to_lang = self._find_language(installed_languages, target_norm)
        direct = from_lang.get_translation(to_lang) if (from_lang and to_lang) else None

        if direct is not None:
            logger.info("Using direct model: %s -> %s", source_norm, target_norm)
            return direct.translate(text)

        logger.info("Direct model not found, using pivot: %s -> %s -> %s", source_norm, pivot_norm, target_norm)
        leg1 = self._ensure_direct_translation(argos_package, argos_translate, source_norm, pivot_norm)
        leg2 = self._ensure_direct_translation(argos_package, argos_translate, pivot_norm, target_norm)
        return leg2.translate(leg1.translate(text))


def build_backend(
    backend: str,
    libretranslate_url: str,
    libretranslate_api_key: str | None,
    argos_auto_install: bool,
    argos_pivot_lang: str = "en",
) -> TranslatorBackend:
    if backend in {"argos", "offline_argos"}:
        return ArgosTranslateBackend(auto_install_package=argos_auto_install, pivot_language=argos_pivot_lang)
    if backend == "libretranslate":
        return LibreTranslateBackend(endpoint=libretranslate_url, api_key=libretranslate_api_key)
    raise ValueError(f"Unsupported backend: {backend}")
