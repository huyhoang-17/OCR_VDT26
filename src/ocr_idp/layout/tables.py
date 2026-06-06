"""Phát hiện bảng (đường kẻ + ô) bằng hình thái học (morphology).

Nền tảng cho trích xuất bảng của Form C (danh sách cổ đông) ở M7. Cách làm:
  * Tách đường kẻ NGANG và DỌC bằng erode/dilate với kernel dài.
  * Giao hai mặt nạ -> lưới; phần bù của lưới -> các Ô (cell).
"""

from __future__ import annotations

import cv2
import numpy as np

from ..preprocess.base import to_gray
from ..types import BBox


def _line_mask(bw: np.ndarray, horizontal: bool, scale: int = 20) -> np.ndarray:
    h, w = bw.shape[:2]
    if horizontal:
        size = max(10, w // scale)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (size, 1))
    else:
        size = max(10, h // scale)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, size))
    eroded = cv2.erode(bw, kernel, iterations=1)
    return cv2.dilate(eroded, kernel, iterations=1)


def detect_table_cells(gray: np.ndarray, min_cell_area: int = 400) -> list[BBox]:
    """Trả về danh sách ô (cell) phát hiện được trong bảng (rỗng nếu không có bảng)."""
    gray = to_gray(gray)
    bw = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]

    horizontal = _line_mask(bw, horizontal=True)
    vertical = _line_mask(bw, horizontal=False)
    grid = cv2.add(horizontal, vertical)

    # Ô = vùng kín được bao bởi lưới -> tìm contour trên ảnh lưới, lấy con bên trong
    contours, hierarchy = cv2.findContours(grid, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    cells: list[BBox] = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if w * h < min_cell_area:
            continue
        # Loại khung quá lớn (cả bảng) và quá dẹt (đường kẻ)
        if w > 0.97 * gray.shape[1] and h > 0.97 * gray.shape[0]:
            continue
        if w < 8 or h < 8:
            continue
        cells.append(BBox(x, y, x + w, y + h))
    return cells


def has_table(gray: np.ndarray, min_cells: int = 6) -> bool:
    """Heuristic nhanh: ảnh có bảng hay không."""
    return len(detect_table_cells(gray)) >= min_cells
