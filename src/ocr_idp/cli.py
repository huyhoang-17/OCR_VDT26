"""Giao diện dòng lệnh (CLI) cho OCR-IDP.

Lệnh:
    ocr-idp version          # phiên bản
    ocr-idp info             # kiểm tra môi trường (Tesseract/poppler) + cấu hình
    ocr-idp forms            # liệt kê các plugin biểu mẫu đã đăng ký
    ocr-idp process <file>   # chạy pipeline 1 file  (khả dụng từ M4)
    ocr-idp batch <dir>      # chạy hàng loạt        (khả dụng từ M7)
    ocr-idp make-data        # sinh dữ liệu giả lập  (khả dụng từ M1)
    ocr-idp evaluate         # đánh giá so ground-truth (khả dụng từ M9)

Import nặng (OCR/engine) được nạp *bên trong* từng lệnh để `--help` luôn nhanh.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from . import __version__
from .config import load_config

# Bảo đảm in được tiếng Việt khi stdout bị redirect/capture (tránh UnicodeError).
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    except Exception:  # noqa: BLE001 - một số stream không hỗ trợ reconfigure
        pass

app = typer.Typer(
    name="ocr-idp",
    help="OCR & trích xuất dữ liệu (IDP) cho biểu mẫu chứng khoán tiếng Việt.",
    no_args_is_help=True,
    add_completion=False,
)
# legacy_windows=False: tránh đường render Win32 console (lỗi với Unicode khi
# output không phải terminal thật, vd bị pipe/redirect).
console = Console(legacy_windows=False)

_NOT_READY = "[yellow]Chưa khả dụng ở mốc hiện tại[/yellow] — sẽ có ở {milestone}."


@app.command()
def version() -> None:
    """In phiên bản."""
    console.print(f"OCR-IDP [bold cyan]v{__version__}[/bold cyan]")


@app.command()
def info(
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="File cấu hình YAML."),
) -> None:
    """Kiểm tra môi trường (dependency hệ thống) + tóm tắt cấu hình hiện tại."""
    cfg = load_config(config)

    # --- Dependency hệ thống ---------------------------------------------- #
    env = Table(title="Môi trường", show_header=True, header_style="bold")
    env.add_column("Thành phần")
    env.add_column("Trạng thái")

    def _check(cmd: str) -> str:
        path = shutil.which(cmd)
        return f"[green]OK[/green] ({path})" if path else "[red]Chưa cài[/red]"

    env.add_row("Tesseract (tesseract)", _check("tesseract"))
    env.add_row("poppler (pdftoppm)", _check("pdftoppm"))

    for mod in ("fitz", "cv2", "rapidocr_onnxruntime", "anthropic"):
        try:
            __import__(mod)
            env.add_row(f"python: {mod}", "[green]OK[/green]")
        except Exception:  # noqa: BLE001
            env.add_row(f"python: {mod}", "[yellow]Thiếu[/yellow]")
    console.print(env)

    # --- Tóm tắt cấu hình -------------------------------------------------- #
    summary = Table(title="Cấu hình", show_header=True, header_style="bold")
    summary.add_column("Khóa")
    summary.add_column("Giá trị")
    summary.add_row("OCR engine", cfg.ocr.engine)
    summary.add_row("Ngôn ngữ OCR", cfg.ocr.lang)
    summary.add_row("Tiền xử lý: binarize", cfg.preprocess.binarize)
    summary.add_row("Tiền xử lý: target_dpi", str(cfg.preprocess.target_dpi))
    summary.add_row("Trích xuất: default_strategy", cfg.extraction.default_strategy)
    summary.add_row("LLM enabled", str(cfg.extraction.llm.enabled))
    summary.add_row("Ngưỡng confidence", str(cfg.validation.min_confidence))
    console.print(summary)


@app.command()
def forms() -> None:
    """Liệt kê các plugin biểu mẫu đã đăng ký."""
    try:
        from .forms.base import list_forms  # nạp lười: registry sẽ có từ M4

        registered = list_forms()
    except Exception:  # noqa: BLE001
        registered = {}

    if not registered:
        console.print("Chưa có plugin biểu mẫu nào được đăng ký (sẽ thêm từ M4).")
        return

    table = Table(title="Biểu mẫu hỗ trợ", show_header=True, header_style="bold")
    table.add_column("form_type")
    table.add_column("Mô tả")
    for ftype, desc in registered.items():
        table.add_row(ftype, desc)
    console.print(table)


@app.command()
def process(
    input_file: Path = typer.Argument(..., help="File PDF/ảnh đầu vào."),
    form: Optional[str] = typer.Option(None, "--form", "-f", help="Loại biểu mẫu (form_type)."),
    engine: Optional[str] = typer.Option(None, "--engine", "-e", help="Engine OCR ghi đè."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="File JSON đầu ra."),
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="File cấu hình YAML."),
) -> None:
    """Chạy pipeline trên 1 file -> JSON theo schema. (Khả dụng từ M4.)"""
    console.print(_NOT_READY.format(milestone="M4 (MVP end-to-end)"))
    raise typer.Exit(code=0)


@app.command()
def batch(
    input_dir: Path = typer.Argument(..., help="Thư mục chứa file đầu vào."),
    config: Optional[Path] = typer.Option(None, "--config", "-c"),
) -> None:
    """Chạy hàng loạt. (Khả dụng từ M7.)"""
    console.print(_NOT_READY.format(milestone="M7"))
    raise typer.Exit(code=0)


@app.command(name="make-data")
def make_data(
    out_dir: Optional[Path] = typer.Option(None, "--out", help="Thư mục lưu dữ liệu (mặc định: data_dir)."),
    samples: int = typer.Option(3, "--samples", "-n", help="Số mẫu mỗi loại biểu mẫu."),
    seed: int = typer.Option(42, "--seed", help="Seed ngẫu nhiên (tái lập)."),
    dpi: int = typer.Option(150, "--dpi", help="DPI của ảnh scan giả."),
    no_scan: bool = typer.Option(False, "--no-scan", help="Chỉ sinh PDF, bỏ ảnh scan."),
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="File cấu hình YAML."),
) -> None:
    """Sinh dữ liệu biểu mẫu giả lập (PDF + ảnh scan) + ground-truth + chia tập."""
    cfg = load_config(config)
    out = str(out_dir) if out_dir else cfg.data_dir
    try:
        from .synthetic.generator import generate_all

        summary = generate_all(out_root=out, samples=samples, seed=seed, dpi=dpi, make_scan=not no_scan)
    except ImportError as exc:  # thiếu reportlab/Pillow/opencv
        console.print(
            f"[red]Thiếu thư viện để sinh dữ liệu:[/red] {exc}\n"
            "Cài: [cyan]pip install reportlab pillow opencv-python-headless numpy[/cyan]"
        )
        raise typer.Exit(code=1)
    except RuntimeError as exc:  # thiếu font
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1)

    table = Table(title="Đã sinh dữ liệu giả lập", show_header=True, header_style="bold")
    table.add_column("Loại biểu mẫu")
    table.add_column("Số mẫu", justify="right")
    for ftype, count in summary["forms"].items():
        table.add_row(ftype, str(count))
    console.print(table)
    console.print(
        f"Tổng [bold]{summary['files_written']}[/bold] file vào [cyan]{summary['out_root']}/synthetic[/cyan] "
        f"(ground-truth ở [cyan]{summary['out_root']}/ground_truth[/cyan], chia tập ở "
        f"[cyan]{summary['out_root']}/splits[/cyan]). Font: {summary['font']}"
    )


@app.command()
def evaluate(
    config: Optional[Path] = typer.Option(None, "--config", "-c"),
) -> None:
    """Đánh giá kết quả so với ground-truth -> bảng MD/CSV. (Khả dụng từ M9.)"""
    console.print(_NOT_READY.format(milestone="M9"))
    raise typer.Exit(code=0)


if __name__ == "__main__":
    app()
