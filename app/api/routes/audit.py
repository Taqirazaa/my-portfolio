from __future__ import annotations

from typing import List
from fastapi import APIRouter, Depends

from blockguard.db.session import get_db_session
from blockguard.schemas.transaction import TransactionIn
from blockguard.services.orchestrator import AuditOrchestrator
from blockguard.agents.simple_compliance_checker import ComplianceChecker as SimpleComplianceChecker
from blockguard.services.audit_processor import AuditProcessor

router = APIRouter()


@router.post("/", summary="Run audit for provided transactions")
async def run_audit(txs: List[TransactionIn], session=Depends(get_db_session)) -> dict:
    orchestrator = AuditOrchestrator(session)
    report_id = await orchestrator.run_audit(txs)
    return {"report_id": report_id}


@router.post("/compliance", summary="Validate a transaction via rule-based ComplianceChecker")
async def validate_compliance(tx: dict) -> dict:
    checker = SimpleComplianceChecker()
    return checker.validate(tx)


@router.post("/process", summary="Run the full audit pipeline for provided transactions")
async def process_audit(txs: List[dict]) -> dict:
    processor = AuditProcessor.default()
    return processor.process(txs)
