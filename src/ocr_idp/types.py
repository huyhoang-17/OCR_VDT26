"""Kiểu dữ liệu dùng chung giữa các bước pipeline (các "hợp đồng" interface).

Tách riêng để mọi module phụ thuộc vào *kiểu* thay vì vào *cài đặt* cụ thể của
nhau -> dễ thay thế từng bước. Không import thư viện nặng (numpy chỉ dùng cho
type-hint) để giữ CLI/khởi động nhẹ.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:  # chỉ để gợi ý kiểu, không bắt buộc cài numpy khi chỉ dùng types
    import numpy as np

    NDArray = np.ndarray
else:  # pragma: no cover
    NDArray = Any


# --------------------------------------------------------------------------- #
# Hình học
# --------------------------------------------------------------------------- #
@dataclass
class BBox:
    """Hộp bao theo tọa độ pixel (gốc trên-trái). x1<=x2, y1<=y2."""

    x1: float
    y1: float
    x2: float
    y2: float

    @property
    def width(self) -> float:
        return self.x2 - self.x1

    @property
    def height(self) -> float:
        return self.y2 - self.y1

    @property
    def cx(self) -> float:
        return (self.x1 + self.x2) / 2.0

    @property
    def cy(self) -> float:
        return (self.y1 + self.y2) / 2.0

    @property
    def area(self) -> float:
        return max(0.0, self.width) * max(0.0, self.height)

    def to_list(self) -> list[float]:
        return [self.x1, self.y1, self.x2, self.y2]

    def iou(self, other: "BBox") -> float:
        """Tỉ lệ giao trên hợp (IoU) — dùng cho gom dòng/so khớp vùng."""
        ix1, iy1 = max(self.x1, other.x1), max(self.y1, other.y1)
        ix2, iy2 = min(self.x2, other.x2), min(self.y2, other.y2)
        iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
        inter = iw * ih
        union = self.area + other.area - inter
        return inter / union if union > 0 else 0.0

    @classmethod
    def from_points(cls, points: list[tuple[float, float]]) -> "BBox":
        """Tạo BBox bao quanh tập điểm (vd polygon 4 đỉnh từ engine OCR)."""
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        return cls(min(xs), min(ys), max(xs), max(ys))


# --------------------------------------------------------------------------- #
# Kết quả OCR (thống nhất giữa mọi engine)
# --------------------------------------------------------------------------- #
@dataclass
class Word:
    text: str
    bbox: BBox
    confidence: float = 1.0


@dataclass
class Line:
    """Một dòng text OCR (đơn vị cơ bản mà phần lớn engine trả về)."""

    text: str
    bbox: BBox
    confidence: float = 1.0
    words: list[Word] = field(default_factory=list)


@dataclass
class OCRResult:
    """Kết quả OCR cho MỘT trang ảnh."""

    page_index: int
    lines: list[Line] = field(default_factory=list)
    engine: str = ""
    image_width: int = 0
    image_height: int = 0
    elapsed_ms: float = 0.0
    raw: Any = None  # output thô của engine (debug)

    @property
    def text(self) -> str:
        """Toàn bộ text của trang, mỗi dòng 1 hàng."""
        return "\n".join(ln.text for ln in self.lines)

    @property
    def mean_confidence(self) -> float:
        if not self.lines:
            return 0.0
        return sum(ln.confidence for ln in self.lines) / len(self.lines)


# --------------------------------------------------------------------------- #
# Ảnh trang (đầu ra của bước tiền xử lý, đầu vào của OCR)
# --------------------------------------------------------------------------- #
@dataclass
class TextLayerLine:
    """Dòng text lấy trực tiếp từ text-layer của PDF (không qua OCR)."""

    text: str
    bbox: BBox


@dataclass
class PageImage:
    """Một trang đã chuẩn hóa, sẵn sàng cho OCR.

    Nếu `text_layer` khác None nghĩa là trang PDF có sẵn text chất lượng tốt ->
    pipeline có thể bỏ qua OCR cho trang này (fast path).
    """

    image: NDArray  # ảnh BGR/GRAY (numpy array)
    page_index: int
    dpi: int = 300
    source: str = ""  # đường dẫn file gốc
    preprocess_meta: dict[str, Any] = field(default_factory=dict)
    text_layer: Optional[list[TextLayerLine]] = None

    @property
    def width(self) -> int:
        return int(self.image.shape[1]) if self.image is not None else 0

    @property
    def height(self) -> int:
        return int(self.image.shape[0]) if self.image is not None else 0

    @property
    def has_text_layer(self) -> bool:
        return self.text_layer is not None and len(self.text_layer) > 0


# --------------------------------------------------------------------------- #
# Trích xuất trường
# --------------------------------------------------------------------------- #
class FieldStatus(str, Enum):
    OK = "ok"
    LOW_CONFIDENCE = "low_confidence"
    MISSING = "missing"
    INVALID_FORMAT = "invalid_format"


@dataclass
class FieldValue:
    """Giá trị một trường sau khi trích xuất + chuẩn hóa."""

    name: str
    raw_value: Optional[str] = None  # văn bản thô trích được
    value: Any = None  # giá trị đã chuẩn hóa (kiểu đúng theo schema)
    confidence: float = 0.0
    source: str = ""  # chiến lược tạo ra: rule | anchor | layout | llm
    bbox: Optional[BBox] = None  # vị trí trên ảnh (để overlay/debug)
    page_index: int = 0
    status: FieldStatus = FieldStatus.OK
    warnings: list[str] = field(default_factory=list)


@dataclass
class ExtractionResult:
    """Kết quả trích xuất toàn biểu mẫu (dạng phẳng theo tên trường).

    `FormPlugin.assemble()` sẽ dựng JSON lồng nhau cuối cùng theo schema từ
    tập `fields` này.
    """

    form_type: str
    fields: dict[str, FieldValue] = field(default_factory=dict)
    page_count: int = 1
    warnings: list[str] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    def get(self, name: str) -> Optional[FieldValue]:
        return self.fields.get(name)
