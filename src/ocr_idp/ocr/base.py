"""Interface chung cho mọi engine OCR.

Mọi engine (RapidOCR, VietOCR, Tesseract, EasyOCR, Paddle) đều hiện thực
`OCREngine.recognize(page) -> OCRResult` để phần còn lại của pipeline không phụ
thuộc vào engine cụ thể -> dễ thay thế & so sánh.
"""

from __future__ import annotations

import importlib.util
from abc import ABC, abstractmethod

from ..config import OCRConfig
from ..types import OCRResult, PageImage


class OCREngine(ABC):
    """Lớp cơ sở cho engine OCR."""

    #: tên định danh (dùng trong cấu hình & registry)
    name: str = "base"
    #: các module Python cần có để engine chạy được (kiểm tra availability)
    requires: tuple[str, ...] = ()

    def __init__(self, config: OCRConfig | None = None) -> None:
        self.config = config or OCRConfig()

    @classmethod
    def is_available(cls) -> bool:
        """True nếu mọi dependency (`requires`) đã cài (không import thật)."""
        return all(importlib.util.find_spec(m) is not None for m in cls.requires)

    @abstractmethod
    def recognize(self, page: PageImage) -> OCRResult:
        """Nhận diện văn bản trên 1 trang -> OCRResult (dòng + bbox + confidence)."""

    def __repr__(self) -> str:  # pragma: no cover
        return f"<OCREngine {self.name}>"
