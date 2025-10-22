from __future__ import annotations

import os
import math
import random
from dataclasses import dataclass
from typing import List, Dict, Sequence

import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score
import joblib

from blockguard.agents.anomaly_detector import AnomalyDetector


@dataclass
class SyntheticTxn:
    tx_hash: str
    from_address: str
    to_address: str
    amount: float
    token_symbol: str
    timestamp: float  # epoch seconds


def featurize(tx: Dict) -> List[float]:
    """Map a transaction dict to a numerical feature vector.

    Features:
      - log10(amount + 1)
      - token one-hot (top 3 tokens: USDC, USDT, ETH) => 3 dims
      - from/to address simple hash buckets (mod 100) normalized => 2 dims
      - hour of day (0..23) normalized
    """
    amount = float(tx.get("amount", 0.0))
    log_amount = math.log10(max(amount, 0.0) + 1.0)

    token = str(tx.get("token_symbol", "")).upper()
    token_vec = [1.0 if token == k else 0.0 for k in ("USDC", "USDT", "ETH")]

    def bucket(addr: str) -> float:
        if not addr:
            return 0.0
        # Simple deterministic bucket
        return (abs(hash(addr)) % 100) / 100.0

    from_b = bucket(str(tx.get("from_address") or tx.get("from") or ""))
    to_b = bucket(str(tx.get("to_address") or tx.get("to") or ""))

    ts = float(tx.get("timestamp", 0.0))
    hour = int((ts // 3600) % 24)
    hour_norm = hour / 23.0 if 23.0 else 0.0

    return [log_amount, *token_vec, from_b, to_b, hour_norm]


def generate_synthetic(n_normal: int = 1000, n_anom: int = 50) -> List[Dict]:
    txs: List[Dict] = []
    tokens = ["USDC", "USDT", "ETH"]

    # Normal transactions
    for i in range(n_normal):
        amount = max(0.0, random.gauss(500.0, 200.0))  # mostly small
        txs.append(
            {
                "tx_hash": f"0xnorm{i}",
                "from_address": f"0xfrom{random.randint(1, 200)}",
                "to_address": f"0xto{random.randint(1, 200)}",
                "amount": amount,
                "token_symbol": random.choice(tokens),
                "timestamp": random.uniform(1_700_000_000, 1_800_000_000),
            }
        )

    # Anomalous transactions
    for i in range(n_anom):
        amount = random.uniform(50_000, 500_000)
        txs.append(
            {
                "tx_hash": f"0xanom{i}",
                "from_address": f"0xfrom{random.randint(150, 250)}",
                "to_address": f"0xto{random.randint(150, 250)}",
                "amount": amount,
                "token_symbol": random.choice(tokens),
                "timestamp": random.uniform(1_700_000_000, 1_800_000_000),
                "label": 1,  # anomalous label for evaluation only
            }
        )

    return txs


def main() -> None:
    random.seed(42)
    np.random.seed(42)

    data = generate_synthetic()
    X = np.array([featurize(tx) for tx in data], dtype=float)

    # For evaluation, mark anomalies if present
    y = np.array([1 if tx.get("label") == 1 else 0 for tx in data], dtype=int)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

    detector = AnomalyDetector(contamination=max(0.01, y.mean() or 0.01))
    detector.train_model(X_train)

    # Evaluate: higher negative decision_function => more anomalous; our score_transaction returns positive anomaly
    scores = np.array([detector.score_transaction(x) for x in X_test])
    # Convert to AUC target: anomalies labeled 1, scores higher for anomalies
    auc = roc_auc_score(y_test, scores)
    print(f"Test AUC: {auc:.3f}")

    os.makedirs("/workspace/models", exist_ok=True)
    model_path = "/workspace/models/isolation_forest.joblib"
    joblib.dump(detector.model, model_path)
    print(f"Saved model to {model_path}")


if __name__ == "__main__":
    main()
