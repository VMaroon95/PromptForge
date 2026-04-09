"""
Anti-hallucination guardrails — grounding instructions, citation requests,
confidence calibration. Applied when risk of hallucination is high.

Patterns are specific: they must indicate a genuine factual-lookup intent,
not just incidental use of words like "number" or "market".
"""

import re

# High-risk patterns: must strongly suggest a factual retrieval intent.
# "number" alone → not enough. "what number", "exact figure", "statistic" → yes.
HIGH_RISK_PATTERNS = [
    # Explicit fact-lookup phrasing
    r'\b(what\s+(is|was|are|were)\s+the\s+(exact|current|latest|actual))',
    r'\b(statistic|statistics|percentage|percent(?!age)s?\s+of\s+\w)',
    r'\b(who\s+(invented|created|discovered|founded|wrote|first))',
    r'\b(when\s+(was|did|were|is)\s+\w)',
    r'\b(exact\s+(date|year|number|figure|amount|count))',

    # Recency-sensitive topics (explicit currency signals)
    r'\b(latest\s+(version|release|update|news|data|stats|figures))',
    r'\b(current\s+(price|rate|value|status|law|regulation|ceo|president))',
    r'\b(as\s+of\s+(today|now|\d{4}))',
    r'\b(up[\s-]to[\s-]date)',

    # Medical / legal / financial with specificity
    r'\b(diagnosis|dosage|drug\s+interaction|contraindication|clinical\s+trial)',
    r'\b(legal\s+(ruling|precedent|statute|code|requirement))',
    r'\b(court\s+(case|decision|ruling|order))',
    r'\b(investment\s+(return|yield|performance)|stock\s+price|valuation)',

    # Explicit citation request
    r'\b(cite\s+(your\s+)?sources?|provide\s+(references?|citations?)|list\s+your\s+sources?)',
    r'\b(peer[\s-]reviewed|published\s+(study|research|paper|journal))',
]

# Signals the prompt already handles grounding — don't add redundant guardrail
ALREADY_GROUNDED_PATTERNS = [
    r'\b(based\s+on\s+the\s+(provided|following|above|given|attached))',
    r'\b(according\s+to\s+the\s+(provided|following|document|text|data))',
    r'\b(from\s+the\s+(provided|following|above|given|attached))',
    r'don\'?t\s+(make\s+up|fabricate|invent|hallucinate)',
    r"if\s+you(?:\s+are|'re)\s+(not\s+sure|uncertain|unsure)",
    r'only\s+include\s+(facts|information)\s+you\'re\s+confident',
    r'do\s+not\s+fabricate',
    r'say\s+so\s+if\s+(you\'re\s+not\s+sure|uncertain)',
]

# Confidence-calibration: prompts asking for opinions/predictions/assessments
_OPINION_TRIGGERS = re.compile(
    r'\b(your\s+opinion|in\s+your\s+view|what\s+do\s+you\s+think'
    r'|predict|forecast|assess|evaluate\s+(the\s+)?risk'
    r'|is\s+it\s+(likely|possible|probable)'
    r'|your\s+(assessment|perspective|take\s+on))\b',
    re.I
)

# Idempotency: already has confidence language
_ALREADY_CALIBRATED = re.compile(
    r'\b(indicate\s+(your\s+)?confidence'
    r'|note\s+(your\s+)?uncertainty'
    r'|if\s+you\'re\s+not\s+sure'
    r'|acknowledge\s+(uncertainty|limitations)'
    r'|where\s+(relevant|appropriate),?\s+indicate)\b',
    re.I
)


def needs_grounding(text: str) -> bool:
    """True if the prompt has high hallucination risk and isn't already grounded."""
    lower = text.lower()
    if any(re.search(p, lower, re.I) for p in ALREADY_GROUNDED_PATTERNS):
        return False
    return any(re.search(p, lower, re.I) for p in HIGH_RISK_PATTERNS)


def apply_grounding(text: str) -> str:
    """Add anti-hallucination instructions when appropriate."""
    if not needs_grounding(text):
        return text

    guardrail = (
        "\n\nIMPORTANT: Only include information you are confident about. "
        "If you are uncertain about a specific fact, statistic, or date, "
        "say so explicitly rather than guessing. Do not fabricate sources or citations."
    )
    return text + guardrail


def apply_confidence_calibration(text: str) -> str:
    """Add confidence framing for opinion/prediction prompts. Idempotent."""
    if _ALREADY_CALIBRATED.search(text):
        return text
    if _OPINION_TRIGGERS.search(text):
        return text + "\n\nWhere relevant, indicate your level of confidence in your assessment."
    return text


GUARDRAILS = [
    ("grounding",              apply_grounding),
    ("confidence_calibration", apply_confidence_calibration),
]
