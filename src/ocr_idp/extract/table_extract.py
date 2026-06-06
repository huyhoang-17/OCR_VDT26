"""Trích xuất BẢNG -> mảng object (vd danh sách cổ đông của Form C).

Cách làm (chạy được cho cả text-layer lẫn ảnh scan vì chỉ dùng dòng + bbox):
  1. Định vị TIÊU ĐỀ từng cột bằng fuzzy theo từ khóa header -> lấy tâm-x mỗi cột.
  2. Cắt vùng dữ liệu: các dòng nằm DƯỚI hàng tiêu đề và TRƯỚC dòng "tổng cộng"
     (stop_keywords).
  3. Gom dòng dữ liệu thành HÀNG theo chồng lấn dọc.
  4. Trong mỗi hàng, gán mỗi ô vào cột có tâm-x gần nhất -> ghép text cùng cột.
  5. Chuẩn hóa từng cột (int/percent/id_number/string...) -> 1 dict / hàng.

Cấu hình (extraction.yaml, dưới `options`):
  columns:   [{field, header:[...], normalizer}]   # thứ tự = thứ tự cột
  key_field: full_name        # bỏ hàng nếu cột này rỗng (lọc dòng rác)
  stop_keywords: ["Tổng cộng"]  # dừng bảng khi gặp (footer)
"""

from __future__ import annotations

from typing import Any, Optional

from ..config import AppConfig
from ..normalize.apply import NORMALIZERS
from ..normalize.text import clean_spaces, norm_key
from ..types import BBox, FieldStatus, FieldValue, Line
from .base import ExtractionContext, FieldExtractor, FieldSpec, vertical_overlap_ratio


class TableExtractor(FieldExtractor):
    strategy = "table"

    def __init__(self, config: AppConfig) -> None:
        self.threshold = config.extraction.anchor.fuzzy_threshold

    def extract(self, spec: FieldSpec, ctx: ExtractionContext) -> FieldValue:
        opts = spec.options or {}
        columns = opts.get("columns") or []
        if not columns:
            return FieldValue(name=spec.name, value=[], status=FieldStatus.MISSING,
                              source="table", warnings=["table thiếu 'columns'"])

        headers = self._locate_headers(columns, ctx.lines)
        if len(headers) < 2:
            return FieldValue(name=spec.name, value=[], status=FieldStatus.MISSING,
                              source="table", warnings=["không định vị được tiêu đề bảng"])

        header_bottom = max(h["line"].bbox.y2 for h in headers)
        x_lo = min(h["line"].bbox.x1 for h in headers)
        x_hi = max(h["line"].bbox.x2 for h in headers)
        stop_y = self._stop_y(ctx.lines, opts.get("stop_keywords") or [], header_bottom)

        margin = 0.5 * (x_hi - x_lo) / max(len(headers), 1)
        data = [
            ln for ln in ctx.lines
            if ln.bbox.cy > header_bottom
            and (stop_y is None or ln.bbox.cy < stop_y)
            and (x_lo - margin) <= ln.bbox.cx <= (x_hi + margin)
        ]
        rows = _cluster_rows(data)

        key_field = opts.get("key_field")
        records: list[dict[str, Any]] = []
        confidences: list[float] = []
        for row in rows:
            rec, conf = self._row_to_record(row, headers)
            if not rec:
                continue
            if key_field and not rec.get(key_field):
                continue  # bỏ hàng rác (thiếu trường khóa)
            if not any(v not in (None, "") for v in rec.values()):
                continue
            records.append(rec)
            confidences.append(conf)

        if not records:
            return FieldValue(name=spec.name, value=[], status=FieldStatus.MISSING,
                              source="table", warnings=["không đọc được dòng dữ liệu nào"])
        conf = min(confidences) if confidences else 0.6
        return FieldValue(name=spec.name, value=records, raw_value=f"{len(records)} dòng",
                          confidence=conf, source="table", status=FieldStatus.OK)

    # -- Định vị tiêu đề ---------------------------------------------------- #
    def _locate_headers(self, columns: list[dict], lines: list[Line]) -> list[dict]:
        from rapidfuzz import fuzz

        used: set[int] = set()
        found: list[dict] = []
        for col in columns:
            labels = col.get("header") or [col["field"]]
            keys = [norm_key(la) for la in labels]
            best_line, best_score, best_i = None, -1.0, -1
            for i, ln in enumerate(lines):
                if i in used:
                    continue
                k = norm_key(ln.text)
                if not k:
                    continue
                score = max(fuzz.ratio(key, k) for key in keys)
                if score > best_score:
                    best_score, best_line, best_i = score, ln, i
            if best_line is not None and best_score >= self.threshold:
                used.add(best_i)
                found.append({"col": col, "line": best_line, "cx": best_line.bbox.cx})
        found.sort(key=lambda h: h["cx"])
        return found

    @staticmethod
    def _stop_y(lines: list[Line], stop_keywords: list[str], header_bottom: float) -> Optional[float]:
        if not stop_keywords:
            return None
        keys = [norm_key(s) for s in stop_keywords]
        cands = []
        for ln in lines:
            if ln.bbox.cy <= header_bottom:
                continue
            k = norm_key(ln.text)
            if any(key and key in k for key in keys):
                cands.append(ln.bbox.cy)
        return min(cands) if cands else None

    # -- Gán ô -> cột trong 1 hàng ------------------------------------------ #
    def _row_to_record(self, row: list[Line], headers: list[dict]) -> tuple[dict[str, Any], float]:
        buckets: dict[int, list[Line]] = {}
        for ln in row:
            j = min(range(len(headers)), key=lambda k: abs(ln.bbox.cx - headers[k]["cx"]))
            buckets.setdefault(j, []).append(ln)

        rec: dict[str, Any] = {}
        for j, h in enumerate(headers):
            col = h["col"]
            cells = sorted(buckets.get(j, []), key=lambda ln: ln.bbox.x1)
            raw = clean_spaces(" ".join(c.text for c in cells))
            rec[col["field"]] = self._norm_cell(raw, col.get("normalizer"))
        conf = min((ln.confidence for ln in row), default=0.6)
        return rec, conf

    @staticmethod
    def _norm_cell(raw: str, normalizer: Optional[str]) -> Any:
        if raw == "":
            return None
        if normalizer and normalizer in NORMALIZERS:
            value, _warns = NORMALIZERS[normalizer](raw)
            return value
        return raw


def _cluster_rows(lines: list[Line], min_overlap: float = 0.3) -> list[list[Line]]:
    """Gom các dòng thành hàng theo chồng lấn dọc (đã sắp theo y)."""
    rows: list[list[Line]] = []
    cur: list[Line] = []
    cur_box: Optional[BBox] = None
    for ln in sorted(lines, key=lambda l: l.bbox.y1):
        if cur and cur_box is not None and vertical_overlap_ratio(ln.bbox, cur_box) >= min_overlap:
            cur.append(ln)
            cur_box = BBox(min(cur_box.x1, ln.bbox.x1), min(cur_box.y1, ln.bbox.y1),
                           max(cur_box.x2, ln.bbox.x2), max(cur_box.y2, ln.bbox.y2))
        else:
            if cur:
                rows.append(cur)
            cur = [ln]
            cur_box = ln.bbox
    if cur:
        rows.append(cur)
    return rows
