"""Benchmark riêng cho rule engine bằng cách chèn lỗi nghiệp vụ nhân tạo."""

from __future__ import annotations

import copy
import json
from dataclasses import asdict, dataclass, field
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from .engine import ComplianceEngine, FieldResolver
from .models import CheckStatus, RuleDefinition
from .parsers import parse_date, parse_number


@dataclass
class MutationResult:
    form_type: str
    target_rule: str
    mutated_field: str
    expected: list[str]
    predicted: list[str]

    @property
    def detected(self) -> bool:
        return self.target_rule in self.predicted


@dataclass
class ComplianceEvalReport:
    cases: list[MutationResult] = field(default_factory=list)
    skipped_rules: list[str] = field(default_factory=list)
    baseline_violations: dict[str, list[str]] = field(default_factory=dict)

    @property
    def tp(self) -> int:
        return sum(len(set(c.expected) & set(c.predicted)) for c in self.cases)

    @property
    def fp(self) -> int:
        return sum(len(set(c.predicted) - set(c.expected)) for c in self.cases)

    @property
    def fn(self) -> int:
        return sum(len(set(c.expected) - set(c.predicted)) for c in self.cases)

    @property
    def precision(self) -> float:
        return self.tp / (self.tp + self.fp) if self.tp + self.fp else 0.0

    @property
    def recall(self) -> float:
        return self.tp / (self.tp + self.fn) if self.tp + self.fn else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if p + r else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "n_cases": len(self.cases), "tp": self.tp, "fp": self.fp, "fn": self.fn,
            "precision": self.precision, "recall": self.recall, "f1": self.f1,
            "baseline_violations": self.baseline_violations,
            "skipped_rules": self.skipped_rules,
            "cases": [{**asdict(c), "detected": c.detected} for c in self.cases],
        }


def evaluate_mutations(
    documents: list[dict[str, Any]], engine: ComplianceEngine | None = None
) -> ComplianceEvalReport:
    engine = engine or ComplianceEngine()
    output = ComplianceEvalReport()
    for document in documents:
        form_type = str(document.get("form_id") or document.get("form_type") or "")
        baseline = engine.check(document, form_type)
        baseline_bad = {
            c.rule_id for c in baseline.checks if c.status == CheckStatus.VIOLATION
        }
        if baseline_bad:
            output.baseline_violations[form_type] = sorted(baseline_bad)
        selectors, rules = engine.registry.load(form_type)
        for rule in rules:
            if rule.id in baseline_bad or rule.params.get("eval_mutation", True) is False:
                output.skipped_rules.append(rule.id)
                continue
            mutated = copy.deepcopy(document)
            resolver = FieldResolver(mutated["results"], selectors)
            field = _mutate(rule, resolver)
            if not field:
                output.skipped_rules.append(rule.id)
                continue
            checked = engine.check(mutated, form_type)
            after_bad = {
                c.rule_id for c in checked.checks if c.status == CheckStatus.VIOLATION
            }
            predicted = sorted(after_bad - baseline_bad)
            expected = [rule.id]
            output.cases.append(MutationResult(form_type, rule.id, field, expected, predicted))
    return output


def _mutate(rule: RuleDefinition, resolver: FieldResolver) -> str | None:
    p = rule.params
    if rule.operation == "equals_product":
        alias = str(p.get("mutation_alias") or p["actual"])
        number = parse_number(resolver.value(alias))
        return _set_number(resolver, alias, number * Decimal("1.25") if number else Decimal(1))
    if rule.operation == "sum_equals":
        alias = str(p["total"])
        number = parse_number(resolver.value(alias))
        delta = max(abs(number or Decimal(0)) * Decimal("0.25"), Decimal(1))
        return _set_number(resolver, alias, (number or Decimal(0)) + delta)
    if rule.operation == "less_or_equal":
        side = str(p.get("mutation_side", "right"))
        alias = str(p[side])
        other = parse_number(resolver.value(str(p["left" if side == "right" else "right"])))
        if other is None:
            return None
        value = other / Decimal(2) if side == "right" else other * Decimal(2) + 1
        return _set_number(resolver, alias, value)
    if rule.operation == "date_order":
        alias = str(p.get("mutation_alias") or p["later"])
        if alias == p["earlier"]:
            later = parse_date(resolver.value(str(p["later"])))
            return _set_value(resolver, alias, (later + timedelta(days=1)).isoformat()) if later else None
        earlier = parse_date(resolver.value(str(p["earlier"])))
        return _set_value(resolver, alias, (earlier - timedelta(days=1)).isoformat()) if earlier else None
    if rule.operation == "years_between":
        alias = str(p["end"])
        end = parse_date(resolver.value(alias))
        return _set_value(resolver, alias, (end + timedelta(days=370)).isoformat()) if end else None
    return None


def _set_number(resolver: FieldResolver, alias: str, value: Decimal) -> str | None:
    return _set_value(resolver, alias, format(value, "f"))


def _set_value(resolver: FieldResolver, alias: str, value: Any) -> str | None:
    key = resolver.key(alias)
    if key is None:
        return None
    resolver.results[key] = value
    return key


def load_documents(data_dir: str | Path) -> list[dict[str, Any]]:
    return [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(Path(data_dir).glob("expect_*.json"))
    ]


def to_markdown(report: ComplianceEvalReport) -> str:
    lines = [
        "# Đánh giá business-rule engine bằng lỗi nhân tạo", "",
        f"- Số ca chèn lỗi: **{len(report.cases)}**",
        f"- TP/FP/FN: **{report.tp}/{report.fp}/{report.fn}**",
        f"- Precision/Recall/F1: **{report.precision:.1%}/{report.recall:.1%}/{report.f1:.1%}**",
        "", "| Form | Luật mục tiêu | Phát hiện | Dự đoán mới |", "|---|---|---:|---|",
    ]
    for case in report.cases:
        lines.append(
            f"| {case.form_type} | `{case.target_rule}` | "
            f"{'✅' if case.detected else '❌'} | {', '.join(case.predicted) or '—'} |"
        )
    if report.baseline_violations:
        lines += ["", "## Vi phạm có sẵn trong JSON gốc (đã loại khỏi nhãn chèn lỗi)", ""]
        for form, rules in report.baseline_violations.items():
            lines.append(f"- `{form}`: {', '.join(rules)}")
    return "\n".join(lines) + "\n"
