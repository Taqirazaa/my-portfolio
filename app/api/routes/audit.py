from __future__ import annotations

from typing import List
from fastapi import APIRouter, Depends

from blockguard.db.session import get_db_session
from blockguard.schemas.transaction import TransactionIn
from blockguard.services.orchestrator import AuditOrchestrator

router = APIRouter()


@router.post("/", summary="Run audit for provided transactions")
async def run_audit(txs: List[TransactionIn], session=Depends(get_db_session)) -> dict:
    orchestrator = AuditOrchestrator(session)
    report_id = await orchestrator.run_audit(txs)
    return {"report_id": report_id}
