"""Cơ sở cho trích xuất trường: FieldSpec, ngữ cảnh, interface, tiện ích hình học."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

from ..config import AppConfig
from ..types import BBox, FieldValue, Line
from ..normalize.text import strip_accents


@dataclass
class FieldSpec:
    """Khai báo cách trích xuất 1 trường (đọc từ extraction.yaml)."""

    name: str  # tên trường dạng dot-path vào JSON (vd: investor.id_document.number)
    strategy: str  # rule | anchor | layout | llm | checkbox | signature
    anchor: list[str] = field(default_factory=list)  # các nhãn để dò (anchor)
    regex: Optional[str] = None
    normalizer: Optional[str] = None
    choices: Optional[list[str]] = None
    required: bool = False
    min_confidence: Optional[float] = None
    value_direction: str = "right"  # right | below
    options: Optional[dict] = None  # cho checkbox/radio (dùng ở M5)
    note: Optional[str] = None

    @classmethod
    def from_dict(cls, d: dict) -> "FieldSpec":
        d = dict(d)
        anchor = d.pop("anchor", [])
        if isinstance(anchor, str):
            anchor = [anchor]
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        kwargs = {k: v for k, v in d.items() if k in known}
        kwargs["anchor"] = anchor
        return cls(**kwargs)


@dataclass
class ExtractionContext:
    """Dữ liệu đầu vào cho trích xuất (gộp các dòng OCR của mọi trang)."""

    lines: list[Line]
    config: AppConfig
    _text: Optional[str] = None
    _utext: Optional[str] = None

    @property
    def text(self) -> str:
        if self._text is None:
            self._text = "\n".join(ln.text for ln in self.lines)
        return self._text

    @property
    def text_unaccented(self) -> str:
        if self._utext is None:
            self._utext = strip_accents(self.text)
        return self._utext


class FieldExtractor(ABC):
    """Interface cho một chiến lược trích xuất."""

    strategy: str = "base"

    @abstractmethod
    def extract(self, spec: FieldSpec, ctx: ExtractionContext) -> FieldValue:
        ...


# --------------------------------------------------------------------------- #
# Tiện ích hình học (gom dòng / tìm giá trị theo vị trí)
# --------------------------------------------------------------------------- #
def vertical_overlap_ratio(a: BBox, b: BBox) -> float:
    """Tỉ lệ chồng lấn theo chiều dọc so với hộp thấp hơn (0..1)."""
    overlap = max(0.0, min(a.y2, b.y2) - max(a.y1, b.y1))
    denom = min(a.height, b.height) or 1.0
    return overlap / denom


def find_value_right(lines: list[Line], anchor: Line, min_overlap: float = 0.4) -> Optional[Line]:
    """Dòng giá trị nằm CÙNG HÀNG và bên PHẢI nhãn (gần nhất)."""
    ab = anchor.bbox
    candidates = [
        ln for ln in lines
        if ln is not anchor
        and vertical_overlap_ratio(ln.bbox, ab) >= min_overlap
        and ln.bbox.x1 >= ab.x2 - 0.5 * ab.height
    ]
    if not candidates:
        return None
    return min(candidates, key=lambda ln: ln.bbox.x1)


def find_value_below(lines: list[Line], anchor: Line, max_gap_ratio: float = 2.5) -> Optional[Line]:
    """Dòng giá trị nằm NGAY DƯỚI nhãn (gần & cùng cột trái)."""
    ab = anchor.bbox
    candidates = []
    for ln in lines:
        if ln is anchor:
            continue
        gap = ln.bbox.y1 - ab.y2
        if gap < -0.2 * ab.height:  # phải nằm dưới
            continue
        if gap > max_gap_ratio * ab.height:
            continue
        if abs(ln.bbox.x1 - ab.x1) > 2.5 * ab.height:  # cùng cột
            continue
        candidates.append(ln)
    if not candidates:
        return None
    return min(candidates, key=lambda ln: ln.bbox.y1)
