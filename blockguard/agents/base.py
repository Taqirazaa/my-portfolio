from __future__ import annotations

from typing import Protocol, Sequence

from blockguard.schemas.transaction import TransactionIn
from blockguard.schemas.audit import AuditFindingOut, Severity


class Agent(Protocol):
    name: str

    async def run(self, transactions: Sequence[TransactionIn]) -> list[AuditFindingOut]: ...
