from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class TextItemRef:
    """Stable pointer to a text-bearing location in a slide."""

    slide_index: int
    shape_index: int
    text_frame_paragraph_index: int | None = None
    table_row_index: int | None = None
    table_col_index: int | None = None
    table_paragraph_index: int | None = None


@dataclass(frozen=True)
class TextItem:
    """Extracted text content and where it came from."""

    ref: TextItemRef
    text: str

    def to_json_dict(self) -> dict:
        payload = asdict(self)
        payload["id"] = text_item_id(self.ref)
        return payload


@dataclass(frozen=True)
class Translation:
    id: str
    translated_text: str


@dataclass(frozen=True)
class TranslationBatchResult:
    translations: list[Translation]


def text_item_id(ref: TextItemRef) -> str:
    parts = [f"s{ref.slide_index}", f"sh{ref.shape_index}"]
    if ref.text_frame_paragraph_index is not None:
        parts.append(f"p{ref.text_frame_paragraph_index}")
    if ref.table_row_index is not None and ref.table_col_index is not None:
        parts.append(f"r{ref.table_row_index}")
        parts.append(f"c{ref.table_col_index}")
    if ref.table_paragraph_index is not None:
        parts.append(f"p{ref.table_paragraph_index}")
    return "-".join(parts)
