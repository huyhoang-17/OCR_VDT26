"""Chạy thử bước tiền xử lý 1 file và lưu ảnh kết quả để xem bằng mắt.

    python scripts/preprocess_demo.py data/synthetic/order_slip/sample_01_scan.png
    python scripts/preprocess_demo.py <file.pdf> --binarize sauvola --out outputs/pre
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ocr_idp.config import PreprocessConfig  # noqa: E402
from ocr_idp.preprocess.base import write_image_file  # noqa: E402
from ocr_idp.preprocess.pipeline_pre import Preprocessor  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description="Demo tiền xử lý tài liệu.")
    ap.add_argument("input", help="File PDF/ảnh đầu vào.")
    ap.add_argument("--out", default="outputs/preprocess", help="Thư mục lưu kết quả.")
    ap.add_argument("--dpi", type=int, default=200)
    ap.add_argument("--binarize", default="none", help="none|otsu|adaptive|sauvola")
    ap.add_argument("--no-deskew", action="store_true")
    ap.add_argument("--no-denoise", action="store_true")
    args = ap.parse_args()

    cfg = PreprocessConfig(
        target_dpi=args.dpi,
        binarize=args.binarize,
        deskew=not args.no_deskew,
        denoise=not args.no_denoise,
    )
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    pages = Preprocessor(cfg).process_file(args.input)
    stem = Path(args.input).stem
    for page in pages:
        out_path = out_dir / f"{stem}_p{page.page_index}_pre.png"
        write_image_file(out_path, page.image)
        print(f"Trang {page.page_index}: {page.width}x{page.height} "
              f"text_layer={page.has_text_layer} meta={page.preprocess_meta}")
        print(f"  -> {out_path}")


if __name__ == "__main__":
    main()
