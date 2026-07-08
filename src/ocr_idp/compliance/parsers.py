"""Parser tất định cho số tiền, số lượng, tỷ lệ và ngày trong JSON eform."""

from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

_NUMBER = re.compile(r"[-+]?\d[\d.,\s]*")


def parse_number(value: Any) -> Decimal | None:
    """Đọc cách viết số Việt Nam (``1.000.000``, ``8,5%``, ``300 tỷ đồng``)."""
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float, Decimal)):
        return Decimal(str(value))

    text = str(value).strip().lower()
    match = _NUMBER.search(text)
    if not match:
        return None
    token = re.sub(r"\s+", "", match.group(0))

    # Việt Nam: dấu chấm thường phân tách hàng nghìn, dấu phẩy là thập phân.
    if "." in token and "," in token:
        if token.rfind(",") > token.rfind("."):
            token = token.replace(".", "").replace(",", ".")
        else:
            token = token.replace(",", "")
    elif "." in token:
        parts = token.lstrip("+-").split(".")
        if len(parts) > 1 and all(len(p) == 3 for p in parts[1:]):
            token = token.replace(".", "")
    elif "," in token:
        parts = token.lstrip("+-").split(",")
        if len(parts) > 2 or (len(parts) == 2 and len(parts[1]) == 3):
            token = token.replace(",", "")
        else:
            token = token.replace(",", ".")

    try:
        number = Decimal(token)
    except InvalidOperation:
        return None
    if "tỷ" in text or "ty" in text:
        number *= Decimal("1000000000")
    elif "triệu" in text or "trieu" in text:
        number *= Decimal("1000000")
    return number


def parse_date(value: Any) -> date | None:
    """Đọc ISO 8601 hoặc ``dd/mm/yyyy``; không suy đoán ngày thiếu thành phần."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        pass
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def display_decimal(value: Decimal | None) -> str | None:
    if value is None:
        return None
    if value == value.to_integral_value():
        return f"{int(value):,}".replace(",", ".")
    return format(value.normalize(), "f").replace(".", ",")
