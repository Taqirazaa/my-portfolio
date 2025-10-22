from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from blockguard.db.session import get_db_session
from blockguard.repositories.reports import ReportRepository
from sqlalchemy import select
from blockguard.db.models import Report

router = APIRouter()


@router.get("/{report_id}", summary="Get audit report by ID")
async def get_report(report_id: str, session=Depends(get_db_session)) -> dict:
    # Fetch by report primary key
    result = await session.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"id": str(report.id), "audit_run_id": str(report.audit_run_id), "content": report.content}
