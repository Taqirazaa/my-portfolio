from __future__ import annotations

from typing import Sequence
from dataclasses import dataclass

from blockguard.schemas.transaction import TransactionIn
from blockguard.schemas.audit import AuditFindingOut


@dataclass
class RiskAssessor:
    name: str = "RiskAssessor"

    async def run(self, transactions: Sequence[TransactionIn]) -> list[AuditFindingOut]:
        findings: list[AuditFindingOut] = []
        # Placeholder heuristic risk scoring: high amount + unknown token
        for tx in transactions:
            score = 0.0
            if float(tx.amount) > 500_000:
                score += 0.6
            if not tx.token_symbol:
                score += 0.3
            if score >= 0.7:
                findings.append(
                    AuditFindingOut(
                        id="",
                        audit_run_id="",
                        transaction_id=tx.tx_id,
                        finding_type="anomaly",
                        rule_name="risk_assessment",
                        severity="high" if score > 0.85 else "medium",
                        score=score,
                        details={"heuristics": True},
                    )
                )
        return findings
