from legal_agent.guardrails import detect_high_risk_issue, standard_disclaimer


def test_detects_high_risk_issue_in_english() -> None:
    warnings = detect_high_risk_issue("I received an eviction notice with a deadline today.")
    assert warnings


def test_detects_high_risk_issue_in_chinese() -> None:
    warnings = detect_high_risk_issue("这个案子可能涉及刑事拘留。")
    assert warnings


def test_standard_disclaimer_includes_jurisdiction() -> None:
    assert "California" in standard_disclaimer("California")
