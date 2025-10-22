from __future__ import annotations

from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from blockguard.db.models import AuditRun, AuditFinding


class AuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_audit_run(self, status: str = "running", summary: str | None = None) -> AuditRun:
        run = AuditRun(status=status, summary=summary)
        self.session.add(run)
        await self.session.commit()
        await self.session.refresh(run)
        return run

    async def update_audit_run(self, run: AuditRun, *, status: str | None = None, summary: str | None = None) -> AuditRun:
        if status is not None:
            run.status = status
        if summary is not None:
            run.summary = summary
        await self.session.commit()
        await self.session.refresh(run)
        return run

    async def add_findings(self, run: AuditRun, findings: list[AuditFinding]) -> None:
        for f in findings:
            f.audit_run_id = run.id
            self.session.add(f)
        await self.session.commit()

    async def list_findings(self, run_id: str) -> Sequence[AuditFinding]:
        stmt = select(AuditFinding).where(AuditFinding.audit_run_id == run_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_run(self, run_id: str) -> AuditRun | None:
        stmt = select(AuditRun).where(AuditRun.id == run_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
