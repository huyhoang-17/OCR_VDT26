"""Tiện ích xử lý chuỗi tiếng Việt (bỏ dấu, chuẩn hóa khoảng trắng, khóa so khớp).

Bỏ dấu (`strip_accents`) rất quan trọng vì OCR ảnh scan (RapidOCR) thường MẤT dấu
("Họ và tên" -> "ho va ten"); so khớp nhãn ở không gian không dấu giúp anchor hoạt
động cho CẢ text-layer (có dấu) lẫn ảnh scan (mất dấu).
"""

from __future__ import annotations

import re
import unicodedata


def strip_accents(text: str) -> str:
    """Bỏ dấu tiếng Việt. 'Nguyễn Đức' -> 'Nguyen Duc'."""
    if not text:
        return ""
    text = text.replace("Đ", "D").replace("đ", "d")
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")


def clean_spaces(text: str) -> str:
    """Gộp khoảng trắng thừa và cắt đầu/cuối."""
    return re.sub(r"\s+", " ", text or "").strip()


def norm_key(text: str) -> str:
    """Chuẩn hóa để so khớp nhãn: bỏ dấu, thường hóa, bỏ dấu câu ở hai đầu."""
    return clean_spaces(strip_accents(text).lower()).strip(" :.…-")
