from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class TransactionIn(BaseModel):
    tx_id: str = Field(..., max_length=128)
    chain: str = Field(..., max_length=32)
    from_address: str = Field(..., max_length=128)
    to_address: Optional[str] = Field(None, max_length=128)
    token_symbol: Optional[str] = Field(None, max_length=32)
    amount: float
    timestamp: datetime
    metadata: Optional[dict] = None


class TransactionOut(TransactionIn):
    id: str

    class Config:
        from_attributes = True
