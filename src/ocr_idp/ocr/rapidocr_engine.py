"""Adapter cho RapidOCR (ONNX) — engine mặc định.

RapidOCR cài nhẹ (ONNX runtime, chạy CPU, không cần torch/paddle) nên phù hợp
khởi động nhanh trên mọi môi trường. Model đi kèm gói (chạy offline).
"""

from __future__ import annotations

import time

from ..config import OCRConfig
from ..preprocess.base import to_bgr
from ..types import BBox, Line, OCRResult, PageImage
from .base import OCREngine
from .registry import register_engine


@register_engine
class RapidOCREngine(OCREngine):
    name = "rapidocr"
    requires = ("rapidocr_onnxruntime", "onnxruntime")

    def __init__(self, config: OCRConfig | None = None) -> None:
        super().__init__(config)
        self._engine = None  # khởi tạo lười (nạp model tốn thời gian)

    def _get_engine(self):
        if self._engine is None:
            from rapidocr_onnxruntime import RapidOCR

            self._engine = RapidOCR()
        return self._engine

    def recognize(self, page: PageImage) -> OCRResult:
        img = to_bgr(page.image)  # RapidOCR nhận ảnh BGR

        t0 = time.perf_counter()
        raw, _elapse = self._get_engine()(img)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        lines: list[Line] = []
        for box, text, score in raw or []:
            conf = float(score)
            if conf < self.config.min_text_confidence:
                continue
            bbox = BBox.from_points([(float(p[0]), float(p[1])) for p in box])
            lines.append(Line(text=str(text), bbox=bbox, confidence=conf))

        # Sắp xếp theo thứ tự đọc: trên->dưới (gom theo dải ~10px), trái->phải
        lines.sort(key=lambda ln: (round(ln.bbox.y1 / 10.0), ln.bbox.x1))

        return OCRResult(
            page_index=page.page_index,
            lines=lines,
            engine=self.name,
            image_width=page.width,
            image_height=page.height,
            elapsed_ms=round(elapsed_ms, 1),
            raw=raw,
        )
