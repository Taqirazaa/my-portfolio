from __future__ import annotations

from typing import Optional, Literal, List
from pydantic import BaseModel


Severity = Literal["low", "medium", "high", "critical"]
FindingType = Literal["rule_violation", "anomaly"]


class AuditRunOut(BaseModel):
    id: str
    status: str
    summary: Optional[str] = None

    class Config:
        from_attributes = True


class AuditFindingOut(BaseModel):
    id: str
    audit_run_id: str
    transaction_id: str
    finding_type: FindingType
    rule_name: Optional[str] = None
    severity: Severity = "low"
    score: Optional[float] = None
    details: Optional[dict] = None

    class Config:
        from_attributes = True


class AuditSummary(BaseModel):
    audit_run: AuditRunOut
    findings: List[AuditFindingOut]
