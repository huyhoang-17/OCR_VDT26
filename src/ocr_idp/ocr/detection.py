"""Phát hiện vùng dòng chữ (text detection) — tách khỏi nhận dạng để tái sử dụng.

Dùng bộ phát hiện DB của RapidOCR (ONNX, nhẹ): rất tốt ở việc ĐỊNH VỊ dòng chữ
(kể cả tiếng Việt), chỉ yếu ở phần NHẬN DẠNG dấu. Nhờ vậy có thể ghép:
    RapidOCR(detection) + VietOCR(recognition) -> vừa định vị tốt vừa giữ dấu.
"""

from __future__ import annotations

from ..types import BBox


class RapidOCRDetector:
    """Bọc bộ detection của RapidOCR -> trả danh sách BBox dòng chữ."""

    requires = ("rapidocr_onnxruntime", "onnxruntime")

    def __init__(self) -> None:
        self._engine = None

    def _get_engine(self):
        if self._engine is None:
            from rapidocr_onnxruntime import RapidOCR

            self._engine = RapidOCR()
        return self._engine

    @staticmethod
    def _boxes_from(raw) -> list[BBox]:
        boxes: list[BBox] = []
        for item in raw or []:
            # det-only: item là box 4 điểm; full: item là [box, text, score]
            box = item[0] if (isinstance(item, (list, tuple)) and len(item) == 3) else item
            try:
                boxes.append(BBox.from_points([(float(p[0]), float(p[1])) for p in box]))
            except (TypeError, ValueError, IndexError):
                continue
        return boxes

    def detect(self, img_bgr) -> list[BBox]:
        """Trả về danh sách BBox của các dòng chữ phát hiện được."""
        engine = self._get_engine()
        # Ưu tiên chạy detection-only cho nhanh; nếu API khác phiên bản -> fallback full.
        try:
            res, _ = engine(img_bgr, use_det=True, use_cls=False, use_rec=False)
            boxes = self._boxes_from(res)
            if boxes:
                return boxes
        except Exception:  # noqa: BLE001 - khác phiên bản API -> fallback
            pass
        res, _ = engine(img_bgr)
        return self._boxes_from(res)
