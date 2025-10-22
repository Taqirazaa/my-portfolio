from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Iterable

from blockguard.schemas.transaction import TransactionIn
from blockguard.schemas.audit import Severity


@dataclass
class RuleResult:
    rule_name: str
    passed: bool
    severity: Severity
    details: dict | None = None


class Rule(Protocol):
    name: str
    severity: Severity

    async def evaluate(self, tx: TransactionIn) -> RuleResult: ...


class RuleEngine:
    def __init__(self, rules: Iterable[Rule]):
        self.rules = list(rules)

    async def run(self, tx: TransactionIn) -> list[RuleResult]:
        results: list[RuleResult] = []
        for rule in self.rules:
            result = await rule.evaluate(tx)
            results.append(result)
        return results
