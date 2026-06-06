"""Phát hiện & sửa nghiêng trang (deskew).

Dùng phương pháp "projection profile": thử xoay ảnh nhị phân ở nhiều góc, chọn
góc làm phép chiếu theo hàng (tổng pixel mỗi hàng) "sắc nét" nhất — khi trang
thẳng, các dòng chữ tách bạch nên phương sai của profile theo hàng đạt cực đại.
Phương pháp này ổn định và không phụ thuộc quy ước góc của cv2.minAreaRect (vốn
khác nhau giữa các phiên bản OpenCV).
"""

from __future__ import annotations

import cv2
import numpy as np

from .base import rotate_image


def estimate_skew_angle(gray: np.ndarray, max_angle: float = 10.0, step: float = 0.5) -> float:
    """Ước lượng góc cần xoay để làm thẳng trang (đơn vị độ).

    Trả về góc hiệu chỉnh: `rotate_image(gray, angle)` sẽ cho trang thẳng.
    """
    h, w = gray.shape[:2]
    # Thu nhỏ để tăng tốc (chiều cao ~600)
    if h > 600:
        scale = 600.0 / h
        small = cv2.resize(gray, (max(1, int(w * scale)), 600), interpolation=cv2.INTER_AREA)
    else:
        small = gray

    # Nhị phân đảo: chữ = trắng (255), nền = đen (0)
    thr = cv2.threshold(small, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]

    best_angle, best_score = 0.0, -1.0
    for angle in np.arange(-max_angle, max_angle + 1e-9, step):
        rotated = rotate_image(thr, float(angle), border=0)
        projection = rotated.sum(axis=1, dtype=np.float64)
        # Phương sai của sai phân profile -> độ "sắc nét" của các dòng
        score = float(np.sum(np.diff(projection) ** 2))
        if score > best_score:
            best_score, best_angle = score, float(angle)
    return best_angle


def deskew(gray: np.ndarray, max_angle: float = 10.0) -> tuple[np.ndarray, float]:
    """Làm thẳng ảnh xám. Trả về (ảnh đã xoay, góc đã xoay)."""
    angle = estimate_skew_angle(gray, max_angle=max_angle)
    if abs(angle) < 0.1:
        return gray, 0.0
    return rotate_image(gray, angle, border=255), angle
