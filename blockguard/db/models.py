from __future__ import annotations

import uuid
from typing import Optional
from datetime import datetime

from sqlalchemy import String, Text, ForeignKey, JSON, Index, Numeric, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from .base import Base, UUIDMixin, TimestampedMixin


class Transaction(Base, UUIDMixin):
    __tablename__ = "transactions"

    tx_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    chain: Mapped[str] = mapped_column(String(32), index=True)
    from_address: Mapped[str] = mapped_column(String(128), index=True)
    to_address: Mapped[Optional[str]] = mapped_column(String(128), index=True, nullable=True)
    token_symbol: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    amount: Mapped[float] = mapped_column(Numeric(36, 18))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    findings: Mapped[list[AuditFinding]] = relationship("AuditFinding", back_populates="transaction")


Index("ix_transactions_from_to_time", Transaction.from_address, Transaction.to_address, Transaction.timestamp)


class AuditRun(Base, UUIDMixin, TimestampedMixin):
    __tablename__ = "audit_runs"

    status: Mapped[str] = mapped_column(String(32), default="completed")
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    findings: Mapped[list[AuditFinding]] = relationship("AuditFinding", back_populates="audit_run")
    report: Mapped[Optional[Report]] = relationship("Report", back_populates="audit_run", uselist=False)


class AuditFinding(Base, UUIDMixin, TimestampedMixin):
    __tablename__ = "audit_findings"

    audit_run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("audit_runs.id"), index=True)
    transaction_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("transactions.id"), index=True)

    finding_type: Mapped[str] = mapped_column(String(32))  # rule_violation | anomaly
    rule_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    severity: Mapped[str] = mapped_column(String(16), default="low")
    score: Mapped[Optional[float]] = mapped_column(Numeric(10, 6), nullable=True)
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    audit_run: Mapped[AuditRun] = relationship("AuditRun", back_populates="findings")
    transaction: Mapped[Transaction] = relationship("Transaction", back_populates="findings")


class Report(Base, UUIDMixin, TimestampedMixin):
    __tablename__ = "reports"

    audit_run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("audit_runs.id"), index=True, unique=True)
    content: Mapped[str] = mapped_column(Text)

    audit_run: Mapped[AuditRun] = relationship("AuditRun", back_populates="report")
