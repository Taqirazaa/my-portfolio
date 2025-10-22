from __future__ import annotations

from typing import Sequence
from dataclasses import dataclass

import numpy as np
from sklearn.ensemble import IsolationForest
import joblib

from blockguard.schemas.transaction import TransactionIn
from blockguard.schemas.audit import AuditFindingOut


@dataclass
class AnomalyDetector:
    name: str = "AnomalyDetector"
    contamination: float = 0.05
    random_state: int = 42

    def __post_init__(self) -> None:
        self.model = IsolationForest(contamination=self.contamination, random_state=self.random_state)

    async def run(self, transactions: Sequence[TransactionIn]) -> list[AuditFindingOut]:
        if not transactions:
            return []

        amounts = np.array([[float(tx.amount)] for tx in transactions], dtype=float)
        self.model.fit(amounts)
        scores = self.model.decision_function(amounts)
        preds = self.model.predict(amounts)  # -1 anomaly, 1 normal

        findings: list[AuditFindingOut] = []
        for tx, pred, score in zip(transactions, preds, scores):
            if pred == -1:
                findings.append(
                    AuditFindingOut(
                        id="",
                        audit_run_id="",
                        transaction_id=tx.tx_id,
                        finding_type="anomaly",
                        rule_name=None,
                        severity="medium",
                        score=float(-score),
                        details={"amount": float(tx.amount)},
                    )
                )
        return findings

    # --- Model management API ---
    def train_model(self, X: Sequence[Sequence[float]]) -> None:
        """Train the IsolationForest model with feature matrix X."""
        features = np.asarray(X, dtype=float)
        if features.ndim != 2 or features.shape[0] == 0:
            raise ValueError("X must be a non-empty 2D array-like [n_samples, n_features]")
        self.model.fit(features)

    def load_model(self, path: str) -> None:
        """Load a persisted IsolationForest model from disk using joblib."""
        loaded = joblib.load(path)
        if not isinstance(loaded, IsolationForest):
            raise TypeError("Loaded object is not an IsolationForest model")
        self.model = loaded

    def score_transaction(self, vector: Sequence[float]) -> float:
        """Return anomaly score for a single feature vector (higher = more anomalous)."""
        if self.model is None:
            raise ValueError("Model is not initialized")
        vec = np.asarray(vector, dtype=float).reshape(1, -1)
        score = self.model.decision_function(vec)[0]
        return float(-score)
