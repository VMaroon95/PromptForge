"""
Optimization techniques — chain-of-thought, few-shot, constraint injection, etc.
Applied selectively based on prompt content.
"""

import re
from .models import ModelConfig

def apply_chain_of_thought(text: str) -> str:
    """Add CoT instruction if prompt involves reasoning/analysis."""
    cot_triggers = [
        "analyze", "why", "how", "reason", "explain", "compare",
        "evaluate", "decide", "solve", "figure out", "determine"
    ]
    lower = text.lower()
    if any(t in lower for t in cot_triggers):
        if "step by step" not in lower and "think through" not in lower:
            return text + "\n\nThink step by step before giving your final answer."
    return text

def apply_output_constraints(text: str) -> str:
    """Add output format constraint if missing."""
    has_format = re.search(
        r'\b(format|json|markdown|bullet|list|numbered|table|paragraph)\b',
        text, re.I
    )
    has_length = re.search(
        r'\b(brief|concise|short|long|detailed|word|sentence|paragraph)\b',
        text, re.I
    )
    additions = []
    if not has_format:
        additions.append("Use clear formatting with headers or bullets where appropriate.")
    if not has_length:
        additions.append("Be concise but complete.")
    if additions:
        return text + "\n\n" + " ".join(additions)
    return text

def apply_role_framing(text: str, model_cfg: ModelConfig = None) -> str:
    """Prepend a role if none exists and task is domain-specific."""
    if re.search(r'\b(you are|act as|as a|your role)\b', text, re.I):
        return text

    domain_roles = {
        r'\b(code|function|class|debug|refactor|sql|python|javascript)\b': "expert software engineer",
        r'\b(data|analysis|statistics|chart|metric|dashboard)\b': "senior data analyst",
        r'\b(write|essay|article|blog|copy|content)\b': "professional writer",
        r'\b(security|vulnerability|threat|audit|pentest)\b': "cybersecurity expert",
        r'\b(legal|contract|clause|regulation|compliance)\b': "legal analyst",
        r'\b(business|strategy|market|revenue|ROI)\b': "business strategist",
    }

    for pattern, role in domain_roles.items():
        if re.search(pattern, text, re.I):
            prefix = f"You are a {role}.\n\n" if not (model_cfg and model_cfg.prefers_xml) else \
                     f"<role>You are a {role}.</role>\n\n"
            return prefix + text

    return text

def apply_specificity(text: str) -> str:
    """Add specificity constraints for vague prompts."""
    vague_patterns = [
        (r'\b(tell me about|write about|explain)\b(?!\s+(how|why|what|when|where))',
         "Be specific: include key facts, examples, and practical implications."),
        (r'\bsummariz(e|ing)\b',
         "Focus on the 3-5 most important points. Include key numbers or conclusions if present."),
    ]
    additions = []
    for pattern, hint in vague_patterns:
        if re.search(pattern, text, re.I) and hint not in text:
            additions.append(hint)
    if additions:
        return text + "\n\n" + " ".join(additions)
    return text

TECHNIQUES = [
    ("role_framing",       apply_role_framing),
    ("chain_of_thought",   apply_chain_of_thought),
    ("output_constraints", apply_output_constraints),
    ("specificity",        apply_specificity),
]
