"""Vẽ overlay bbox OCR lên ảnh để xem/debug (dùng lại cho web demo ở M10).

LƯU Ý: cv2.putText không hỗ trợ tiếng Việt -> chỉ vẽ KHUNG + số thứ tự dòng,
không vẽ nội dung text lên ảnh (text xem ở JSON/console).
"""

from __future__ import annotations

import cv2
import numpy as np

from ..preprocess.base import to_bgr
from ..types import OCRResult


def draw_ocr_overlay(
    image: np.ndarray,
    result: OCRResult,
    color: tuple[int, int, int] = (0, 160, 0),
    thickness: int = 2,
    show_index: bool = True,
) -> np.ndarray:
    """Trả về ảnh BGR có vẽ khung bbox của từng dòng OCR."""
    canvas = to_bgr(image).copy()
    for i, line in enumerate(result.lines):
        b = line.bbox
        cv2.rectangle(canvas, (int(b.x1), int(b.y1)), (int(b.x2), int(b.y2)), color, thickness)
        if show_index:
            cv2.putText(
                canvas, str(i), (int(b.x1), max(10, int(b.y1) - 3)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA,
            )
    return canvas
