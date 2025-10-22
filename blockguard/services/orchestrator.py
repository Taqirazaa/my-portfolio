from __future__ import annotations

from typing import Sequence
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from blockguard.schemas.transaction import TransactionIn
from blockguard.schemas.audit import AuditFindingOut
from blockguard.agents.compliance_checker import ComplianceChecker
from blockguard.agents.anomaly_detector import AnomalyDetector
from blockguard.agents.risk_assessor import RiskAssessor
from blockguard.agents.report_generator import ReportGenerator
from blockguard.repositories.transactions import TransactionRepository
from blockguard.repositories.audits import AuditRepository
from blockguard.repositories.reports import ReportRepository
from blockguard.db.models import Transaction, AuditFinding


@dataclass
class AuditOrchestrator:
    session: AsyncSession

    def __post_init__(self) -> None:
        self.compliance_checker = ComplianceChecker()
        self.anomaly_detector = AnomalyDetector()
        self.risk_assessor = RiskAssessor()
        self.report_generator = ReportGenerator()
        self.tx_repo = TransactionRepository(self.session)
        self.audit_repo = AuditRepository(self.session)
        self.report_repo = ReportRepository(self.session)

    async def ingest_transactions(self, txs: Sequence[TransactionIn]) -> None:
        orm_txs = [
            Transaction(
                tx_id=tx.tx_id,
                chain=tx.chain,
                from_address=tx.from_address,
                to_address=tx.to_address,
                token_symbol=tx.token_symbol,
                amount=tx.amount,
                timestamp=tx.timestamp,
                tx_metadata=tx.metadata,
            )
            for tx in txs
        ]
        await self.tx_repo.upsert_transactions(orm_txs)

    async def run_audit(self, txs: Sequence[TransactionIn]) -> str:
        audit_run = await self.audit_repo.create_audit_run(status="running")

        findings: list[AuditFindingOut] = []
        # Agents
        for agent in [self.compliance_checker, self.anomaly_detector, self.risk_assessor]:
            findings.extend(await agent.run(txs))

        # Persist findings
        orm_findings = [
            AuditFinding(
                audit_run_id=audit_run.id,
                transaction_id=(await self.tx_repo.get_by_tx_id(f.transaction_id)).id if await self.tx_repo.get_by_tx_id(f.transaction_id) else None,  # type: ignore[arg-type]
                finding_type=f.finding_type,
                rule_name=f.rule_name,
                severity=f.severity,
                score=f.score,
                details=f.details,
            )
            for f in findings
            if f.transaction_id
        ]
        await self.audit_repo.add_findings(audit_run, orm_findings)

        await self.audit_repo.update_audit_run(audit_run, status="completed", summary=f"{len(orm_findings)} findings")

        # Report
        report_text = await self.report_generator.run(findings)
        report = await self.report_repo.create_report(audit_run_id=str(audit_run.id), content=report_text)
        return str(report.id)
