"""Test M10: REST API (FastAPI) qua TestClient.

Cần fastapi + httpx (TestClient). Nếu thiếu -> skip. /process thật chạy trên PDF
text-layer (không cần engine OCR nặng).
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from ocr_idp.api.app import app  # noqa: E402

client = TestClient(app)


def test_health() -> None:
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok" and body["version"] and body["default_engine"]


def test_forms_lists_three() -> None:
    r = client.get("/forms")
    assert r.status_code == 200
    forms = r.json()["forms"]
    for ft in ("account_opening_individual", "order_slip", "shareholder_list"):
        assert ft in forms


def test_engines_includes_rapidocr() -> None:
    r = client.get("/engines")
    assert r.status_code == 200
    body = r.json()
    assert "rapidocr" in body["engines"] and body["default"]


def test_process_form_a_pdf() -> None:
    pytest.importorskip("fitz")
    sample = Path("data/synthetic/account_opening_individual/sample_01.pdf")
    if not sample.exists():
        pytest.skip("Chưa có dữ liệu synthetic (chạy: ocr-idp make-data)")

    with sample.open("rb") as f:
        r = client.post(
            "/process",
            files={"file": ("sample_01.pdf", f, "application/pdf")},
            data={"form_type": "account_opening_individual"},
        )
    assert r.status_code == 200
    body = r.json()
    assert body["form_type"] == "account_opening_individual"
    assert body["output"]["investor"]["full_name"]
    assert isinstance(body["warnings"], list)
    assert "textlayer" in body["ocr_engine"]


def test_process_empty_file_is_400() -> None:
    r = client.post("/process", files={"file": ("empty.pdf", b"", "application/pdf")})
    assert r.status_code == 400


def test_process_unknown_form_is_400() -> None:
    pytest.importorskip("fitz")
    sample = Path("data/synthetic/order_slip/sample_01.pdf")
    if not sample.exists():
        pytest.skip("Chưa có dữ liệu synthetic")
    with sample.open("rb") as f:
        r = client.post(
            "/process",
            files={"file": ("sample_01.pdf", f, "application/pdf")},
            data={"form_type": "khong_ton_tai"},
        )
    assert r.status_code == 400
