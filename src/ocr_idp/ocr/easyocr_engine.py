"""Adapter EasyOCR (dựa trên PyTorch).

EasyOCR vừa phát hiện vùng vừa nhận dạng (có hỗ trợ tiếng Việt 'vi'). Cần torch
-> trên host Python 3.14 thường CHƯA có wheel; chạy trong Docker (Python 3.11).
Lần đầu chạy sẽ tải trọng số model về (cần mạng).
"""

from __future__ import annotations

import time

from ..config import OCRConfig
from ..preprocess.base import to_bgr
from ..types import BBox, Line, OCRResult, PageImage
from .base import OCREngine
from .registry import register_engine


@register_engine
class EasyOCREngine(OCREngine):
    name = "easyocr"
    requires = ("easyocr", "torch")

    def __init__(self, config: OCRConfig | None = None) -> None:
        super().__init__(config)
        self._reader = None  # khởi tạo lười (nạp model tốn thời gian)

    def _get_reader(self):
        if self._reader is None:
            import easyocr

            langs = [self.config.lang] if self.config.lang else ["vi"]
            self._reader = easyocr.Reader(langs, gpu=self.config.use_gpu)
        return self._reader

    def recognize(self, page: PageImage) -> OCRResult:
        img = to_bgr(page.image)
        reader = self._get_reader()

        t0 = time.perf_counter()
        raw = reader.readtext(img)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        lines = self._lines_from(raw, self.config.min_text_confidence)
        lines.sort(key=lambda ln: (round(ln.bbox.y1 / 10.0), ln.bbox.x1))
        return OCRResult(
            page_index=page.page_index, lines=lines, engine=self.name,
            image_width=page.width, image_height=page.height,
            elapsed_ms=round(elapsed_ms, 1), raw=raw,
        )

    @staticmethod
    def _lines_from(raw, min_conf: float) -> list[Line]:
        """raw = list of (box[4 điểm], text, conf)."""
        lines: list[Line] = []
        for item in raw or []:
            box, text, score = item[0], item[1], item[2]
            conf = float(score)
            if conf < min_conf or not str(text).strip():
                continue
            bbox = BBox.from_points([(float(p[0]), float(p[1])) for p in box])
            lines.append(Line(text=str(text).strip(), bbox=bbox, confidence=conf))
        return lines
