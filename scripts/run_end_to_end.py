"""Chạy pipeline end-to-end và lưu JSON kết quả.

    # 1 file:
    python scripts/run_end_to_end.py data/synthetic/account_opening_individual/sample_01.pdf
    # mặc định: tất cả mẫu Form A trong data/synthetic:
    python scripts/run_end_to_end.py --engine rapidocr
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ocr_idp.config import load_config  # noqa: E402
from ocr_idp.pipeline import Pipeline  # noqa: E402


def _gather(input_arg: str | None) -> list[Path]:
    if input_arg:
        return [Path(input_arg)]
    base = Path("data/synthetic/account_opening_individual")
    return sorted([*base.glob("*.pdf"), *base.glob("*_scan.png")]) if base.exists() else []


def main() -> None:
    ap = argparse.ArgumentParser(description="Chạy pipeline end-to-end -> JSON.")
    ap.add_argument("input", nargs="?", help="File PDF/ảnh (bỏ trống = mẫu Form A).")
    ap.add_argument("--form", default=None, help="form_type (mặc định: tự đoán).")
    ap.add_argument("--engine", default=None, help="Engine OCR.")
    ap.add_argument("--out", default="outputs/json", help="Thư mục lưu JSON.")
    ap.add_argument("--config", default=None)
    args = ap.parse_args()

    cfg = load_config(args.config)
    if args.engine:
        cfg.ocr.engine = args.engine
    pipe = Pipeline(cfg)

    files = _gather(args.input)
    if not files:
        print("Không có file để xử lý. Chạy 'ocr-idp make-data' trước.")
        return

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    for f in files:
        try:
            result = pipe.run(f, form_type=args.form)
        except Exception as exc:  # noqa: BLE001
            print(f"[LỖI] {f.name}: {exc}")
            continue
        out_path = out_dir / f"{f.stem}.json"
        out_path.write_text(
            json.dumps(result.output_json, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        n_warn = len(result.output_json.get("_meta", {}).get("warnings", []))
        print(f"{f.name:42s} -> {out_path.name} | {result.form_type} | "
              f"{n_warn} cảnh báo | {result.timings_ms}")


if __name__ == "__main__":
    main()
