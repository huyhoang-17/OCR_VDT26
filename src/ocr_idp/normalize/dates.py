"""Chuẩn hóa ngày tháng tiếng Việt -> ISO (YYYY-MM-DD)."""

from __future__ import annotations

import re
from datetime import date
from typing import Optional

from .text import strip_accents

# Các định dạng hỗ trợ (chạy trên chuỗi đã bỏ dấu, không phân biệt hoa thường):
#   dd/mm/yyyy, dd-mm-yyyy, dd.mm.yyyy
#   ngay dd thang mm nam yyyy
_PATTERNS = [
    re.compile(r"(\d{1,2})\s*[/\-.]\s*(\d{1,2})\s*[/\-.]\s*(\d{2,4})"),
    re.compile(r"ngay\s+(\d{1,2})\s+thang\s+(\d{1,2})\s+nam\s+(\d{2,4})"),
]


def parse_date(raw: Optional[str], output_format: str = "%Y-%m-%d") -> tuple[Optional[str], list[str]]:
    """Phân tích ngày (kiểu Việt: ngày trước) -> chuỗi ISO. Trả về (giá trị, cảnh báo)."""
    if not raw or not raw.strip():
        return None, ["ngày trống"]

    s = strip_accents(raw).lower()
    match = None
    for pat in _PATTERNS:
        match = pat.search(s)
        if match:
            break
    if not match:
        return None, [f"không nhận dạng được ngày: '{raw}'"]

    day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
    if year < 100:
        year += 2000
    try:
        return date(year, month, day).strftime(output_format), []
    except ValueError:
        return None, [f"ngày không hợp lệ: '{raw}'"]
