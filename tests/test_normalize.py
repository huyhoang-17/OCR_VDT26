"""Test M4: chuẩn hóa ngày/số/điện thoại/email/giấy tờ/lựa chọn."""

from __future__ import annotations

import pytest

from ocr_idp.normalize.apply import (
    NORMALIZERS,
    normalize_choice,
)
from ocr_idp.normalize.dates import parse_date
from ocr_idp.normalize.numbers import parse_int
from ocr_idp.normalize.text import clean_spaces, norm_key, strip_accents


def test_strip_accents_and_keys() -> None:
    assert strip_accents("Nguyễn Đức") == "Nguyen Duc"
    assert norm_key("  Họ và tên:  ") == "ho va ten"
    assert clean_spaces("a   b\n c") == "a b c"


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("24/03/1979", "1979-03-24"),
        ("07-09-2016", "2016-09-07"),
        ("1.1.2020", "2020-01-01"),
        ("ngày 10 tháng 09 năm 2024", "2024-09-10"),
        ("ngay 5 thang 2 nam 2025", "2025-02-05"),
    ],
)
def test_parse_date_ok(raw: str, expected: str) -> None:
    value, warns = parse_date(raw)
    assert value == expected
    assert warns == []


def test_parse_date_invalid() -> None:
    value, warns = parse_date("32/13/2020")
    assert value is None and warns
    value, warns = parse_date("không có ngày")
    assert value is None and warns


def test_parse_int() -> None:
    assert parse_int("5.000")[0] == 5000
    assert parse_int("1,234,567")[0] == 1234567
    assert parse_int("85 000")[0] == 85000
    assert parse_int("abc")[0] is None


def test_phone_email_id_account() -> None:
    assert NORMALIZERS["phone"]("0940265423")[0] == "0940265423"
    assert NORMALIZERS["phone"]("090 123")[1]  # quá ngắn -> có cảnh báo
    assert NORMALIZERS["email"](" Abc@Mail.COM ")[0] == "abc@mail.com"
    assert NORMALIZERS["email"]("sai-email")[1]
    assert NORMALIZERS["id_number"]("819600133")[0] == "819600133"
    assert NORMALIZERS["id_number"]("123")[1]  # số chữ số bất thường
    assert NORMALIZERS["account_number"](" 204c161559 ")[0] == "204C161559"


def test_normalize_choice() -> None:
    assert normalize_choice("nam", ["Nam", "Nữ"])[0] == "Nam"
    assert normalize_choice("CMND", ["CCCD", "CMND", "Hộ chiếu"])[0] == "CMND"
    assert normalize_choice("ho chieu", ["CCCD", "CMND", "Hộ chiếu"])[0] == "Hộ chiếu"
    val, warns = normalize_choice("xyz", ["Nam", "Nữ"])
    assert warns  # không khớp -> cảnh báo
