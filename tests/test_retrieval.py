from pathlib import Path

from legal_agent.retrieval import retrieve


def test_retrieve_returns_matching_source(tmp_path: Path) -> None:
    source = tmp_path / "tenant.md"
    source.write_text("# Deposit\nSecurity deposit return rules and landlord notices.", encoding="utf-8")

    results = retrieve("landlord deposit", tmp_path)

    assert len(results) == 1
    assert results[0].file == "tenant.md"
    assert results[0].heading == "Deposit"


def test_retrieve_ignores_unmatched_source(tmp_path: Path) -> None:
    source = tmp_path / "contracts.txt"
    source.write_text("Liquidated damages and breach.", encoding="utf-8")

    assert retrieve("immigration visa", tmp_path) == []

