"""So sánh các engine OCR trên cùng tập ảnh: thời gian + chất lượng text.

Chất lượng text đo bằng độ tương đồng (rapidfuzz token_set_ratio) giữa text engine
đọc được và TEXT THAM CHIẾU lấy từ text-layer của PDF cùng mẫu (chính xác tuyệt
đối). Hai chỉ số bổ sung cho nhau:
  * sim_unaccented: bỏ dấu cả hai phía -> đo khả năng đọc KÝ TỰ (công bằng với
    engine mất dấu như RapidOCR/Tesseract-lat).
  * sim_accented: giữ dấu -> phản ánh ưu thế GIỮ DẤU tiếng Việt (VietOCR/EasyOCR).

Engine thiếu dependency được liệt kê là "chưa sẵn sàng" (không làm hỏng benchmark)
-> trên host chỉ chạy engine nhẹ; trong Docker chạy đủ cả 5.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

from ..config import AppConfig, load_config
from ..logging_conf import get_logger
from ..normalize.text import clean_spaces, strip_accents

logger = get_logger(__name__)


@dataclass
class EngineStat:
    engine: str
    available: bool
    n_samples: int = 0
    avg_ms: float = 0.0
    avg_lines: float = 0.0
    avg_conf: float = 0.0
    sim_unaccented: float = 0.0
    sim_accented: float = 0.0
    note: str = ""


def _avg(xs: list[float]) -> float:
    return round(sum(xs) / len(xs), 2) if xs else 0.0


def discover_samples(data_root: str | Path = "data", limit: Optional[int] = None) -> list[tuple[Path, Path]]:
    """Tìm cặp (ảnh scan, PDF tham chiếu) trong data/synthetic/<form>/."""
    root = Path(data_root) / "synthetic"
    pairs: list[tuple[Path, Path]] = []
    for png in sorted(root.glob("*/*_scan.png")):
        pdf = png.with_name(png.name.replace("_scan.png", ".pdf"))
        if pdf.exists():
            pairs.append((png, pdf))
    return pairs[:limit] if limit else pairs


def _reference_text(pdf: Path, config: AppConfig) -> str:
    """Text tham chiếu = text-layer của PDF (chính xác tuyệt đối)."""
    from ..ocr.textlayer import ocr_result_from_text_layer
    from ..preprocess.pipeline_pre import Preprocessor

    pages = Preprocessor(config.preprocess).process_file(pdf)
    parts = [ocr_result_from_text_layer(p).text for p in pages if p.has_text_layer]
    return clean_spaces(" ".join(parts))


def _similarity(ref: str, hyp: str) -> float:
    from rapidfuzz import fuzz

    return float(fuzz.token_set_ratio(ref, hyp))


def benchmark_engines(
    engine_names: Optional[list[str]] = None,
    config: Optional[AppConfig] = None,
    data_root: str | Path = "data",
    limit: Optional[int] = None,
) -> dict:
    """Chạy benchmark. Trả về {stats: [EngineStat...], records: [...], n_samples}.

    Tiền xử lý mỗi ảnh MỘT LẦN và dùng chung cho mọi engine (đầu vào công bằng).
    """
    config = config or load_config()
    from ..ocr.registry import available_engines, get_engine
    from ..preprocess.pipeline_pre import Preprocessor

    avail = available_engines()
    names = engine_names if engine_names is not None else list(avail.keys())
    pairs = discover_samples(data_root, limit)

    # Tiền xử lý ảnh + text tham chiếu (tính một lần)
    pre = Preprocessor(config.preprocess)
    refs: dict[Path, str] = {}
    pages_by_png: dict[Path, object] = {}
    for png, pdf in pairs:
        refs[pdf] = _reference_text(pdf, config)
        pages_by_png[png] = pre.process_file(png)[0]

    stats: list[EngineStat] = []
    records: list[dict] = []
    for name in names:
        if not avail.get(name, False):
            stats.append(EngineStat(engine=name, available=False, note="thiếu dependency"))
            logger.info("Bỏ qua engine '%s' (chưa cài dependency).", name)
            continue
        try:
            engine = get_engine(name, config.ocr)
        except Exception as exc:  # noqa: BLE001
            stats.append(EngineStat(engine=name, available=False, note=f"lỗi khởi tạo: {exc}"))
            continue

        ms, nl, cf, su, sa = [], [], [], [], []
        for png, pdf in pairs:
            page = pages_by_png[png]
            res = engine.recognize(page)
            hyp = clean_spaces(res.text)
            ref = refs[pdf]
            s_un = _similarity(strip_accents(ref), strip_accents(hyp))
            s_ac = _similarity(ref, hyp)
            ms.append(res.elapsed_ms); nl.append(len(res.lines)); cf.append(res.mean_confidence)
            su.append(s_un); sa.append(s_ac)
            records.append({
                "engine": name, "sample": png.parent.name + "/" + png.name,
                "elapsed_ms": res.elapsed_ms, "lines": len(res.lines),
                "sim_unaccented": round(s_un, 1), "sim_accented": round(s_ac, 1),
            })
        stats.append(EngineStat(
            engine=name, available=True, n_samples=len(pairs),
            avg_ms=_avg(ms), avg_lines=_avg(nl), avg_conf=round(_avg(cf), 3),
            sim_unaccented=_avg(su), sim_accented=_avg(sa),
        ))

    return {"stats": stats, "records": records, "n_samples": len(pairs)}


def recommend_default(result: dict) -> Optional[str]:
    """Đề xuất engine mặc định: ưu tiên giữ dấu, rồi đọc ký tự, rồi nhanh."""
    ranked = [s for s in result["stats"] if s.available and s.n_samples > 0]
    if not ranked:
        return None
    best = max(ranked, key=lambda s: (s.sim_accented, s.sim_unaccented, -s.avg_ms))
    return best.engine


def _sorted_stats(stats: list[EngineStat]) -> list[EngineStat]:
    return sorted(stats, key=lambda s: (s.available, s.sim_unaccented, s.sim_accented), reverse=True)


def to_markdown(result: dict) -> str:
    rec = recommend_default(result)
    lines = [
        f"# Benchmark engine OCR ({result['n_samples']} ảnh scan)",
        "",
        "So với text-layer (tham chiếu chính xác). `sim_*` là % tương đồng token.",
        "",
        "| Engine | Sẵn sàng | #mẫu | TG TB (ms) | #dòng TB | conf TB | Sim(bỏ dấu) | Sim(có dấu) | Ghi chú |",
        "|---|---|--:|--:|--:|--:|--:|--:|---|",
    ]
    for s in _sorted_stats(result["stats"]):
        mark = "✅" if s.available else "—"
        lines.append(
            f"| {s.engine} | {mark} | {s.n_samples} | {s.avg_ms} | {s.avg_lines} | "
            f"{s.avg_conf} | {s.sim_unaccented} | {s.sim_accented} | {s.note} |"
        )
    lines += ["", f"**Đề xuất engine mặc định:** `{rec}`" if rec else "**Chưa có engine khả dụng để đề xuất.**", ""]
    return "\n".join(lines)


def to_csv(result: dict) -> str:
    import csv
    import io

    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["engine", "available", "n_samples", "avg_ms", "avg_lines",
                "avg_conf", "sim_unaccented", "sim_accented", "note"])
    for s in _sorted_stats(result["stats"]):
        row = asdict(s)
        w.writerow([row["engine"], row["available"], row["n_samples"], row["avg_ms"],
                    row["avg_lines"], row["avg_conf"], row["sim_unaccented"],
                    row["sim_accented"], row["note"]])
    return buf.getvalue()


def write_reports(result: dict, out_dir: str | Path = "outputs") -> dict[str, Path]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    md_path, csv_path = out / "benchmark.md", out / "benchmark.csv"
    md_path.write_text(to_markdown(result), encoding="utf-8")
    csv_path.write_text(to_csv(result), encoding="utf-8")
    return {"markdown": md_path, "csv": csv_path}
