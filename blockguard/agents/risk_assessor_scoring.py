from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, Deque, List, Sequence
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

import numpy as np
from sklearn.exceptions import NotFittedError

from blockguard.agents.simple_compliance_checker import ComplianceChecker
from blockguard.agents.anomaly_detector import AnomalyDetector


def _epoch_seconds(value: float | int | str | datetime | None) -> float:
    if value is None:
        return float(datetime.now(tz=timezone.utc).timestamp())
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, datetime):
        return float(value.replace(tzinfo=value.tzinfo or timezone.utc).timestamp())
    s = str(value).strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
        return float(dt.replace(tzinfo=dt.tzinfo or timezone.utc).timestamp())
    except ValueError:
        return float(s)


def _bucket(addr: str) -> float:
    if not addr:
        return 0.0
    return (abs(hash(addr)) % 100) / 100.0


def featurize(tx: dict) -> List[float]:
    amount = float(tx.get("amount", 0.0))
    log_amount = math.log10(max(amount, 0.0) + 1.0)

    token = str(tx.get("token_symbol", "")).upper()
    token_vec = [1.0 if token == k else 0.0 for k in ("USDC", "USDT", "ETH")]

    from_b = _bucket(str(tx.get("from_address") or tx.get("from") or ""))
    to_b = _bucket(str(tx.get("to_address") or tx.get("to") or ""))

    ts = _epoch_seconds(tx.get("timestamp"))
    hour_norm = (int((ts // 3600) % 24)) / 23.0 if 23.0 else 0.0

    return [log_amount, *token_vec, from_b, to_b, hour_norm]


@dataclass
class RiskAssessor:
    """Combine ComplianceChecker and AnomalyDetector into a 0..100 risk score.

    risk = 100 * (0.6 * compliance + 0.3 * anomaly + 0.1 * history)

    - compliance: 1.0 if any violation else 0.0
    - anomaly: normalized anomaly score (0..1) from IsolationForest
    - history: frequency-based (0..1) using a rolling window per sender
    """

    compliance_checker: ComplianceChecker = field(default_factory=ComplianceChecker)
    anomaly_detector: AnomalyDetector = field(default_factory=AnomalyDetector)
    frequency_window_seconds: int = 3600
    max_txs_in_window: int = 10
    anomaly_scale: float = 3.0  # larger => slower saturation

    _history: Dict[str, Deque[datetime]] = field(default_factory=lambda: defaultdict(deque), init=False, repr=False)

    def _history_component(self, from_addr: str, ts: float) -> float:
        if not from_addr:
            return 0.0
        now_dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        window = timedelta(seconds=self.frequency_window_seconds)
        dq = self._history[from_addr]
        while dq and (now_dt - dq[0]) > window:
            dq.popleft()
        # Compute risk BEFORE recording this tx
        hist_risk = min(len(dq) / max(1, self.max_txs_in_window), 1.0)
        dq.append(now_dt)
        return float(hist_risk)

    def _anomaly_component(self, tx: dict) -> float:
        vec = np.asarray(featurize(tx), dtype=float)
        try:
            raw = float(self.anomaly_detector.score_transaction(vec))
        except NotFittedError:
            return 0.0
        except Exception:
            return 0.0
        # Normalize to 0..1 via 1 - exp(-x/scale)
        return float(1.0 - math.exp(-max(0.0, raw) / max(1e-6, self.anomaly_scale)))

    def _compliance_component(self, tx: dict) -> float:
        result = self.compliance_checker.validate(tx)
        return 0.0 if result.get("compliant", False) else 1.0

    def assess(self, tx: dict) -> dict:
        tx_hash = str(tx.get("tx_hash") or tx.get("tx_id") or "")
        from_addr = (tx.get("from_address") or tx.get("from") or "").lower()
        ts = _epoch_seconds(tx.get("timestamp"))

        c = self._compliance_component(tx)
        a = self._anomaly_component(tx)
        h = self._history_component(from_addr, ts)

        risk = 100.0 * (0.6 * c + 0.3 * a + 0.1 * h)
        # Clamp and round to two decimals
        risk = float(max(0.0, min(100.0, round(risk, 2))))

        return {"tx_hash": tx_hash, "risk_score": risk}
