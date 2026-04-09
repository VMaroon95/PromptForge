"""
Optimization techniques — chain-of-thought, role framing, constraint injection, specificity.
All passes are idempotent — they never duplicate instructions already present.
"""

import re
from .models import ModelConfig


def _already_has(text: str, *phrases: str) -> bool:
    """Case-insensitive check for existing phrases — prevents duplication."""
    lower = text.lower()
    return any(p.lower() in lower for p in phrases)


def apply_chain_of_thought(text: str) -> str:
    """Add CoT only if prompt involves reasoning AND doesn't already request it."""
    if _already_has(text, "step by step", "think through", "chain of thought", "let's think"):
        return text
    cot_triggers = [
        "analyze", "why", "how does", "reason", "compare", "evaluate",
        "decide", "solve", "figure out", "determine", "assess", "explain why"
    ]
    if any(t in text.lower() for t in cot_triggers):
        return text + "\n\nThink step by step before giving your final answer."
    return text


def apply_output_constraints(text: str) -> str:
    """Add format/length hints only if genuinely missing. Idempotent."""
    has_format = re.search(
        r'\b(format|json|markdown|bullet|list|numbered|table|paragraph|output as|return a|return as)\b',
        text, re.I
    )
    has_length = re.search(
        r'\b(brief|concise|short|long|detailed|word|sentence|paragraph|limit|max|under \d+)\b',
        text, re.I
    )
    additions = []
    fmt_hint = "Use clear formatting with headers or bullets where appropriate."
    len_hint = "Be concise but complete."

    if not has_format and not _already_has(text, fmt_hint):
        additions.append(fmt_hint)
    if not has_length and not _already_has(text, len_hint):
        additions.append(len_hint)

    return (text + "\n\n" + " ".join(additions)).rstrip() if additions else text


def apply_role_framing(text: str, model_cfg: ModelConfig = None) -> str:
    """
    Prepend a domain-specific role only when:
    - No role already exists
    - Prompt is long enough to have a clear domain
    - Domain is unambiguously detected
    Uses correct grammar (a/an).
    """
    if re.search(r'\b(you are|act as|as a|your role|you\'re a)\b', text, re.I):
        return text
    if text.strip().endswith('?') or len(text.split()) < 8:
        return text

    # Domain → role mapping with correct a/an
    domain_roles = [
        (r'\b(code|function|class|debug|refactor|sql|python|javascript|typescript|api|backend|frontend)\b',
         ("an", "expert software engineer")),
        (r'\b(data|analysis|statistics|chart|metric|dashboard|csv|pandas|dataframe)\b',
         ("a", "senior data analyst")),
        (r'\b(security|vulnerability|threat|audit|pentest|cve|exploit)\b',
         ("a", "cybersecurity expert")),
        (r'\b(legal|contract|clause|regulation|compliance|gdpr|statute)\b',
         ("a", "legal analyst")),
        (r'\b(business|strategy|market|revenue|roi|competitive|go-to-market)\b',
         ("a", "business strategist")),
        (r'\b(medical|clinical|diagnosis|treatment|dosage|symptom|patient)\b',
         ("a", "medical information specialist")),
        (r'\b(finance|investment|portfolio|stock|bond|valuation|accounting)\b',
         ("a", "financial analyst")),
        (r'\b(design|ux|ui|wireframe|figma|user.experience|interface)\b',
         ("a", "UX/UI designer")),
    ]

    for pattern, (article, role) in domain_roles:
        if re.search(pattern, text, re.I):
            use_xml = model_cfg and model_cfg.prefers_xml
            if use_xml:
                prefix = f"<role>You are {article} {role}.</role>\n\n"
            else:
                prefix = f"You are {article} {role}.\n\n"
            return prefix + text

    return text  # No clear domain — don't assign a generic role


def apply_specificity(text: str) -> str:
    """Add specificity hints for vague prompts. Idempotent."""
    vague_patterns = [
        (r'\b(tell me about|write about)\s+\w',
         "Be specific: include key facts, examples, and practical implications."),
        (r'\bsummariz(e|ing)\b',
         "Focus on the 3-5 most important points. Include key numbers or conclusions if present."),
    ]
    additions = []
    lower = text.lower()
    for pattern, hint in vague_patterns:
        if re.search(pattern, lower) and hint.lower() not in lower:
            additions.append(hint)
    return (text + "\n\n" + " ".join(additions)) if additions else text


TECHNIQUES = [
    ("role_framing",       apply_role_framing),
    ("chain_of_thought",   apply_chain_of_thought),
    ("output_constraints", apply_output_constraints),
    ("specificity",        apply_specificity),
]
