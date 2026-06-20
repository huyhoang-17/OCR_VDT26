"""Test M10: REST API (FastAPI) qua TestClient.

Cần fastapi + httpx (TestClient). Nếu thiếu -> skip. /process thật chạy trên PDF
text-layer (không cần engine OCR nặng).
"""

from __future__ import annotations

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


def test_forms_lists_generic() -> None:
    r = client.get("/forms")
    assert r.status_code == 200
    forms = r.json()["forms"]
    assert "generic" in forms


def test_engines_includes_rapidocr() -> None:
    r = client.get("/engines")
    assert r.status_code == 200
    body = r.json()
    assert "rapidocr" in body["engines"] and body["default"]


def _tiny_png() -> bytes:
    """Ảnh PNG trắng nhỏ -> OCR nhanh (không cần dữ liệu thật), đủ để test đường API."""
    import cv2
    import numpy as np

    img = np.full((40, 120, 3), 255, np.uint8)
    ok, buf = cv2.imencode(".png", img)
    assert ok
    return buf.tobytes()


def test_process_generic_image() -> None:
    pytest.importorskip("rapidocr_onnxruntime")
    r = client.post(
        "/process",
        files={"file": ("blank.png", _tiny_png(), "image/png")},
    )
    assert r.status_code == 200
    body = r.json()
    # Không nhận diện được biểu mẫu cụ thể -> fallback 'generic', kết xuất theo trang
    assert body["form_type"] == "generic"
    assert "pages" in body["output"] and "page_count" in body["output"]
    assert isinstance(body["warnings"], list)
    assert body["ocr_engine"]


def test_process_empty_file_is_400() -> None:
    r = client.post("/process", files={"file": ("empty.pdf", b"", "application/pdf")})
    assert r.status_code == 400


def test_process_unknown_form_is_400() -> None:
    pytest.importorskip("rapidocr_onnxruntime")
    r = client.post(
        "/process",
        files={"file": ("blank.png", _tiny_png(), "image/png")},
        data={"form_type": "khong_ton_tai"},
    )
    assert r.status_code == 400
