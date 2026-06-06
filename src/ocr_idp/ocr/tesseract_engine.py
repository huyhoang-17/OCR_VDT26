"""Adapter Tesseract OCR (pytesseract).

Tesseract cần BINARY hệ thống (không chỉ gói Python). `is_available` kiểm tra cả
hai: gói `pytesseract` và lệnh `tesseract` trên PATH (hoặc biến TESSERACT_CMD).
Trên Windows: cài bản UB-Mannheim + gói ngôn ngữ `vie`, đặt PATH hoặc TESSERACT_CMD.

Dùng `image_to_data` để lấy hộp + độ tin cậy theo TỪ, rồi gom thành DÒNG theo
(block, par, line) -> đồng nhất với OCRResult của các engine khác.
"""

from __future__ import annotations

import importlib.util
import os
import shutil
import time

from ..config import OCRConfig
from ..preprocess.base import to_gray
from ..types import BBox, Line, OCRResult, PageImage
from .base import OCREngine
from .registry import register_engine

# Ánh xạ mã ngôn ngữ cấu hình -> mã Tesseract (vi -> vie).
_LANG_MAP = {"vi": "vie", "en": "eng", "vie": "vie", "eng": "eng"}


@register_engine
class TesseractEngine(OCREngine):
    name = "tesseract"
    requires = ("pytesseract",)

    @classmethod
    def is_available(cls) -> bool:
        if importlib.util.find_spec("pytesseract") is None:
            return False
        cmd = os.environ.get("TESSERACT_CMD") or "tesseract"
        return shutil.which(cmd) is not None or os.path.isfile(cmd)

    def _tess(self):
        import pytesseract

        cmd = os.environ.get("TESSERACT_CMD")
        if cmd:
            pytesseract.pytesseract.tesseract_cmd = cmd
        return pytesseract

    def _lang(self) -> str:
        return _LANG_MAP.get(self.config.lang, self.config.lang)

    def recognize(self, page: PageImage) -> OCRResult:
        pyt = self._tess()
        gray = to_gray(page.image)

        t0 = time.perf_counter()
        data = pyt.image_to_data(
            gray, lang=self._lang(), output_type=pyt.Output.DICT, config="--psm 6"
        )
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        lines = self._group_lines(data, self.config.min_text_confidence)
        lines.sort(key=lambda ln: (round(ln.bbox.y1 / 10.0), ln.bbox.x1))
        return OCRResult(
            page_index=page.page_index, lines=lines, engine=self.name,
            image_width=page.width, image_height=page.height,
            elapsed_ms=round(elapsed_ms, 1), raw=data,
        )

    @staticmethod
    def _group_lines(data: dict, min_conf: float) -> list[Line]:
        """Gom các TỪ của Tesseract (image_to_data DICT) thành DÒNG."""
        n = len(data.get("text", []))
        groups: dict[tuple, list[int]] = {}
        for i in range(n):
            txt = (data["text"][i] or "").strip()
            try:
                conf = float(data["conf"][i])
            except (TypeError, ValueError):
                conf = -1.0
            if not txt or conf < 0:
                continue
            key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
            groups.setdefault(key, []).append(i)

        lines: list[Line] = []
        for idxs in groups.values():
            idxs.sort(key=lambda i: data["left"][i])
            text = " ".join(data["text"][i].strip() for i in idxs if data["text"][i].strip())
            if not text:
                continue
            conf = sum(float(data["conf"][i]) for i in idxs) / len(idxs) / 100.0
            if conf < min_conf:
                continue
            x1 = min(data["left"][i] for i in idxs)
            y1 = min(data["top"][i] for i in idxs)
            x2 = max(data["left"][i] + data["width"][i] for i in idxs)
            y2 = max(data["top"][i] + data["height"][i] for i in idxs)
            lines.append(Line(text=text, bbox=BBox(x1, y1, x2, y2), confidence=conf))
        return lines
