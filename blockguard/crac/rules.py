from __future__ import annotations

from dataclasses import dataclass

from blockguard.crac.base import Rule, RuleResult
from blockguard.schemas.transaction import TransactionIn
from blockguard.schemas.audit import Severity


@dataclass
class MaxTransferAmountRule:
    name: str = "MaxTransferAmount"
    severity: Severity = "high"
    max_amount: float = 1_000_000.0

    async def evaluate(self, tx: TransactionIn) -> RuleResult:
        passed = float(tx.amount) <= self.max_amount
        details = None if passed else {"amount": tx.amount, "max": self.max_amount}
        return RuleResult(rule_name=self.name, passed=passed, severity=self.severity, details=details)


@dataclass
class BlacklistedAddressRule:
    name: str = "BlacklistedAddress"
    severity: Severity = "critical"
    blacklist: set[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.blacklist is None:
            self.blacklist = set()

    async def evaluate(self, tx: TransactionIn) -> RuleResult:
        is_blacklisted = tx.from_address in self.blacklist or (tx.to_address is not None and tx.to_address in self.blacklist)
        passed = not is_blacklisted
        details = None if passed else {"from": tx.from_address, "to": tx.to_address}
        return RuleResult(rule_name=self.name, passed=passed, severity=self.severity, details=details)
