"""Script tiện dụng: sinh dữ liệu biểu mẫu giả lập + ground-truth.

Tương đương lệnh `ocr-idp make-data`. Chạy:
    python scripts/make_synthetic.py --out data --samples 3 --seed 42
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Cho phép chạy trực tiếp khi chưa `pip install -e .`
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ocr_idp.synthetic.generator import generate_all  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description="Sinh dữ liệu biểu mẫu chứng khoán giả lập.")
    ap.add_argument("--out", default="data", help="Thư mục dữ liệu (mặc định: data).")
    ap.add_argument("--samples", type=int, default=3, help="Số mẫu mỗi loại biểu mẫu.")
    ap.add_argument("--seed", type=int, default=42, help="Seed ngẫu nhiên (tái lập).")
    ap.add_argument("--dpi", type=int, default=150, help="DPI ảnh scan giả.")
    ap.add_argument("--no-scan", action="store_true", help="Chỉ sinh PDF, bỏ ảnh scan.")
    args = ap.parse_args()

    summary = generate_all(
        out_root=args.out, samples=args.samples, seed=args.seed, dpi=args.dpi,
        make_scan=not args.no_scan,
    )
    print("Đã sinh dữ liệu:")
    for k, v in summary.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
