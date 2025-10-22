from __future__ import annotations

from typing import Sequence
from dataclasses import dataclass

from blockguard.schemas.transaction import TransactionIn
from blockguard.schemas.audit import AuditFindingOut
from blockguard.crac.base import RuleEngine
from blockguard.crac.rules import MaxTransferAmountRule, BlacklistedAddressRule


@dataclass
class ComplianceChecker:
    name: str = "ComplianceChecker"

    def __init__(self, blacklist: set[str] | None = None) -> None:
        self.engine = RuleEngine(
            [
                MaxTransferAmountRule(),
                BlacklistedAddressRule(blacklist=blacklist or set()),
            ]
        )

    async def run(self, transactions: Sequence[TransactionIn]) -> list[AuditFindingOut]:
        findings: list[AuditFindingOut] = []
        for tx in transactions:
            results = await self.engine.run(tx)
            for res in results:
                if not res.passed:
                    findings.append(
                        AuditFindingOut(
                            id="",  # to be set when persisted
                            audit_run_id="",
                            transaction_id=tx.tx_id,
                            finding_type="rule_violation",
                            rule_name=res.rule_name,
                            severity=res.severity,
                            score=None,
                            details=res.details,
                        )
                    )
        return findings
