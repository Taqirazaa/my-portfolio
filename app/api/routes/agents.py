from __future__ import annotations

from typing import List, Literal, Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel

from blockguard.schemas.transaction import TransactionIn
from blockguard.schemas.audit import Severity, FindingType, AuditFindingOut

router = APIRouter()


class FindingInput(BaseModel):
    transaction_id: str
    finding_type: FindingType
    rule_name: Optional[str] = None
    severity: Severity = "low"
    score: Optional[float] = None
    details: Optional[dict] = None


@router.post("/compliance", summary="Run ComplianceChecker on transactions")
async def run_compliance_checker(txs: List[TransactionIn], request: Request) -> dict:
    agent = request.app.state.agents["compliance"]
    results: list[AuditFindingOut] = await agent.run(txs)
    payload = [
        {k: v for k, v in f.model_dump().items() if k not in ("id", "audit_run_id")}
        for f in results
    ]
    return {"count": len(payload), "findings": payload}


@router.post("/anomaly", summary="Run AnomalyDetector on transactions")
async def run_anomaly_detector(txs: List[TransactionIn], request: Request) -> dict:
    agent = request.app.state.agents["anomaly"]
    results: list[AuditFindingOut] = await agent.run(txs)
    payload = [
        {k: v for k, v in f.model_dump().items() if k not in ("id", "audit_run_id")}
        for f in results
    ]
    return {"count": len(payload), "findings": payload}


@router.post("/risk", summary="Run RiskAssessor on transactions")
async def run_risk_assessor(txs: List[TransactionIn], request: Request) -> dict:
    agent = request.app.state.agents["risk"]
    results: list[AuditFindingOut] = await agent.run(txs)
    payload = [
        {k: v for k, v in f.model_dump().items() if k not in ("id", "audit_run_id")}
        for f in results
    ]
    return {"count": len(payload), "findings": payload}


@router.post("/report", summary="Generate report text from findings")
async def run_report_generator(findings: List[FindingInput], request: Request) -> dict:
    agent = request.app.state.agents["report"]
    # Cast input to AuditFindingOut with placeholders for ids
    casted = [
        AuditFindingOut(
            id="",
            audit_run_id="",
            transaction_id=f.transaction_id,
            finding_type=f.finding_type,
            rule_name=f.rule_name,
            severity=f.severity,
            score=f.score,
            details=f.details,
        )
        for f in findings
    ]
    content = await agent.run(casted)
    return {"content": content}
