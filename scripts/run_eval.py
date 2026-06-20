"""Đánh giá pipeline so với ground-truth -> in tóm tắt + ghi MD/CSV.

Ghép raw/form_N.pdf ↔ ground_truth/expect_N.json theo N (form_type = eformN).

    python scripts/run_eval.py                 # dùng text-layer nếu có, tất cả form
    python scripts/run_eval.py --kind scan     # ép OCR mọi trang (đo chất lượng OCR)
    python scripts/run_eval.py --form eform7
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ocr_idp.config import load_config  # noqa: E402
from ocr_idp.eval.report import evaluate_dataset, to_markdown, write_reports  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description="Đánh giá so ground-truth.")
    ap.add_argument("--kind", default="pdf", choices=["pdf", "scan"], help="Đầu vào đánh giá.")
    ap.add_argument("--form", default=None, help="Chỉ 1 form_type (mặc định: tất cả).")
    ap.add_argument("--data", default="data", help="Thư mục data.")
    ap.add_argument("--out", default="outputs", help="Thư mục ghi báo cáo.")
    ap.add_argument("--config", default=None)
    args = ap.parse_args()

    forms = [args.form] if args.form else None
    report = evaluate_dataset(config=load_config(args.config), kind=args.kind, forms=forms, data_root=args.data)
    if not report.samples:
        print("Không có cặp (raw/form_N.pdf ↔ ground_truth/expect_N.json).")
        return
    print(to_markdown(report))
    paths = write_reports(report, out_dir=args.out)
    print(f"Đã ghi: {paths['markdown']}, {paths['csv']}")


if __name__ == "__main__":
    main()
