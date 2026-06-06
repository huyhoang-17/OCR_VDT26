"""Tiện ích ảnh dùng chung cho các bước tiền xử lý."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


def read_image_file(path: str | Path) -> np.ndarray:
    """Đọc ảnh -> mảng BGR. Dùng imdecode để an toàn với đường dẫn Unicode (Windows)."""
    data = np.fromfile(str(path), dtype=np.uint8)
    img = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"Không đọc được ảnh: {path}")
    return img


def write_image_file(path: str | Path, img: np.ndarray) -> None:
    """Ghi ảnh, an toàn với đường dẫn Unicode."""
    suffix = Path(path).suffix or ".png"
    ok, buf = cv2.imencode(suffix, img)
    if not ok:
        raise ValueError(f"Không mã hóa được ảnh: {path}")
    buf.tofile(str(path))


def to_gray(img: np.ndarray) -> np.ndarray:
    """Chuyển về ảnh xám 1 kênh (idempotent)."""
    if img.ndim == 2:
        return img
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


def to_bgr(img: np.ndarray) -> np.ndarray:
    """Chuyển về ảnh BGR 3 kênh (idempotent)."""
    if img.ndim == 3:
        return img
    return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)


def rotate_image(img: np.ndarray, angle: float, border: int = 255) -> np.ndarray:
    """Xoay ảnh quanh tâm `angle` độ (dương = ngược chiều kim đồng hồ), nền `border`."""
    h, w = img.shape[:2]
    mat = cv2.getRotationMatrix2D((w / 2.0, h / 2.0), angle, 1.0)
    border_value = border if img.ndim == 2 else (border, border, border)
    return cv2.warpAffine(
        img, mat, (w, h), flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT, borderValue=border_value,
    )


def crop_bbox(img: np.ndarray, x1: float, y1: float, x2: float, y2: float, pad: int = 2):
    """Cắt vùng theo hộp (kẹp trong biên ảnh, có đệm). Trả None nếu vùng suy biến."""
    h, w = img.shape[:2]
    ix1, iy1 = max(0, int(x1) - pad), max(0, int(y1) - pad)
    ix2, iy2 = min(w, int(x2) + pad), min(h, int(y2) + pad)
    if ix2 - ix1 < 2 or iy2 - iy1 < 2:
        return None
    return img[iy1:iy2, ix1:ix2]


def limit_size(img: np.ndarray, max_side: int) -> tuple[np.ndarray, float]:
    """Thu nhỏ nếu cạnh dài > max_side (giữ tỉ lệ). Trả về (ảnh, hệ số scale đã áp)."""
    h, w = img.shape[:2]
    longest = max(h, w)
    if longest <= max_side:
        return img, 1.0
    scale = max_side / float(longest)
    resized = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    return resized, scale
