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
