"""Tự động cắt vùng nội dung (bỏ viền/khoảng trắng thừa)."""

from __future__ import annotations

from typing import Optional

import cv2
import numpy as np


def auto_crop(
    gray: np.ndarray, pad: int = 12, min_area_ratio: float = 0.05
) -> tuple[np.ndarray, Optional[tuple[int, int, int, int]]]:
    """Cắt quanh vùng có nội dung.

    Trả về (ảnh đã cắt, hộp cắt (x0,y0,x1,y1)). Nếu không phát hiện được nội dung
    đáng kể (vùng quá nhỏ -> tránh cắt nhầm), trả lại ảnh gốc và None.
    """
    h, w = gray.shape[:2]
    thr = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    # Đóng (close) để gộp các nét chữ rời thành mảng nội dung liền
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    closed = cv2.morphologyEx(thr, cv2.MORPH_CLOSE, kernel)

    coords = cv2.findNonZero(closed)
    if coords is None:
        return gray, None

    x, y, bw, bh = cv2.boundingRect(coords)
    x0, y0 = max(0, x - pad), max(0, y - pad)
    x1, y1 = min(w, x + bw + pad), min(h, y + bh + pad)

    if (x1 - x0) * (y1 - y0) < min_area_ratio * w * h:
        return gray, None  # vùng quá nhỏ -> không cắt
    return gray[y0:y1, x0:x1], (x0, y0, x1, y1)
