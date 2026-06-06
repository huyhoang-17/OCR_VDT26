"""Giao diện dòng lệnh (CLI) cho OCR-IDP.

Lệnh:
    ocr-idp version          # phiên bản
    ocr-idp info             # kiểm tra môi trường (Tesseract/poppler) + cấu hình
    ocr-idp forms            # liệt kê các plugin biểu mẫu đã đăng ký
    ocr-idp make-data        # sinh dữ liệu giả lập + ground-truth
    ocr-idp process <file>   # chạy pipeline 1 file -> JSON
    ocr-idp batch <dir>      # chạy hàng loạt cả thư mục
    ocr-idp benchmark        # so sánh engine OCR -> MD/CSV
    ocr-idp evaluate         # đánh giá so ground-truth -> MD/CSV
    ocr-idp serve-api        # chạy REST API (FastAPI)
    ocr-idp serve-web        # chạy web demo (Streamlit)

Import nặng (OCR/engine) được nạp *bên trong* từng lệnh để `--help` luôn nhanh.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from . import __version__
from .config import load_config
from .logging_conf import _force_utf8_streams

# Bảo đảm in được tiếng Việt khi stdout bị redirect/capture (tránh UnicodeError).
_force_utf8_streams()

app = typer.Typer(
    name="ocr-idp",
    help="OCR & trích xuất dữ liệu (IDP) cho biểu mẫu chứng khoán tiếng Việt.",
    no_args_is_help=True,
    add_completion=False,
)
# legacy_windows=False: tránh đường render Win32 console (lỗi với Unicode khi
# output không phải terminal thật, vd bị pipe/redirect).
console = Console(legacy_windows=False)


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

    # --- Engine OCR đã đăng ký --------------------------------------------- #
    try:
        from .ocr.registry import available_engines

        engines = available_engines()
        eng_table = Table(title="Engine OCR", show_header=True, header_style="bold")
        eng_table.add_column("Engine")
        eng_table.add_column("Sẵn sàng")
        for name, ok in engines.items():
            mark = "[green]OK[/green]" if ok else "[yellow]Chưa cài dep[/yellow]"
            eng_table.add_row(name + (" (mặc định)" if name == cfg.ocr.engine else ""), mark)
        console.print(eng_table)
    except Exception as exc:  # noqa: BLE001
        console.print(f"[yellow]Không liệt kê được engine OCR: {exc}[/yellow]")

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
        from .forms.base import list_forms  # nạp lười registry plugin

        registered = list_forms()
    except Exception:  # noqa: BLE001
        registered = {}

    if not registered:
        console.print("Chưa có plugin biểu mẫu nào được đăng ký.")
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
    form: Optional[str] = typer.Option(None, "--form", "-f", help="Loại biểu mẫu (mặc định: tự đoán)."),
    engine: Optional[str] = typer.Option(None, "--engine", "-e", help="Engine OCR ghi đè."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="File JSON đầu ra."),
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="File cấu hình YAML."),
) -> None:
    """Chạy pipeline trên 1 file PDF/ảnh -> JSON theo schema + cảnh báo cần kiểm tra."""
    import json

    from .pipeline import Pipeline

    if not input_file.exists():
        console.print(f"[red]Không tìm thấy file: {input_file}[/red]")
        raise typer.Exit(code=1)

    cfg = load_config(config)
    if engine:
        cfg.ocr.engine = engine

    try:
        result = Pipeline(cfg).run(input_file, form_type=form)
    except (KeyError, ValueError, RuntimeError) as exc:
        console.print(f"[red]Lỗi: {exc}[/red]")
        raise typer.Exit(code=1)

    json_str = json.dumps(result.output_json, ensure_ascii=False, indent=2)
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json_str, encoding="utf-8")
        console.print(f"[green]Đã ghi JSON:[/green] {output}")
    else:
        print(json_str)

    # Bảng cảnh báo (trường cần người kiểm tra)
    warnings = result.output_json.get("_meta", {}).get("warnings", [])
    console.print(
        f"\n[bold]{result.form_type}[/bold] | engine={result.output_json['_meta'].get('ocr_engine')} "
        f"| {result.timings_ms}"
    )
    if warnings:
        wt = Table(title=f"Cảnh báo cần kiểm tra ({len(warnings)})", header_style="bold yellow")
        wt.add_column("#", justify="right")
        wt.add_column("Nội dung")
        for i, w in enumerate(warnings, 1):
            wt.add_row(str(i), w)
        console.print(wt)
    else:
        console.print("[green]Không có cảnh báo.[/green]")


@app.command()
def batch(
    input_dir: Path = typer.Argument(..., help="Thư mục chứa file PDF/ảnh đầu vào."),
    form: Optional[str] = typer.Option(None, "--form", "-f", help="Loại biểu mẫu (mặc định: tự đoán)."),
    engine: Optional[str] = typer.Option(None, "--engine", "-e", help="Engine OCR ghi đè."),
    out_dir: Path = typer.Option(Path("outputs/json"), "--out", "-o", help="Thư mục JSON đầu ra."),
    recursive: bool = typer.Option(False, "--recursive", "-r", help="Quét cả thư mục con."),
    config: Optional[Path] = typer.Option(None, "--config", "-c"),
) -> None:
    """Chạy pipeline hàng loạt cho mọi file PDF/ảnh trong thư mục -> JSON + tóm tắt."""
    import json

    from .pipeline import Pipeline

    if not input_dir.is_dir():
        console.print(f"[red]Không phải thư mục: {input_dir}[/red]")
        raise typer.Exit(code=1)

    exts = {".pdf", ".png", ".jpg", ".jpeg"}
    globber = input_dir.rglob if recursive else input_dir.glob
    files = sorted(p for p in globber("*") if p.suffix.lower() in exts)
    if not files:
        console.print(f"[yellow]Không tìm thấy file PDF/ảnh trong {input_dir}[/yellow]")
        raise typer.Exit(code=0)

    cfg = load_config(config)
    if engine:
        cfg.ocr.engine = engine
    pipe = Pipeline(cfg)
    out_dir.mkdir(parents=True, exist_ok=True)

    table = Table(title=f"Batch ({len(files)} file)", header_style="bold")
    for col in ("File", "Biểu mẫu", "#cảnh báo", "Trạng thái"):
        table.add_column(col)

    ok = 0
    for f in files:
        try:
            result = pipe.run(f, form_type=form)
            (out_dir / f"{f.stem}.json").write_text(
                json.dumps(result.output_json, ensure_ascii=False, indent=2), encoding="utf-8")
            n_warn = len(result.output_json.get("_meta", {}).get("warnings", []))
            table.add_row(f.name, result.form_type or "—", str(n_warn), "[green]OK[/green]")
            ok += 1
        except Exception as exc:  # noqa: BLE001
            table.add_row(f.name, "—", "—", f"[red]Lỗi: {exc}[/red]")

    console.print(table)
    console.print(f"[green]Xong {ok}/{len(files)} file[/green] -> [cyan]{out_dir}[/cyan]")


@app.command(name="serve-api")
def serve_api(
    host: str = typer.Option("127.0.0.1", "--host", help="Địa chỉ bind."),
    port: int = typer.Option(8000, "--port", "-p", help="Cổng."),
    reload: bool = typer.Option(False, "--reload", help="Tự nạp lại khi sửa code (dev)."),
) -> None:
    """Chạy REST API (FastAPI/uvicorn). Tài liệu: http://<host>:<port>/docs"""
    try:
        import uvicorn
    except ImportError:
        console.print("[red]Thiếu uvicorn.[/red] Cài: [cyan]pip install -e \".[api]\"[/cyan]")
        raise typer.Exit(code=1)
    console.print(f"[green]REST API:[/green] http://{host}:{port}/docs")
    uvicorn.run("ocr_idp.api.app:app", host=host, port=port, reload=reload)


