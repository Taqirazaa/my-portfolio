from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Sequence

from blockguard.agents.simple_compliance_checker import ComplianceChecker as SimpleComplianceChecker
from blockguard.agents.anomaly_detector import AnomalyDetector
from blockguard.agents.risk_assessor_scoring import RiskAssessor
from blockguard.agents.report_generator import ReportGenerator


@dataclass
class AuditProcessor:
    """Service pipeline chaining Compliance → Anomaly → Risk → Report.

    Input: sequence of transaction dicts
    Output: consolidated JSON with per-tx results and a generated report
    """

    compliance_checker: SimpleComplianceChecker
    anomaly_detector: AnomalyDetector
    risk_assessor: RiskAssessor
    report_generator: ReportGenerator

    @classmethod
    def default(cls) -> "AuditProcessor":
        return cls(
            compliance_checker=SimpleComplianceChecker(),
            anomaly_detector=AnomalyDetector(),
            risk_assessor=RiskAssessor(),
            report_generator=ReportGenerator(),
        )

    def process(self, txs: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
        # 1) Compliance per tx
        compliance_results: List[Dict[str, Any]] = [self.compliance_checker.validate(tx) for tx in txs]

        # 2) Anomaly: build feature vectors and score per tx
        from blockguard.scripts.train_isolation_forest import featurize  # reuse featurization
        X = [featurize(tx) for tx in txs]
        # If not trained, train on-the-fly using all data as background
        try:
            self.anomaly_detector.train_model(X)
        except Exception:
            pass
        anomaly_scores: List[float] = [self.anomaly_detector.score_transaction(vec) for vec in X]

        # 3) Risk per tx combines compliance + anomaly + history
        risk_results: List[Dict[str, Any]] = [self.risk_assessor.assess(tx) for tx in txs]

        # 4) Report using findings-like dicts
        findings_like = []
        for tx, comp, score in zip(txs, compliance_results, anomaly_scores):
            findings_like.append(
                {
                    "tx_hash": comp.get("tx_hash") or tx.get("tx_hash") or tx.get("tx_id"),
                    "finding_type": "rule_violation" if not comp.get("compliant", True) else "anomaly" if score > 0 else "info",
                    "rule_name": ",".join(comp.get("violations", [])) or None,
                    "severity": "high" if not comp.get("compliant", True) else ("medium" if score > 0.5 else "low"),
                    "score": score,
                    "details": {"violations": comp.get("violations", [])},
                }
            )
        report = self.report_generator.generate_report(findings_like)

        consolidated = {
            "transactions": [
                {
                    "tx_hash": comp.get("tx_hash") or tx.get("tx_hash") or tx.get("tx_id"),
                    "compliance": comp,
                    "anomaly_score": score,
                    "risk": risk,
                }
                for tx, comp, score, risk in zip(txs, compliance_results, anomaly_scores, risk_results)
            ],
            "report": report,
        }
        return consolidated
