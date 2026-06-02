# -*- coding: utf-8 -*-
from __future__ import annotations

import os
from openai import OpenAI

from legal_agent.config import get_settings
from legal_agent.prompts import LEGAL_AGENT_INSTRUCTIONS


def _get_client():
    settings = get_settings()
    base_url = os.environ.get("OPENAI_BASE_URL", "")
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if base_url:
        return OpenAI(api_key=api_key, base_url=base_url)
    return OpenAI(api_key=api_key)


async def ask_legal_agent(question: str, jurisdiction: str | None = None) -> str:
    settings = get_settings()
    active_jurisdiction = jurisdiction or settings.jurisdiction
    client = _get_client()

    messages = [
        {"role": "system", "content": LEGAL_AGENT_INSTRUCTIONS},
        {"role": "user", "content": f"Jurisdiction: {active_jurisdiction}\n\nQuestion: {question}"},
    ]

    try:
        resp = client.chat.completions.create(
            model=settings.model,
            messages=messages,
            max_tokens=2000,
            temperature=0.3,
        )
        return resp.choices[0].message.content or "No response."
    except Exception as e:
        return f"Error: {e}"


def build_agent():
    """Kept for backwards compatibility - returns None as we use direct API now."""
    return None
