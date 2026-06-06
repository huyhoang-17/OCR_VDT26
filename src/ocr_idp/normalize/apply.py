"""Áp chuẩn hóa cho từng trường theo cấu hình (`normalizer` / `choices`).

Mỗi normalizer là hàm `raw:str -> (value, warnings)`. `apply_normalization` duyệt
các FieldValue và đặt `.value` (giá trị đã chuẩn hóa) + gộp cảnh báo.
"""

from __future__ import annotations

import re
from typing import Any, Callable, Optional

from ..types import FieldValue
from .dates import parse_date
from .numbers import parse_int, parse_money
from .text import clean_spaces, strip_accents


def _norm_string(raw: str) -> tuple[Any, list[str]]:
    return clean_spaces(raw), []


def _norm_date(raw: str) -> tuple[Any, list[str]]:
    return parse_date(raw)


def _norm_int(raw: str) -> tuple[Any, list[str]]:
    return parse_int(raw)


def _norm_money(raw: str) -> tuple[Any, list[str]]:
    return parse_money(raw)


def _norm_phone(raw: str) -> tuple[Any, list[str]]:
    digits = re.sub(r"\D", "", raw or "")
    warns = [] if 9 <= len(digits) <= 11 else [f"số điện thoại bất thường: '{raw}'"]
    return digits, warns


def _norm_email(raw: str) -> tuple[Any, list[str]]:
    email = clean_spaces(raw).lower().replace(" ", "")
    warns = [] if re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email) else [f"email không hợp lệ: '{raw}'"]
    return email, warns


def _norm_id_number(raw: str) -> tuple[Any, list[str]]:
    digits = re.sub(r"\D", "", raw or "")
    warns = [] if len(digits) in (9, 12) else [f"số giấy tờ bất thường ({len(digits)} chữ số)"]
    return digits, warns


def _norm_account(raw: str) -> tuple[Any, list[str]]:
    return re.sub(r"\s", "", (raw or "")).upper(), []


NORMALIZERS: dict[str, Callable[[str], tuple[Any, list[str]]]] = {
    "string": _norm_string,
    "date": _norm_date,
    "int": _norm_int,
    "money": _norm_money,
    "phone": _norm_phone,
    "email": _norm_email,
    "id_number": _norm_id_number,
    "account_number": _norm_account,
}


def normalize_choice(raw: str, choices: list[str], threshold: int = 80) -> tuple[Any, list[str]]:
    """Ánh xạ giá trị về một lựa chọn hợp lệ (không phân biệt dấu/hoa thường)."""
    if not raw or not raw.strip():
        return None, ["lựa chọn trống"]
    key = strip_accents(raw).lower().strip()
    folded = [strip_accents(c).lower().strip() for c in choices]
    for canonical, f in zip(choices, folded):
        if f == key or f in key or key in f:
            return canonical, []
    # fuzzy fallback
    try:
        from rapidfuzz import fuzz, process

        best = process.extractOne(key, folded, scorer=fuzz.ratio)
        if best and best[1] >= threshold:
            return choices[best[2]], []
    except Exception:  # noqa: BLE001
        pass
    return raw, [f"giá trị '{raw}' không khớp lựa chọn {choices}"]


def apply_normalization(fields: dict[str, FieldValue], specs: list) -> None:
    """Đặt `.value` đã chuẩn hóa cho từng FieldValue dựa trên FieldSpec tương ứng.

    Lưu ý: các extractor dựa-trên-layout (checkbox/chữ ký) đã tự đặt `.value`
    (list/bool); khi field KHÔNG khai báo normalizer/choices ta KHÔNG ghi đè giá
    trị đó — chỉ điền value từ raw_value khi extractor chưa đặt (value còn None).
    """
    spec_by_name = {s.name: s for s in specs}
    for name, fv in fields.items():
        spec = spec_by_name.get(name)
        if spec is None:
            continue
        if getattr(spec, "choices", None):
            if fv.raw_value is None:
                continue
            value, warns = normalize_choice(fv.raw_value, spec.choices)
        elif spec.normalizer and spec.normalizer in NORMALIZERS:
            if fv.raw_value is None:
                continue
            value, warns = NORMALIZERS[spec.normalizer](fv.raw_value)
        else:
            # Không có normalizer: giữ value extractor đã đặt; chỉ điền từ raw_value
            # nếu value còn trống (vd anchor text thuần không khai báo normalizer).
            if fv.value is None and fv.raw_value is not None:
                fv.value = clean_spaces(fv.raw_value)
            continue
        fv.value = value
        fv.warnings.extend(warns)
