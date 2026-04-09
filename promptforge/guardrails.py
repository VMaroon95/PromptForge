"""
Anti-hallucination guardrails — grounding instructions, citation requests,
confidence calibration. Applied when risk of hallucination is high.
"""

import re

# Topics where hallucination risk is elevated
HIGH_RISK_TOPICS = [
    r'\b(fact|statistic|number|percent|date|year|when|who invented|who created)\b',
    r'\b(latest|current|recent|today|now|up to date|2024|2025|2026)\b',
    r'\b(medical|diagnosis|treatment|drug|medication|symptom|disease)\b',
    r'\b(legal|law|regulation|compliance|court|ruling)\b',
    r'\b(financial|investment|stock|price|market)\b',
    r'\b(citation|reference|source|study|research|paper)\b',
]

ALREADY_GROUNDED = [
    r'\b(based on|according to|from the|provided|cite|source|don\'t make up|if you\'re not sure)\b',
]

def needs_grounding(text: str) -> bool:
    lower = text.lower()
    if any(re.search(p, lower) for p in ALREADY_GROUNDED):
        return False
    return any(re.search(p, lower) for p in HIGH_RISK_TOPICS)

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
    """Add confidence framing for opinion/analysis prompts."""
    analysis_triggers = [
        r'\b(think|believe|opinion|perspective|view|assess|predict|forecast)\b'
    ]
    if any(re.search(p, text, re.I) for p in analysis_triggers):
        if "confident" not in text.lower() and "certain" not in text.lower():
            return text + "\n\nWhere relevant, indicate your level of confidence in your assessment."
    return text

GUARDRAILS = [
    ("grounding",              apply_grounding),
    ("confidence_calibration", apply_confidence_calibration),
]
