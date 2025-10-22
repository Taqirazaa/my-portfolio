from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from blockguard.db.models import Report


class ReportRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_report(self, audit_run_id: str, content: str) -> Report:
        report = Report(audit_run_id=audit_run_id, content=content)
        self.session.add(report)
        await self.session.commit()
        await self.session.refresh(report)
        return report

    async def get_by_audit(self, audit_run_id: str) -> Report | None:
        stmt = select(Report).where(Report.audit_run_id == audit_run_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
