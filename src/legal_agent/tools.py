from __future__ import annotations

from agents import function_tool

from legal_agent.config import get_settings
from legal_agent.guardrails import detect_high_risk_issue, standard_disclaimer
from legal_agent.retrieval import retrieve


@function_tool
def retrieve_local_legal_sources(query: str, limit: int = 5) -> str:
    """Search local legal source files and return citeable snippets."""
    settings = get_settings()
    chunks = retrieve(query=query, source_dir=settings.source_dir, limit=limit)
    if not chunks:
        return (
            "No matching local legal sources were found. Tell the user that the answer "
            "needs source verification before it is relied on."
        )

    rendered = []
    for index, chunk in enumerate(chunks, start=1):
        rendered.append(
            "[{}] file={}; heading={}; score={}\n{}".format(
                index, chunk.file, chunk.heading, chunk.score, chunk.text
            )
        )
    return "\n\n".join(rendered)


@function_tool
def legal_safety_check(user_question: str, jurisdiction: str | None = None) -> str:
    """Return legal safety warnings and the standard non-advice disclaimer."""
    active_jurisdiction = jurisdiction or get_settings().jurisdiction
    warnings = detect_high_risk_issue(user_question)
    lines = [standard_disclaimer(active_jurisdiction)]
    if warnings:
        lines.append("High-risk signals detected:")
        lines.extend("- {}".format(w) for w in warnings)
    else:
        lines.append("No high-risk signal was detected from the configured keyword list.")
    return "\n".join(lines)


@function_tool
def contract_review_tool(contract_text: str) -> str:
    """Review a contract text for risky clauses, missing clauses, and assign a risk score.
    Use this when the user provides contract text for analysis."""
    from legal_agent.contract_review import review_contract, format_review
    result = review_contract(contract_text)
    return format_review(result)
