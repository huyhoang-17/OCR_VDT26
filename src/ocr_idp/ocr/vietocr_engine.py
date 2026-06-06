"""Adapter VietOCR — nhận dạng tiếng Việt CHẤT LƯỢNG CAO (giữ dấu).

VietOCR chỉ NHẬN DẠNG (recognition) trên ảnh dòng đã cắt, không tự phát hiện vùng.
Ở đây ghép: RapidOCR(detection) -> cắt từng dòng -> VietOCR(recognition).

LƯU Ý môi trường: VietOCR cần PyTorch. Trên Python 3.14 (host) torch thường CHƯA
có wheel -> engine này chạy trong Docker (Python 3.11). Lần chạy đầu, VietOCR tải
trọng số model về (cần mạng).
"""

from __future__ import annotations

import time

from ..config import OCRConfig
from ..preprocess.base import crop_bbox, to_bgr
from ..types import Line, OCRResult, PageImage
from .base import OCREngine
from .detection import RapidOCRDetector
from .registry import register_engine


@register_engine
class VietOCREngine(OCREngine):
    name = "vietocr"
    # Cần vietocr + torch (nhận dạng) và rapidocr (phát hiện vùng)
    requires = ("vietocr", "torch", "rapidocr_onnxruntime")

    def __init__(self, config: OCRConfig | None = None) -> None:
        super().__init__(config)
        self._predictor = None
        self._detector = RapidOCRDetector()

    def _get_predictor(self):
        if self._predictor is None:
            from vietocr.tool.config import Cfg
            from vietocr.tool.predictor import Predictor

            cfg = Cfg.load_config_from_name(self.config.vietocr_model)
            cfg["device"] = "cuda:0" if self.config.use_gpu else "cpu"
            cfg["predictor"]["beamsearch"] = False  # nhanh hơn, đủ tốt
            self._predictor = Predictor(cfg)
        return self._predictor

    @staticmethod
    def _to_pil(crop_bgr):
        import cv2
        from PIL import Image

        return Image.fromarray(cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB))

    def recognize(self, page: PageImage) -> OCRResult:
        img = to_bgr(page.image)
        predictor = self._get_predictor()

        t0 = time.perf_counter()
        boxes = self._detector.detect(img)

        lines: list[Line] = []
        for bbox in boxes:
            crop = crop_bbox(img, bbox.x1, bbox.y1, bbox.x2, bbox.y2, pad=2)
            if crop is None:
                continue
            text, prob = self._predict(predictor, self._to_pil(crop))
            if text and text.strip():
                lines.append(Line(text=text.strip(), bbox=bbox, confidence=float(prob)))

        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        lines.sort(key=lambda ln: (round(ln.bbox.y1 / 10.0), ln.bbox.x1))
        return OCRResult(
            page_index=page.page_index,
            lines=lines,
            engine=self.name,
            image_width=page.width,
            image_height=page.height,
            elapsed_ms=round(elapsed_ms, 1),
        )

    @staticmethod
    def _predict(predictor, pil_img) -> tuple[str, float]:
        """Gọi VietOCR, xử lý linh hoạt cả khi trả (text, prob) lẫn chỉ text."""
        out = predictor.predict(pil_img, return_prob=True)
        if isinstance(out, tuple) and len(out) == 2:
            return str(out[0]), float(out[1])
        return str(out), 1.0
