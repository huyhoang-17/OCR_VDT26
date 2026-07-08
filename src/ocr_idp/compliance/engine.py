"""Business-rule engine khai báo bằng YAML, chỉ dùng toán tử cho phép."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml

from .models import CheckStatus, ComplianceReport, RiskLevel, RuleDefinition, RuleResult
from .parsers import display_decimal, parse_date, parse_number


class FieldResolver:
    """Ánh xạ alias của luật tới key dài trong ``results`` bằng suffix duy nhất."""

    def __init__(self, results: dict[str, Any], selectors: dict[str, str]) -> None:
        self.results = results
        self.selectors = selectors

    def key(self, alias: str) -> str | None:
        selector = self.selectors.get(alias, alias)
        if selector in self.results:
            return selector
        matches = [key for key in self.results if key.endswith(selector)]
        return matches[0] if len(matches) == 1 else None

    def value(self, alias: str) -> Any:
        key = self.key(alias)
        return self.results.get(key) if key is not None else None


class RuleRegistry:
    def __init__(self, rules_dir: str | Path | None = None) -> None:
        self.rules_dir = Path(rules_dir) if rules_dir else Path(__file__).with_name("rules")

    def load(self, form_type: str) -> tuple[dict[str, str], list[RuleDefinition]]:
        path = self.rules_dir / f"{form_type}.yaml"
        if not path.exists():
            return {}, []
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        fields = {str(k): str(v) for k, v in (raw.get("fields") or {}).items()}
        rules = [
            RuleDefinition(
                id=str(item["id"]),
                form_type=form_type,
                title=str(item["title"]),
                severity=RiskLevel(item.get("severity", "error")),
                operation=str(item["operation"]),
                fields=fields,
                params={k: v for k, v in item.items() if k not in {
                    "id", "title", "severity", "operation", "message"
                }},
                message=str(item.get("message", "")),
            )
            for item in (raw.get("rules") or [])
        ]
        return fields, rules


class ComplianceEngine:
    """Đánh giá ràng buộc liên-trường; không sửa dữ liệu nguồn."""

    SUPPORTED_OPERATIONS = {
        "equals_product", "less_or_equal", "sum_equals", "date_order", "years_between"
    }

    def __init__(self, rules_dir: str | Path | None = None) -> None:
        self.registry = RuleRegistry(rules_dir)

    def check(self, document: dict[str, Any], form_type: str | None = None) -> ComplianceReport:
        detected = form_type or document.get("form_id") or document.get("form_type")
        if not detected:
            raise ValueError("JSON không có form_id/form_type để chọn bộ luật nghiệp vụ.")
        results = document.get("results")
        if not isinstance(results, dict):
            raise ValueError("JSON phải có object 'results' chứa dữ liệu đã trích xuất.")
        selectors, rules = self.registry.load(str(detected))
        resolver = FieldResolver(results, selectors)
        checks = [self._evaluate(rule, resolver) for rule in rules]
        report = ComplianceReport(form_type=str(detected), checks=checks)
        if not rules:
            report.warnings.append(f"Chưa khai báo bộ luật nghiệp vụ cho {detected}.")
        return report

    def _evaluate(self, rule: RuleDefinition, resolver: FieldResolver) -> RuleResult:
        if rule.operation not in self.SUPPORTED_OPERATIONS:
            return self._skipped(rule, {}, f"Toán tử không được hỗ trợ: {rule.operation}")
        aliases = self._aliases(rule)
        values = {alias: resolver.value(alias) for alias in aliases}
        keys = {alias: resolver.key(alias) or rule.fields.get(alias, alias) for alias in aliases}
        try:
            passed, actual, expected = self._calculate(rule, values)
        except (TypeError, ValueError, ArithmeticError) as exc:
            return self._skipped(rule, keys, f"Không đủ dữ liệu hợp lệ để kiểm tra: {exc}", values)
        status = CheckStatus.PASS if passed else CheckStatus.VIOLATION
        message = (
            f"Đạt: {rule.title}." if passed else (rule.message or f"Vi phạm: {rule.title}.")
        )
        return RuleResult(
            rule_id=rule.id, title=rule.title, severity=rule.severity, status=status,
            message=message, fields=keys, values=values, actual=actual, expected=expected,
        )

    @staticmethod
    def _aliases(rule: RuleDefinition) -> list[str]:
        p = rule.params
        if rule.operation == "equals_product":
            return [p["actual"], *p["factors"]]
        if rule.operation == "less_or_equal":
            return [p["left"], p["right"]]
        if rule.operation == "sum_equals":
            return [p["total"], *p["parts"]]
        if rule.operation == "date_order":
            return [p["earlier"], p["later"]]
        if rule.operation == "years_between":
            return [p["start"], p["end"], p["years"]]
        return []

    def _calculate(self, rule: RuleDefinition, values: dict[str, Any]) -> tuple[bool, Any, Any]:
        p = rule.params
        if rule.operation == "date_order":
            earlier, later = self._dates(values, p["earlier"], p["later"])
            return earlier <= later, later.isoformat(), f">= {earlier.isoformat()}"
        if rule.operation == "years_between":
            start, end = self._dates(values, p["start"], p["end"])
            years = self._number(values[p["years"]])
            anniversary = self._add_years(start, int(years))
            tolerance_days = int(p.get("tolerance_days", 1))
            delta = abs((end - anniversary).days)
            return delta <= tolerance_days, end.isoformat(), anniversary.isoformat()

        null_as_zero = bool(p.get("null_as_zero", False))
        nums = {
            alias: (Decimal(0) if value in (None, "") and null_as_zero else self._number(value))
            for alias, value in values.items()
        }
        if rule.operation == "equals_product":
            actual = nums[p["actual"]]
            expected = Decimal(1)
            for alias in p["factors"]:
                expected *= nums[alias]
            return self._close(actual, expected, p), display_decimal(actual), display_decimal(expected)
        if rule.operation == "less_or_equal":
            left, right = nums[p["left"]], nums[p["right"]]
            tolerance = Decimal(str(p.get("absolute_tolerance", 0)))
            return left <= right + tolerance, display_decimal(left), f"<= {display_decimal(right)}"
        if rule.operation == "sum_equals":
            actual = nums[p["total"]]
            expected = sum((nums[a] for a in p["parts"]), Decimal(0))
            return self._close(actual, expected, p), display_decimal(actual), display_decimal(expected)
        raise ValueError(rule.operation)

    @staticmethod
    def _number(value: Any) -> Decimal:
        parsed = parse_number(value)
        if parsed is None:
            raise ValueError(f"không đọc được số từ {value!r}")
        return parsed

    @staticmethod
    def _dates(values: dict[str, Any], *aliases: str) -> list[date]:
        parsed = [parse_date(values[a]) for a in aliases]
        if any(v is None for v in parsed):
            raise ValueError("thiếu hoặc sai định dạng ngày")
        return parsed  # type: ignore[return-value]

    @staticmethod
    def _close(actual: Decimal, expected: Decimal, params: dict[str, Any]) -> bool:
        absolute = Decimal(str(params.get("absolute_tolerance", 0)))
        relative = Decimal(str(params.get("relative_tolerance", "0.01")))
        allowed = max(absolute, abs(expected) * relative)
        return abs(actual - expected) <= allowed

    @staticmethod
    def _add_years(value: date, years: int) -> date:
        try:
            return value.replace(year=value.year + years)
        except ValueError:  # 29/02 -> 28/02
            return value.replace(month=2, day=28, year=value.year + years)

    @staticmethod
    def _skipped(
        rule: RuleDefinition,
        fields: dict[str, str],
        message: str,
        values: dict[str, Any] | None = None,
    ) -> RuleResult:
        return RuleResult(
            rule_id=rule.id, title=rule.title, severity=rule.severity,
            status=CheckStatus.SKIPPED, message=message, fields=fields, values=values or {},
        )
