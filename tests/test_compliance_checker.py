from __future__ import annotations

from blockguard.agents.simple_compliance_checker import ComplianceChecker


FIXED_TS = "2025-01-01T00:00:00Z"


def test_compliant_transaction():
    checker = ComplianceChecker(blacklist=set(), aml_threshold=10_000.0)
    tx = {
        "tx_hash": "0xok",
        "from_address": "0xfrom1",
        "to_address": "0xto1",
        "amount": 1000.0,
        "timestamp": FIXED_TS,
    }
    result = checker.validate(tx)
    assert result["tx_hash"] == "0xok"
    assert result["compliant"] is True
    assert result["violations"] == []


def test_blacklisted_and_aml_violation():
    bl = {"0xblocked"}
    checker = ComplianceChecker(blacklist=bl, aml_threshold=10_000.0)
    tx = {
        "tx_hash": "0xviolate",
        "from_address": "0xblocked",
        "to_address": "0xto2",
        "amount": 10_000.0,  # threshold reached => violation
        "timestamp": FIXED_TS,
    }
    result = checker.validate(tx)
    assert result["tx_hash"] == "0xviolate"
    assert result["compliant"] is False
    assert set(result["violations"]) >= {"blacklisted_address", "aml_threshold_exceeded"}


def test_frequency_violation_on_second_tx():
    checker = ComplianceChecker(blacklist=set(), aml_threshold=10_000.0, frequency_window_seconds=3600, max_txs_in_window=1)
    base_tx = {
        "tx_hash": "0xfirst",
        "from_address": "0xfromA",
        "to_address": "0xtoA",
        "amount": 100.0,
        "timestamp": FIXED_TS,
    }
    # First tx should be compliant
    first = checker.validate(base_tx)
    assert first["compliant"] is True
    # Second tx in same window should trigger frequency violation
    second = checker.validate({**base_tx, "tx_hash": "0xsecond"})
    assert second["compliant"] is False
    assert "frequency_limit_exceeded" in second["violations"]
