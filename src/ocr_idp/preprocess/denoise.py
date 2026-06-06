"""Khử nhiễu ảnh xám."""

from __future__ import annotations

import cv2
import numpy as np


def denoise(gray: np.ndarray, strength: float = 7.0, method: str = "fastnl") -> np.ndarray:
    """Khử nhiễu.

    method:
      * fastnl   — Non-Local Means (chất lượng cao, chậm hơn). Mặc định.
      * median   — lọc trung vị 3x3 (nhanh, tốt cho nhiễu muối tiêu).
      * bilateral— giữ cạnh tốt.
    """
    method = method.lower()
    if method == "median":
        return cv2.medianBlur(gray, 3)
    if method == "bilateral":
        return cv2.bilateralFilter(gray, d=5, sigmaColor=50, sigmaSpace=50)
    return cv2.fastNlMeansDenoising(
        gray, None, h=float(strength), templateWindowSize=7, searchWindowSize=21
    )
