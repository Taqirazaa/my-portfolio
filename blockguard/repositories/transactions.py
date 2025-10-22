from __future__ import annotations

from typing import Iterable, Sequence
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from blockguard.db.models import Transaction


class TransactionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert_transactions(self, transactions: Iterable[Transaction]) -> None:
        for tx in transactions:
            self.session.add(tx)
        await self.session.commit()

    async def create(self, tx: Transaction) -> Transaction:
        self.session.add(tx)
        await self.session.commit()
        await self.session.refresh(tx)
        return tx

    async def list_recent(self, limit: int = 1000) -> Sequence[Transaction]:
        stmt = select(Transaction).order_by(Transaction.timestamp.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_between(self, start: datetime, end: datetime) -> Sequence[Transaction]:
        stmt = select(Transaction).where(Transaction.timestamp.between(start, end)).order_by(Transaction.timestamp.asc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_tx_id(self, tx_id: str) -> Transaction | None:
        stmt = select(Transaction).where(Transaction.tx_id == tx_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
