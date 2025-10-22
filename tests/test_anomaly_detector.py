from __future__ import annotations

import numpy as np

from blockguard.agents.anomaly_detector import AnomalyDetector


def test_anomaly_detector_training_and_scoring():
    # Build a simple dataset: many small amounts, few large
    normal = np.random.normal(loc=100.0, scale=10.0, size=(200, 1))
    anomalies = np.random.uniform(low=1000.0, high=2000.0, size=(5, 1))
    X = np.vstack([normal, anomalies])

    det = AnomalyDetector(contamination=0.02, random_state=0)
    det.train_model(X)

    # Score a normal-like and an anomalous vector
    normal_score = det.score_transaction([110.0])
    anomalous_score = det.score_transaction([1500.0])

    assert anomalous_score > normal_score
    assert anomalous_score > 0
