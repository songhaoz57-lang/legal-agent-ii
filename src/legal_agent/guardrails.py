from __future__ import annotations

HIGH_RISK_TERMS = {
    "arrest": "Criminal defense issues can become urgent quickly.",
    "detained": "Detention requires immediate licensed legal help.",
    "deportation": "Immigration deadlines and removal proceedings are high risk.",
    "eviction notice": "Housing deadlines may be short and jurisdiction-specific.",
    "restraining order": "Safety orders require fast local legal review.",
    "domestic violence": "Safety planning and local emergency resources may be needed.",
    "suicide": "Immediate safety support is more important than legal drafting.",
    "deadline today": "Same-day legal deadlines require urgent professional review.",
    "statute of limitations": "Limitation periods can permanently affect rights.",
    "tax audit": "Tax matters need jurisdiction-specific professional advice.",
    "securities": "Securities questions carry regulatory and liability risk.",
    "刑事": "刑事事项需要尽快联系持证律师。",
    "拘留": "被拘留或羁押时应立即联系律师或法律援助机构。",
    "驱逐出境": "移民和驱逐程序通常有严格期限。",
    "家暴": "人身安全和保护令问题需要本地紧急资源支持。",
    "诉讼时效": "诉讼时效可能永久影响权利。",
    "今天截止": "当天截止事项需要紧急人工复核。",
}


def detect_high_risk_issue(text: str) -> list[str]:
    lowered = text.lower()
    return [reason for term, reason in HIGH_RISK_TERMS.items() if term.lower() in lowered]


def standard_disclaimer(jurisdiction: str) -> str:
    return (
        f"本回答仅提供一般法律信息和工作思路，默认司法辖区为 {jurisdiction}。"
        "它不是律师意见，也不建立律师-客户关系；请让持证律师结合完整事实和最新法律复核。"
    )

