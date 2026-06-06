"""Adapter PaddleOCR (dựa trên PaddlePaddle).

PaddleOCR hỗ trợ tiếng Việt ('vi'), phát hiện + nhận dạng. Cần `paddlepaddle`
(`import paddle`) -> trên host Python 3.14 thường CHƯA có wheel; chạy trong Docker.
Lần đầu chạy sẽ tải model về (cần mạng).

Tham số `.ocr()` trả về cấu trúc lồng theo trang: [[ [box, (text, conf)], ... ]].
Hàm parse xử lý linh hoạt để chịu được khác biệt phiên bản.
"""

from __future__ import annotations

import time

from ..config import OCRConfig
from ..preprocess.base import to_bgr
from ..types import BBox, Line, OCRResult, PageImage
from .base import OCREngine
from .registry import register_engine

_LANG_MAP = {"vi": "vi", "vie": "vi", "en": "en", "eng": "en"}


@register_engine
class PaddleOCREngine(OCREngine):
    name = "paddle"
    requires = ("paddleocr", "paddle")

    def __init__(self, config: OCRConfig | None = None) -> None:
        super().__init__(config)
        self._ocr = None  # khởi tạo lười

    def _lang(self) -> str:
        return _LANG_MAP.get(self.config.lang, self.config.lang)

    def _get_ocr(self):
        if self._ocr is None:
            from paddleocr import PaddleOCR

            self._ocr = PaddleOCR(use_angle_cls=True, lang=self._lang(), show_log=False)
        return self._ocr

    def recognize(self, page: PageImage) -> OCRResult:
        img = to_bgr(page.image)
        ocr = self._get_ocr()

        t0 = time.perf_counter()
        raw = ocr.ocr(img, cls=True)
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
        """Chuẩn hóa output PaddleOCR -> list[Line].

        Dạng phổ biến: raw = [page0], page0 = [ [box, (text, conf)], ... ].
        Một số phiên bản trả thẳng list các entry -> tự nhận diện.
        """
        if not raw:
            return []
        # Bóc lớp "theo trang" nếu có (raw[0] là list các entry)
        page = raw[0] if isinstance(raw[0], list) and raw[0] and isinstance(raw[0][0], (list, tuple)) else raw

        lines: list[Line] = []
        for item in page or []:
            try:
                box, payload = item[0], item[1]
                text = payload[0] if isinstance(payload, (list, tuple)) else payload
                conf = float(payload[1]) if isinstance(payload, (list, tuple)) and len(payload) > 1 else 1.0
            except (TypeError, IndexError, ValueError):
                continue
            if conf < min_conf or not str(text).strip():
                continue
            bbox = BBox.from_points([(float(p[0]), float(p[1])) for p in box])
            lines.append(Line(text=str(text).strip(), bbox=bbox, confidence=conf))
        return lines
