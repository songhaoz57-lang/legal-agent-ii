from __future__ import annotations

from agents import Agent, Runner

from legal_agent.config import get_settings
from legal_agent.prompts import LEGAL_AGENT_INSTRUCTIONS
from legal_agent.tools import (
    legal_safety_check,
    retrieve_local_legal_sources,
    contract_review_tool,
)


def build_agent() -> Agent:
    settings = get_settings()
    return Agent(
        name="Legal Triage Agent",
        instructions=LEGAL_AGENT_INSTRUCTIONS,
        model=settings.model,
        tools=[legal_safety_check, retrieve_local_legal_sources, contract_review_tool],
    )


async def ask_legal_agent(question: str, jurisdiction: str | None = None) -> str:
    settings = get_settings()
    active_jurisdiction = jurisdiction or settings.jurisdiction
    prompt = (
        "Jurisdiction: " + active_jurisdiction + "\n"
        "User question:\n" + question + "\n\n"
        "First run the safety check. Then search local legal sources. "
        "If the user provides contract text, use the contract review tool. "
        "If local sources are not enough, say what needs verification."
    )
    result = await Runner.run(build_agent(), prompt)
    return result.final_output
