"""Chuẩn hóa số: '1.000' / '1,000' / '85 000' -> 1000, 85000."""

from __future__ import annotations

import re
from typing import Optional


def parse_int(raw: Optional[str]) -> tuple[Optional[int], list[str]]:
    """Lấy số nguyên (bỏ mọi ký tự phân tách: dấu chấm/phẩy/khoảng trắng)."""
    if not raw:
        return None, ["số trống"]
    digits = re.sub(r"[^\d]", "", raw)
    if not digits:
        return None, [f"không có chữ số trong '{raw}'"]
    return int(digits), []


def parse_money(raw: Optional[str]) -> tuple[Optional[int], list[str]]:
    """Số tiền (VND, số nguyên). Hiện coi như số nguyên giống parse_int."""
    return parse_int(raw)


def parse_price(raw: Optional[str]) -> tuple[Optional[int], list[str]]:
    """Giá lệnh: số nguyên; lệnh thị trường ('theo lệnh'/ATO/...) -> None KHÔNG cảnh báo."""
    if not raw or not re.search(r"\d", raw):
        return None, []  # không có chữ số -> giá theo lệnh, để trống hợp lệ
    digits = re.sub(r"[^\d]", "", raw)
    return int(digits), []


def parse_float(raw: Optional[str]) -> tuple[Optional[float], list[str]]:
    """Số thực kiểu Việt: '12,34' hoặc '12.34' -> 12.34; '1.234,5' -> 1234.5.

    Dùng cho tỉ lệ %, đơn giá lẻ. Bỏ ký hiệu '%' và khoảng trắng.
    """
    if not raw:
        return None, ["số trống"]
    s = re.sub(r"[%\s]", "", raw)
    s = re.sub(r"[^\d.,\-]", "", s)
    if not re.search(r"\d", s):
        return None, [f"không có chữ số trong '{raw}'"]
    if "." in s and "," in s:
        # Có cả hai: dấu xuất hiện sau cùng là dấu thập phân
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")  # 1.234,5 -> 1234.5
        else:
            s = s.replace(",", "")  # 1,234.5 -> 1234.5
    elif "," in s:
        s = s.replace(",", ".")  # 12,34 -> 12.34
    try:
        return float(s), []
    except ValueError:
        return None, [f"không phân tích được số thực: '{raw}'"]
