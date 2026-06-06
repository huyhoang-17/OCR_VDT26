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


_TIME = re.compile(r"(\d{1,2})\s*[:hg]\s*(\d{2})")


def parse_datetime(raw: Optional[str]) -> tuple[Optional[str], list[str]]:
    """Ngày + giờ -> ISO 8601 'YYYY-MM-DDTHH:MM'.

    Chấp nhận thứ tự bất kỳ: '09:30 ngày 15/01/2025', '15/01/2025 9h30'. Nếu thiếu
    giờ -> chỉ trả ngày; thiếu ngày -> cảnh báo.
    """
    if not raw or not raw.strip():
        return None, ["thời gian trống"]
    iso_date, date_warns = parse_date(raw)
    if iso_date is None:
        return None, date_warns or [f"không nhận dạng được ngày-giờ: '{raw}'"]
    m = _TIME.search(strip_accents(raw))
    if not m:
        return iso_date, []  # chỉ có ngày
    hh, mm = int(m.group(1)), int(m.group(2))
    if not (0 <= hh <= 23 and 0 <= mm <= 59):
        return iso_date, [f"giờ không hợp lệ trong '{raw}'"]
    return f"{iso_date}T{hh:02d}:{mm:02d}", []
