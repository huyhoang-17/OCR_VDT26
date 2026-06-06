"""Phát hiện vùng chữ ký / con dấu: có nét mực đáng kể ở vùng bên dưới nhãn ký.

Heuristic: chữ ký là các nét rời rạc nằm dưới dòng "(Ký, ghi rõ họ tên)" / "Người
đặt lệnh"... Đo tỉ lệ mực trong vùng bên dưới nhãn; vượt ngưỡng nhỏ -> có chữ ký.
"""

from __future__ import annotations

import cv2
import numpy as np

from ..preprocess.base import crop_bbox, to_gray
from ..types import BBox


def detect_signature(
    gray: np.ndarray, anchor_bbox: BBox, region_height: float = 3.2, ink_threshold: float = 0.004
) -> tuple[bool, float]:
    """Kiểm tra có nét mực (chữ ký) bên dưới `anchor_bbox`. Trả (present, ratio)."""
    gray = to_gray(gray)
    H = max(anchor_bbox.height, 8.0)
    rx1 = anchor_bbox.x1 - 1.2 * H
    rx2 = anchor_bbox.x2 + 1.2 * H
    ry1 = anchor_bbox.y2 + 0.2 * H
    ry2 = anchor_bbox.y2 + region_height * H
    region = crop_bbox(gray, rx1, ry1, rx2, ry2, pad=0)
    if region is None or region.size == 0:
        return False, 0.0

    inv = cv2.threshold(region, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    ratio = float((inv > 0).mean())
    return ratio > ink_threshold, ratio