@app.command(name="serve-web")
def serve_web(
    port: int = typer.Option(8501, "--port", "-p", help="Cổng Streamlit."),
) -> None:
    """Chạy web demo (Streamlit)."""
    import importlib.util
    import subprocess
    import sys

    if importlib.util.find_spec("streamlit") is None:
        console.print("[red]Thiếu streamlit.[/red] Cài: [cyan]pip install -e \".[web]\"[/cyan]")
        raise typer.Exit(code=1)
    app_path = Path(__file__).resolve().parent / "webapp" / "app.py"
    console.print(f"[green]Web demo:[/green] http://localhost:{port}")
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(app_path),
                    "--server.port", str(port)], check=False)


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
def benchmark(
    engines: Optional[str] = typer.Option(None, "--engines", "-e", help="DS engine (phẩy). Mặc định: tất cả đã đăng ký."),
    limit: Optional[int] = typer.Option(None, "--limit", "-n", help="Giới hạn số ảnh scan."),
    data_root: Path = typer.Option(Path("data"), "--data", help="Thư mục data (chứa synthetic/)."),
    out_dir: Path = typer.Option(Path("outputs"), "--out", help="Thư mục ghi báo cáo."),
    config: Optional[Path] = typer.Option(None, "--config", "-c"),
) -> None:
    """So sánh các engine OCR (thời gian + chất lượng) trên ảnh scan -> MD/CSV + đề xuất engine."""
    from .eval.benchmark import benchmark_engines, recommend_default, write_reports

    cfg = load_config(config)
    names = [e.strip() for e in engines.split(",")] if engines else None
    with console.status("[cyan]Đang chạy benchmark engine OCR...[/cyan]"):
        result = benchmark_engines(engine_names=names, config=cfg, data_root=str(data_root), limit=limit)

    if result["n_samples"] == 0:
        console.print("[yellow]Không tìm thấy ảnh scan nào trong data/synthetic. Chạy: ocr-idp make-data[/yellow]")
        raise typer.Exit(code=0)

    table = Table(title=f"Benchmark engine OCR ({result['n_samples']} ảnh)", header_style="bold")
    for col in ("Engine", "Sẵn sàng", "TG TB(ms)", "#dòng", "Sim bỏ dấu", "Sim có dấu", "Ghi chú"):
        table.add_column(col)
    from .eval.benchmark import _sorted_stats

    for s in _sorted_stats(result["stats"]):
        table.add_row(
            s.engine, "[green]OK[/green]" if s.available else "[yellow]—[/yellow]",
            str(s.avg_ms), str(s.avg_lines), str(s.sim_unaccented), str(s.sim_accented), s.note,
        )
    console.print(table)

    paths = write_reports(result, out_dir=out_dir)
    rec = recommend_default(result)
    if rec:
        console.print(f"[green]Đề xuất engine mặc định:[/green] [bold]{rec}[/bold]")
    console.print(f"Đã ghi báo cáo: [cyan]{paths['markdown']}[/cyan], [cyan]{paths['csv']}[/cyan]")


