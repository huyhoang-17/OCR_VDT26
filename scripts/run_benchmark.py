"""So sánh các engine OCR trên ảnh scan giả lập -> báo cáo MD/CSV + đề xuất engine.

    python scripts/run_benchmark.py                 # tất cả engine đã đăng ký
    python scripts/run_benchmark.py --engines rapidocr,tesseract --limit 3
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ocr_idp.config import load_config  # noqa: E402
from ocr_idp.eval.benchmark import benchmark_engines, recommend_default, to_markdown, write_reports  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description="Benchmark engine OCR.")
    ap.add_argument("--engines", default=None, help="DS engine (phẩy). Mặc định: tất cả.")
    ap.add_argument("--limit", type=int, default=None, help="Giới hạn số ảnh scan.")
    ap.add_argument("--data", default="data", help="Thư mục data (chứa synthetic/).")
    ap.add_argument("--out", default="outputs", help="Thư mục ghi báo cáo.")
    ap.add_argument("--config", default=None)
    args = ap.parse_args()

    names = [e.strip() for e in args.engines.split(",")] if args.engines else None
    result = benchmark_engines(
        engine_names=names, config=load_config(args.config), data_root=args.data, limit=args.limit
    )
    if result["n_samples"] == 0:
        print("Không có ảnh scan trong data/synthetic. Chạy 'ocr-idp make-data' trước.")
        return

    print(to_markdown(result))
    paths = write_reports(result, out_dir=args.out)
    print(f"\nĐề xuất engine mặc định: {recommend_default(result)}")
    print(f"Đã ghi: {paths['markdown']}, {paths['csv']}")


if __name__ == "__main__":
    main()
