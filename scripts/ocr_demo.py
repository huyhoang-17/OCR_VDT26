"""Chạy thử OCR 1 file: tiền xử lý -> OCR -> lưu ảnh overlay bbox + in text.

    python scripts/ocr_demo.py data/raw/form_1.pdf
    python scripts/ocr_demo.py data/raw/form_7.pdf --engine rapidocr
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ocr_idp.config import load_config  # noqa: E402
from ocr_idp.ocr.overlay import draw_ocr_overlay  # noqa: E402
from ocr_idp.pipeline import Pipeline  # noqa: E402
from ocr_idp.preprocess.base import write_image_file  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description="Demo OCR + overlay bbox.")
    ap.add_argument("input", help="File PDF/ảnh.")
    ap.add_argument("--engine", default=None, help="Engine OCR (ghi đè cấu hình).")
    ap.add_argument("--out", default="outputs/ocr", help="Thư mục lưu overlay.")
    ap.add_argument("--no-textlayer", action="store_true", help="Không dùng text-layer (ép OCR).")
    ap.add_argument("--config", default=None)
    args = ap.parse_args()

    cfg = load_config(args.config)
    if args.engine:
        cfg.ocr.engine = args.engine

    pipe = Pipeline(cfg)
    pages = pipe.preprocess(args.input)
    results = pipe.ocr(pages, use_text_layer=not args.no_textlayer)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(args.input).stem

    for page, res in zip(pages, results):
        overlay = draw_ocr_overlay(page.image, res)
        out_path = out_dir / f"{stem}_p{page.page_index}_ocr.png"
        write_image_file(out_path, overlay)
        print(f"\n=== Trang {page.page_index} | engine={res.engine} | "
              f"{len(res.lines)} dòng | {res.elapsed_ms} ms | conf~{res.mean_confidence:.2f} ===")
        for i, line in enumerate(res.lines):
            print(f"  [{i:2d}] ({line.confidence:.2f}) {line.text}")
        print(f"  -> overlay: {out_path}")


if __name__ == "__main__":
    main()
