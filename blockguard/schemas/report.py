from __future__ import annotations

from pydantic import BaseModel


class ReportOut(BaseModel):
    id: str
    audit_run_id: str
    content: str

    class Config:
        from_attributes = True