@app.command()
def evaluate(
    kind: str = typer.Option("pdf", "--kind", "-k", help="Đầu vào đánh giá: pdf (text-layer) | scan (ảnh OCR)."),
    form: Optional[str] = typer.Option(None, "--form", "-f", help="Chỉ đánh giá 1 form_type (mặc định: tất cả)."),
    data_root: Path = typer.Option(Path("data"), "--data", help="Thư mục data (ground_truth/ + synthetic/)."),
    out_dir: Path = typer.Option(Path("outputs"), "--out", help="Thư mục ghi báo cáo."),
    config: Optional[Path] = typer.Option(None, "--config", "-c"),
) -> None:
    """Đánh giá kết quả so với ground-truth -> số liệu + báo cáo MD/CSV."""
    from .eval.report import evaluate_dataset, write_reports

    cfg = load_config(config)
    forms = [form] if form else None
    with console.status(f"[cyan]Đang đánh giá ({kind})...[/cyan]"):
        report = evaluate_dataset(config=cfg, kind=kind, forms=forms, data_root=str(data_root))

    if not report.samples:
        console.print("[yellow]Không tìm thấy cặp (ground-truth, input). Chạy: ocr-idp make-data[/yellow]")
        raise typer.Exit(code=0)

    o = report.overall
    summary = Table(title=f"Đánh giá ({kind}) — {o.n_samples} mẫu", header_style="bold")
    for col in ("Form", "#mẫu", "Exact form", "Acc trường", "P", "R", "F1"):
        summary.add_column(col)

    def _pct(x: float) -> str:
        return f"{x * 100:.1f}%"

    for ft, fa in sorted(report.form_aggs.items()):
        summary.add_row(ft, str(fa.n_samples), _pct(fa.form_exact_rate), _pct(fa.field_accuracy),
                        _pct(fa.prf.precision), _pct(fa.prf.recall), _pct(fa.prf.f1))
    summary.add_row("[bold](tất cả)[/bold]", str(o.n_samples), _pct(o.form_exact_rate),
                    _pct(o.field_accuracy), _pct(o.prf.precision), _pct(o.prf.recall), _pct(o.prf.f1))
    console.print(summary)
    if o.errors:
        console.print(f"Lỗi theo loại: [yellow]{dict(o.errors)}[/yellow]")

    paths = write_reports(report, out_dir=out_dir)
    console.print(f"Đã ghi báo cáo: [cyan]{paths['markdown']}[/cyan], [cyan]{paths['csv']}[/cyan]")


if __name__ == "__main__":
    app()
