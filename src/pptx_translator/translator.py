from __future__ import annotations

import json
import logging
import os
from abc import ABC, abstractmethod

from openai import OpenAI

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


class OpenAIResponsesTranslator(TranslatorBackend):
    def __init__(self, model: str = "gpt-4.1-mini", client: OpenAI | None = None) -> None:
        self.model = model
        self.client = client or OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def translate_items(
        self,
        items: list[TextItem],
        source_lang: str,
        target_lang: str,
    ) -> TranslationBatchResult:
        if not items:
            return TranslationBatchResult(translations=[])

        payload_items = [{"id": text_item_id(item.ref), "text": item.text} for item in items]
        logger.info("Translating %s items with model %s", len(payload_items), self.model)

        response = self.client.responses.create(
            model=self.model,
            input=[
                {
                    "role": "system",
                    "content": (
                        "You translate slide text with high fidelity. "
                        "Only translate text likely in the source language. "
                        "Leave already-English text unchanged. "
                        "Preserve names, acronyms, numbers, and product names where possible. "
                        "Return strict JSON matching the requested schema."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Translate from {source_lang} to {target_lang}. "
                        "For each input item, output one translated entry with same id.\n"
                        f"items={json.dumps(payload_items, ensure_ascii=False)}"
                    ),
                },
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "translation_batch",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "translations": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "string"},
                                        "translated_text": {"type": "string"},
                                    },
                                    "required": ["id", "translated_text"],
                                    "additionalProperties": False,
                                },
                            }
                        },
                        "required": ["translations"],
                        "additionalProperties": False,
                    },
                }
            },
        )

        content = response.output_text
        data = json.loads(content)
        translations = [Translation(id=t["id"], translated_text=t["translated_text"]) for t in data["translations"]]
        return TranslationBatchResult(translations=translations)
