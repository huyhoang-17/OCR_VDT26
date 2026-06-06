"""So khớp JSON dự đoán với ground-truth -> kết quả theo TỪNG TRƯỜNG.

Hỗ trợ 3 loại trường:
  * scalar  — chuỗi/số/bool/null (so exact + fuzzy).
  * set     — mảng giá trị vô hướng (checkbox: account_types/services) -> so theo TẬP.
  * table   — mảng object (danh sách cổ đông) -> so từng hàng/ô (ghép hàng tham lam).

Mỗi trường cho ra: khớp tuyệt đối? độ tương đồng (0..1), có/thiếu ở gt/pred, và
PHÂN LOẠI LỖI: missing | extra | ocr_error (gần đúng/mất dấu) | format_error.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from ..normalize.text import strip_accents

# Bỏ qua khi so khớp (siêu dữ liệu / hằng số)
_SKIP_KEYS = {"_meta", "form_type"}

OCR_SIMILARITY_THRESHOLD = 85.0  # ratio >= -> coi là lỗi OCR (gần đúng), dưới -> sai định dạng


@dataclass
class FieldOutcome:
    path: str
    kind: str                 # scalar | set | table
    gt_present: bool
    pred_present: bool
    exact: bool
    similarity: float         # 0..1
    error_type: Optional[str]  # None nếu khớp; missing|extra|ocr_error|format_error


# --------------------------------------------------------------------------- #
# Thu thập trường (đệ quy) -> dict[path] = (kind, value)
# --------------------------------------------------------------------------- #
def collect_fields(obj: Any, prefix: str = "") -> dict[str, tuple[str, Any]]:
    out: dict[str, tuple[str, Any]] = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            if prefix == "" and k in _SKIP_KEYS:
                continue
            path = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                out.update(collect_fields(v, path))
            elif isinstance(v, list):
                out[path] = (("table" if _is_list_of_dicts(v) else "set"), v)
            else:
                out[path] = ("scalar", v)
    return out


def _is_list_of_dicts(v: list) -> bool:
    return len(v) > 0 and all(isinstance(x, dict) for x in v)


# --------------------------------------------------------------------------- #
# So khớp giá trị
# --------------------------------------------------------------------------- #
def _is_empty(v: Any) -> bool:
    return v is None or v == "" or v == [] or v == {}


def _canon(v: Any) -> str:
    return strip_accents(str(v)).lower().strip()


def _ratio(a: Any, b: Any) -> float:
    from rapidfuzz import fuzz

    return float(fuzz.ratio(_canon(a), _canon(b)))


def _scalar_equal(pred: Any, gt: Any) -> bool:
    if _is_empty(pred) and _is_empty(gt):
        return True
    if isinstance(pred, bool) or isinstance(gt, bool):
        return bool(pred) == bool(gt)
    if isinstance(pred, (int, float)) and isinstance(gt, (int, float)):
        return abs(float(pred) - float(gt)) < 1e-6
    return str(pred).strip() == str(gt).strip()


def _classify(pred: Any, gt: Any, exact: bool, sim: float) -> Optional[str]:
    if exact:
        return None
    if _is_empty(gt) and not _is_empty(pred):
        return "extra"
    if _is_empty(pred) and not _is_empty(gt):
        return "missing"
    return "ocr_error" if sim * 100.0 >= OCR_SIMILARITY_THRESHOLD else "format_error"


def compare_scalar(path: str, pred: Any, gt: Any) -> FieldOutcome:
    exact = _scalar_equal(pred, gt)
    sim = 1.0 if exact else (_ratio(pred, gt) / 100.0 if not (_is_empty(pred) or _is_empty(gt)) else 0.0)
    return FieldOutcome(path, "scalar", not _is_empty(gt), not _is_empty(pred), exact, sim,
                        _classify(pred, gt, exact, sim))


def compare_set(path: str, pred: Any, gt: Any) -> FieldOutcome:
    ps = {_canon(x) for x in (pred or [])}
    gs = {_canon(x) for x in (gt or [])}
    exact = ps == gs
    inter = len(ps & gs)
    union = len(ps | gs) or 1
    sim = inter / union
    return FieldOutcome(path, "set", not _is_empty(gt), not _is_empty(pred), exact, sim,
                        _classify(pred, gt, exact, sim))


def compare_table(path: str, pred: Any, gt: Any) -> FieldOutcome:
    pred_rows = list(pred or [])
    gt_rows = list(gt or [])
    if not gt_rows:
        exact = len(pred_rows) == 0
        return FieldOutcome(path, "table", False, len(pred_rows) > 0, exact,
                            1.0 if exact else 0.0, None if exact else "extra")

    keys: list[str] = []
    for r in gt_rows:
        for k in r:
            if k not in keys:
                keys.append(k)

    used: set[int] = set()
    matched_cells = 0
    total_cells = len(gt_rows) * len(keys)
    for grow in gt_rows:
        best_i, best_hits = -1, -1
        for i, prow in enumerate(pred_rows):
            if i in used:
                continue
            hits = sum(1 for k in keys if _scalar_equal(prow.get(k), grow.get(k)))
            if hits > best_hits:
                best_hits, best_i = hits, i
        if best_i >= 0:
            used.add(best_i)
            matched_cells += best_hits

    sim = matched_cells / total_cells if total_cells else 0.0
    exact = (len(pred_rows) == len(gt_rows)) and matched_cells == total_cells
    return FieldOutcome(path, "table", True, len(pred_rows) > 0, exact, sim,
                        None if exact else ("ocr_error" if sim >= 0.6 else "format_error"))


def compare_documents(pred: dict, gt: dict) -> list[FieldOutcome]:
    """So khớp toàn bộ tài liệu theo từng trường (lấy schema từ ground-truth)."""
    gt_fields = collect_fields(gt)
    pred_fields = collect_fields(pred)
    outcomes: list[FieldOutcome] = []
    for path, (kind, gval) in gt_fields.items():
        pval = pred_fields.get(path, (kind, None))[1]
        if kind == "set":
            outcomes.append(compare_set(path, pval, gval))
        elif kind == "table":
            outcomes.append(compare_table(path, pval, gval))
        else:
            outcomes.append(compare_scalar(path, pval, gval))
    return outcomes
