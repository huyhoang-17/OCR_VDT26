"""Tăng tương phản (CLAHE) và nhị phân hóa (binarization).

LƯU Ý: các engine OCR học sâu (RapidOCR/PaddleOCR/VietOCR) thường cho kết quả
TỐT HƠN với ảnh xám (grayscale), nhị phân hóa mạnh có thể làm giảm độ chính xác.
Vì vậy mặc định pipeline để `binarize: none`. Nhị phân (otsu/adaptive/sauvola)
hữu ích chủ yếu cho Tesseract hoặc ảnh nền bẩn.
"""

from __future__ import annotations

import cv2
import numpy as np


def enhance_contrast(gray: np.ndarray, clip_limit: float = 2.0, grid: int = 8) -> np.ndarray:
    """Tăng tương phản cục bộ bằng CLAHE."""
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(grid, grid))
    return clahe.apply(gray)


def binarize(gray: np.ndarray, method: str = "otsu") -> np.ndarray:
    """Nhị phân hóa ảnh xám. method: none | otsu | adaptive | sauvola."""
    method = (method or "none").lower()
    if method in ("none", ""):
        return gray
    if method == "otsu":
        return cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    if method == "adaptive":
        return cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, blockSize=31, C=10
        )
    if method == "sauvola":
        # Sauvola: ngưỡng thích nghi cục bộ, tốt cho ảnh nền không đều (cần scikit-image)
        from skimage.filters import threshold_sauvola

        thresh = threshold_sauvola(gray, window_size=25)
        return ((gray > thresh) * 255).astype(np.uint8)
    raise ValueError(f"Phương pháp binarize không hợp lệ: {method}")
