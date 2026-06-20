"""Đánh giá toàn tập dữ liệu so ground-truth -> số liệu + báo cáo MD/CSV.

Chỉ số:
  * accuracy theo trường (exact-match từng trường).
  * exact-match toàn form (mọi trường đúng).
  * precision / recall / F1 (micro) ở mức "trích đúng giá trị có thật".
  * phân loại lỗi: missing | extra | ocr_error | format_error.
  * thời gian xử lý trung bình (preprocess / ocr / extract) theo form.

Dùng để chốt engine/cấu hình mặc định bằng SỐ LIỆU (không cảm tính).
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from ..config import AppConfig, load_config
from ..logging_conf import get_logger
from .metrics import FieldOutcome, compare_documents

logger = get_logger(__name__)


@dataclass
class SampleResult:
    form_type: str
    stem: str
    input_path: str
    outcomes: list[FieldOutcome]
    form_exact: bool
    timings_ms: dict[str, float]
    error: Optional[str] = None  # nếu pipeline lỗi cả file


@dataclass
class PRF:
    tp: int = 0
    fp: int = 0
    fn: int = 0

    @property
    def precision(self) -> float:
        return self.tp / (self.tp + self.fp) if (self.tp + self.fp) else 0.0

    @property
    def recall(self) -> float:
        return self.tp / (self.tp + self.fn) if (self.tp + self.fn) else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) else 0.0

    def add(self, o: FieldOutcome) -> None:
        correct = o.exact
        if o.pred_present and o.gt_present and correct:
            self.tp += 1
        if o.pred_present and not (o.gt_present and correct):
            self.fp += 1
        if o.gt_present and not (o.pred_present and correct):
            self.fn += 1


@dataclass
class FieldAgg:
    path: str
    n: int = 0
    exact: int = 0
    sim_sum: float = 0.0
    prf: PRF = field(default_factory=PRF)
    errors: Counter = field(default_factory=Counter)

    @property
    def accuracy(self) -> float:
        return self.exact / self.n if self.n else 0.0

    @property
    def mean_sim(self) -> float:
        return self.sim_sum / self.n if self.n else 0.0


@dataclass
class FormAgg:
    form_type: str
    n_samples: int = 0
    n_form_exact: int = 0
    n_fields: int = 0
    n_exact: int = 0
    prf: PRF = field(default_factory=PRF)
    errors: Counter = field(default_factory=Counter)
    timings: Counter = field(default_factory=Counter)

    @property
    def form_exact_rate(self) -> float:
        return self.n_form_exact / self.n_samples if self.n_samples else 0.0

    @property
    def field_accuracy(self) -> float:
        return self.n_exact / self.n_fields if self.n_fields else 0.0

    def avg_timing(self, key: str) -> float:
        return round(self.timings[key] / self.n_samples, 1) if self.n_samples else 0.0


@dataclass
class EvalReport:
    kind: str
    samples: list[SampleResult]
    field_aggs: dict[str, FieldAgg]
    form_aggs: dict[str, FormAgg]
    overall: FormAgg


def _discover(
    data_root: str | Path, kind: str, forms: Optional[list[str]]
) -> list[tuple[str, str, Path, Path]]:
    """Trả về (form_type, stem, input_pdf, gt_path) cho mỗi cặp dữ liệu thật.

    Layout dữ liệu thật: `ground_truth/expect_<N>.json` ghép với `raw/form_<N>.pdf`
    theo số N. form_type = 'eform<N>' (lấy từ tên file). `kind` chỉ là nhãn báo cáo
    (chọn đường text-layer hay ép OCR được xử lý ở `evaluate_dataset`).
    """
    gt_root = Path(data_root) / "ground_truth"
    raw_root = Path(data_root) / "raw"
    items: list[tuple[str, str, Path, Path]] = []
    for gt_file in sorted(gt_root.glob("expect_*.json")):
        n = gt_file.stem.split("expect_", 1)[-1]  # "expect_7" -> "7"
        form_type = f"eform{n}"
        if forms and form_type not in forms:
            continue
        pdf = raw_root / f"form_{n}.pdf"
        if pdf.exists():
            items.append((form_type, f"form_{n}", pdf, gt_file))
    return items


def evaluate_dataset(
    config: Optional[AppConfig] = None,
    kind: str = "pdf",
    forms: Optional[list[str]] = None,
    data_root: str | Path = "data",
) -> EvalReport:
    config = config or load_config()
    from ..pipeline import Pipeline

    pipe = Pipeline(config)
    items = _discover(data_root, kind, forms)
    # kind='scan' -> ép OCR mọi trang (kể cả PDF số có text-layer) để đo chất lượng OCR.
    use_text_layer = kind != "scan"

    samples: list[SampleResult] = []
    for form_type, stem, inp, gt_path in items:
        gt = json.loads(gt_path.read_text(encoding="utf-8"))
        try:
            # form_type=None -> pipeline fallback 'generic' (chưa có extractor eform).
            res = pipe.run(inp, use_text_layer=use_text_layer)
            outcomes = compare_documents(res.output_json, gt)
            form_exact = bool(outcomes) and all(o.exact for o in outcomes)
            samples.append(SampleResult(form_type, stem, str(inp), outcomes, form_exact, dict(res.timings_ms)))
        except Exception as exc:  # noqa: BLE001
            logger.warning("Lỗi đánh giá %s: %s", inp, exc)
            samples.append(SampleResult(form_type, stem, str(inp), [], False, {}, error=str(exc)))

    return _aggregate(kind, samples)


def _aggregate(kind: str, samples: list[SampleResult]) -> EvalReport:
    field_aggs: dict[str, FieldAgg] = {}
    form_aggs: dict[str, FormAgg] = {}
    overall = FormAgg(form_type="(tất cả)")

    for s in samples:
        fa = form_aggs.setdefault(s.form_type, FormAgg(form_type=s.form_type))
        fa.n_samples += 1
        overall.n_samples += 1
        for k, v in (s.timings_ms or {}).items():
            fa.timings[k] += v
            overall.timings[k] += v
        if s.error:
            continue
        if s.form_exact:
            fa.n_form_exact += 1
            overall.n_form_exact += 1
        for o in s.outcomes:
            agg = field_aggs.setdefault(o.path, FieldAgg(path=o.path))
            agg.n += 1
            agg.sim_sum += o.similarity
            agg.prf.add(o)
            fa.prf.add(o)
            overall.prf.add(o)
            fa.n_fields += 1
            overall.n_fields += 1
            if o.exact:
                agg.exact += 1
                fa.n_exact += 1
                overall.n_exact += 1
            else:
                agg.errors[o.error_type] += 1
                fa.errors[o.error_type] += 1
                overall.errors[o.error_type] += 1

    return EvalReport(kind, samples, field_aggs, form_aggs, overall)


# --------------------------------------------------------------------------- #
# Xuất báo cáo
# --------------------------------------------------------------------------- #
def _pct(x: float) -> str:
    return f"{x * 100:.1f}%"


def to_markdown(report: EvalReport) -> str:
    o = report.overall
    lines = [
        f"# Đánh giá so ground-truth (đầu vào: {report.kind})",
        "",
        f"- Số mẫu: **{o.n_samples}** | Exact-match toàn form: **{_pct(o.form_exact_rate)}**",
        f"- Accuracy theo trường: **{_pct(o.field_accuracy)}** "
        f"({o.n_exact}/{o.n_fields}) | P/R/F1: "
        f"**{_pct(o.prf.precision)} / {_pct(o.prf.recall)} / {_pct(o.prf.f1)}**",
        f"- Lỗi: {dict(o.errors)}",
        "",
        "## Theo loại biểu mẫu",
        "",
        "| Form | #mẫu | Exact form | Acc trường | P | R | F1 | TG TB(ms) |",
        "|---|--:|--:|--:|--:|--:|--:|--:|",
    ]
    for ft, fa in sorted(report.form_aggs.items()):
        total_ms = sum(fa.avg_timing(k) for k in fa.timings)
        lines.append(
            f"| {ft} | {fa.n_samples} | {_pct(fa.form_exact_rate)} | {_pct(fa.field_accuracy)} | "
            f"{_pct(fa.prf.precision)} | {_pct(fa.prf.recall)} | {_pct(fa.prf.f1)} | {total_ms:.0f} |"
        )

    lines += ["", "## Theo trường", "", "| Trường | n | Acc | Sim TB | lỗi |", "|---|--:|--:|--:|---|"]
    for path, agg in sorted(report.field_aggs.items(), key=lambda kv: kv[1].accuracy):
        err = ", ".join(f"{k}:{v}" for k, v in agg.errors.items() if k) or "—"
        lines.append(f"| {path} | {agg.n} | {_pct(agg.accuracy)} | {_pct(agg.mean_sim)} | {err} |")

    failed = [s for s in report.samples if s.error]
    if failed:
        lines += ["", "## Mẫu lỗi pipeline", ""]
        lines += [f"- `{s.input_path}`: {s.error}" for s in failed]
    return "\n".join(lines) + "\n"


def to_csv(report: EvalReport) -> str:
    import csv
    import io

    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["field", "n", "exact", "accuracy", "mean_similarity",
                "precision", "recall", "f1", "missing", "extra", "ocr_error", "format_error"])
    for path, a in sorted(report.field_aggs.items()):
        w.writerow([path, a.n, a.exact, round(a.accuracy, 4), round(a.mean_sim, 4),
                    round(a.prf.precision, 4), round(a.prf.recall, 4), round(a.prf.f1, 4),
                    a.errors.get("missing", 0), a.errors.get("extra", 0),
                    a.errors.get("ocr_error", 0), a.errors.get("format_error", 0)])
    return buf.getvalue()


def write_reports(report: EvalReport, out_dir: str | Path = "outputs") -> dict[str, Path]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    md = out / f"eval_{report.kind}.md"
    csv_path = out / f"eval_{report.kind}.csv"
    md.write_text(to_markdown(report), encoding="utf-8")
    csv_path.write_text(to_csv(report), encoding="utf-8")
    return {"markdown": md, "csv": csv_path}
