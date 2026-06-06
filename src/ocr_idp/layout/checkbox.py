"""Phát hiện trạng thái checkbox/radio (tick/untick) bằng hình học.

Ý tưởng: ô đánh dấu (X / ✓ / tô đậm) có nhiều "mực" ở PHẦN LÕI bên trong hơn ô
trống (ô trống chỉ có viền). Ta tìm ô vuông ở vùng bên trái nhãn, rồi đo tỉ lệ
mực ở lõi (đã loại viền) -> vượt ngưỡng = đã tick.
"""

from __future__ import annotations

from typing import Optional

import cv2
import numpy as np

from ..preprocess.base import crop_bbox, to_gray
from ..types import BBox


def _find_box(region: np.ndarray, expected_side: float) -> Optional[tuple[int, int, int, int]]:
    """Tìm ô vuông trong vùng cắt. Trả (x,y,w,h) theo tọa độ vùng, hoặc None."""
    inv = cv2.threshold(region, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    contours, _ = cv2.findContours(inv, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    best, best_x = None, -1.0
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if w < 4 or h < 4:
            continue
        aspect = w / float(h)
        if not (0.6 <= aspect <= 1.7):
            continue
        if not (0.45 * expected_side <= h <= 2.0 * expected_side):
            continue
        # Ưu tiên ô gần nhãn nhất (bên phải vùng tìm kiếm)
        if x > best_x:
            best, best_x = (x, y, w, h), x
    return best


def _inner_ink_ratio(gray_box: np.ndarray) -> float:
    """Tỉ lệ pixel 'mực' ở lõi (50% giữa) của 1 ô."""
    h, w = gray_box.shape[:2]
    if h < 4 or w < 4:
        return 0.0
    inner = gray_box[h // 4 : 3 * h // 4, w // 4 : 3 * w // 4]
    if inner.size == 0:
        return 0.0
    return float((inner < 128).mean())


def detect_checkbox_state(
    gray: np.ndarray, label_bbox: BBox, tick_threshold: float = 0.05
) -> tuple[bool, Optional[BBox], float]:
    """Xác định ô (trái nhãn) đã tick chưa. Trả (ticked, box_bbox, fill_ratio)."""
    gray = to_gray(gray)
    H = max(label_bbox.height, 6.0)
    rx1 = label_bbox.x1 - 2.4 * H
    rx2 = label_bbox.x1 + 0.3 * H
    ry1 = label_bbox.y1 - 0.3 * H
    ry2 = label_bbox.y2 + 0.3 * H
    region = crop_bbox(gray, rx1, ry1, rx2, ry2, pad=0)
    if region is None:
        return False, None, 0.0

    box = _find_box(region, expected_side=H)
    if box is None:
        # Không thấy ô vuông -> KHÔNG đoán bừa "đã tick" (tránh dương tính giả
        # do chữ lân cận). Trả về không tick + không có hộp.
        return False, None, 0.0

    bx, by, bw, bh = box
    ratio = _inner_ink_ratio(region[by : by + bh, bx : bx + bw])
    abs_bbox = BBox(rx1 + bx, ry1 + by, rx1 + bx + bw, ry1 + by + bh)
    return ratio > tick_threshold, abs_bbox, ratio
