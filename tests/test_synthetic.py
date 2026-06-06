"""Test M1: schema hợp lệ + bộ sinh dữ liệu chạy được và ground-truth đúng cấu trúc."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

SCHEMA_DIR = Path("src/ocr_idp/forms")
SCHEMAS = ["account_opening/schema.json", "order_slip/schema.json", "shareholder_list/schema.json"]


def test_schemas_are_valid_json_schema() -> None:
    for rel in SCHEMAS:
        data = json.loads((SCHEMA_DIR / rel).read_text(encoding="utf-8"))
        assert data["type"] == "object"
        assert "properties" in data and "form_type" in data["properties"]
        assert "required" in data


def test_record_builders_match_schema_keys() -> None:
    # Không cần reportlab/PIL: chỉ kiểm tra bộ sinh bản ghi
    import random

    from ocr_idp.synthetic import generator as g

    rng = random.Random(0)
    acc = g.make_account_opening(rng)
    assert acc["form_type"] == "account_opening_individual"
    assert acc["investor"]["id_document"]["type"] in {"CCCD", "CMND"}
    assert "thường" in acc["account"]["account_types"] or "ký quỹ" in acc["account"]["account_types"]

    order = g.make_order_slip(rng)
    assert order["side"] in {"MUA", "BÁN"}
    if order["order_type"] in {"ATO", "ATC", "MP", "MTL"}:
        assert order["price"] is None

    sh = g.make_shareholder_list(rng)
    assert sh["total_shares"] == sum(p["shares"] for p in sh["shareholders"])
    assert sh["total_shareholders"] == len(sh["shareholders"])


def test_helpers() -> None:
    from ocr_idp.synthetic.generator import unaccent, vn_date, vn_num

    assert unaccent("Nguyễn Đức") == "Nguyen Duc"
    assert vn_date("2003-05-09") == "09/05/2003"
    assert vn_num(1000000) == "1.000.000"


def test_generate_all_end_to_end(tmp_path) -> None:
    pytest.importorskip("reportlab")
    pytest.importorskip("PIL")
    pytest.importorskip("cv2")
    pytest.importorskip("numpy")

    from ocr_idp.synthetic.generator import generate_all

    summary = generate_all(out_root=str(tmp_path), samples=1, seed=1, dpi=100)
    assert summary["files_written"] == 6  # 3 form x (pdf + scan)

    for ftype in ("account_opening_individual", "order_slip", "shareholder_list"):
        assert (tmp_path / "synthetic" / ftype / "sample_01.pdf").exists()
        assert (tmp_path / "synthetic" / ftype / "sample_01_scan.png").exists()
        gt = json.loads((tmp_path / "ground_truth" / ftype / "sample_01.json").read_text(encoding="utf-8"))
        assert gt["form_type"] == ftype

    for split in ("train", "dev", "test"):
        assert (tmp_path / "splits" / f"{split}.txt").exists()
