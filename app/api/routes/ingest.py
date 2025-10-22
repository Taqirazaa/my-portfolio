from __future__ import annotations

from typing import List
from fastapi import APIRouter, Depends

from blockguard.db.session import get_db_session
from blockguard.schemas.transaction import TransactionIn
from blockguard.services.orchestrator import AuditOrchestrator

router = APIRouter()


@router.post("/", summary="Ingest transactions")
async def ingest_transactions(txs: List[TransactionIn], session=Depends(get_db_session)) -> dict:
    orchestrator = AuditOrchestrator(session)
    await orchestrator.ingest_transactions(txs)
    return {"ingested": len(txs)}
