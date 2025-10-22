from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Deque, List, Optional
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone


def _parse_timestamp(value: datetime | str | int | float) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, (int, float)):
        # Assume seconds since epoch
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    if isinstance(value, str):
        s = value.strip()
        # Handle trailing Z as UTC
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(s)
        except ValueError:
            # Fallback: try parsing as seconds
            dt = datetime.fromtimestamp(float(s), tz=timezone.utc)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    raise TypeError("Unsupported timestamp type")


@dataclass
class ComplianceChecker:
    """Rule-based validator for a single blockchain transaction dict.

    Rules:
    - Blacklist check: either address in blacklist => violation "blacklisted_address".
    - AML threshold: amount >= aml_threshold => violation "aml_threshold_exceeded".
    - Frequency: more than max_txs_in_window from same sender within window => violation "frequency_limit_exceeded".

    Expected tx dict keys (flexible):
    - tx_hash (preferred) or tx_id
    - from_address or from
    - to_address or to
    - amount (numeric as str/float/int)
    - timestamp (ISO8601 string, epoch seconds, or datetime)
    """

    blacklist: set[str] = field(default_factory=set)
    aml_threshold: float = 10_000.0
    frequency_window_seconds: int = 3600
    max_txs_in_window: int = 10

    # Internal per-sender history of timestamps to evaluate frequency rule
    _history: Dict[str, Deque[datetime]] = field(default_factory=lambda: defaultdict(deque), init=False, repr=False)

    def validate(self, tx: dict) -> dict:
        """Validate a single transaction dict and return compliance result.

        Returns: {"tx_hash": str, "compliant": bool, "violations": list[str]}
        """
        tx_hash = str(tx.get("tx_hash") or tx.get("tx_id") or "")
        from_addr = (tx.get("from_address") or tx.get("from") or "").lower()
        to_addr = (tx.get("to_address") or tx.get("to") or "").lower()

        try:
            amount = float(tx.get("amount", 0.0))
        except (TypeError, ValueError):
            amount = 0.0

        timestamp_raw = tx.get("timestamp") or tx.get("time")
        timestamp = _parse_timestamp(timestamp_raw) if timestamp_raw is not None else datetime.now(tz=timezone.utc)

        violations: List[str] = []

        # 1) Blacklist check
        if from_addr in self.blacklist or (to_addr and to_addr in self.blacklist):
            violations.append("blacklisted_address")

        # 2) AML threshold
        if amount >= self.aml_threshold:
            violations.append("aml_threshold_exceeded")

        # 3) Frequency rule (per sender)
        if from_addr:
            window = timedelta(seconds=self.frequency_window_seconds)
            dq = self._history[from_addr]
            # Drop old entries
            while dq and (timestamp - dq[0]) > window:
                dq.popleft()
            # Check current count before adding this tx
            if len(dq) >= self.max_txs_in_window:
                violations.append("frequency_limit_exceeded")
            # Record this tx
            dq.append(timestamp)

        return {
            "tx_hash": tx_hash,
            "compliant": len(violations) == 0,
            "violations": violations,
        }
