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

    # Domain → role mapping with correct a/an.
    # ORDER MATTERS: more specific patterns must come before general ones.
    # E.g. medical before data-analyst (medical prompts may mention "data").
    domain_roles = [
        # Specific technical domains first
        (r'\b(medical|clinical|diagnosis|treatment|dosage|symptom|patient|healthcare|prescription)\b',
         ("a", "medical information specialist")),
        (r'\b(security|vulnerability|threat|audit|pentest|cve|exploit|malware|firewall|cybersec)\b',
         ("a", "cybersecurity expert")),
        (r'\b(legal|contract|clause|regulation|compliance|gdpr|statute|intellectual\s+property|litigation)\b',
         ("a", "legal analyst")),
        (r'\b(devops|ci\s*/\s*cd|kubernetes|docker|deployment|infrastructure|terraform|pipeline)\b',
         ("a", "DevOps engineer")),
        (r'\b(machine\s+learning|neural\s+network|deep\s+learning|model\s+training|pytorch|tensorflow|llm|bert|transformer)\b',
         ("an", "ML engineer")),
        (r'\b(code|function|class|debug|refactor|sql|python|javascript|typescript|api|backend|frontend)\b',
         ("an", "expert software engineer")),
        # Business/finance — check for specificity
        (r'\b(finance|investment|portfolio|stock|bond|valuation|accounting|budget|financial\s+model)\b',
         ("a", "financial analyst")),
        (r'\b(business|strategy|revenue|roi|competitive|go-to-market|startup|saas|b2b|product.market.fit)\b',
         ("a", "business strategist")),
        # Data — general, after specific domains
        (r'\b(data\s+(analysis|science|visualization|pipeline|warehouse|lake)|statistics|pandas|dataframe|tableau|dashboard|csv)\b',
         ("a", "senior data analyst")),
        # Creative/content
        (r'\b(seo|content\s+(marketing|strategy|calendar)|blog\s+(post|article)|copywriting|headline|landing\s+page)\b',
         ("a", "content marketing specialist")),
        (r'\b(design|ux|ui|wireframe|figma|user.experience|interface|prototype|accessibility)\b',
         ("a", "UX/UI designer")),
        # Education and language
        (r'\b(teach|lesson\s+plan|curriculum|student|learning\s+objective|pedagogy|explain\s+to\s+(a|beginners?))\b',
         ("an", "expert educator")),
        (r'\b(product\s+(manager|management|roadmap|backlog|sprint|user\s+story|acceptance\s+criteria))\b',
         ("a", "senior product manager")),
        (r'\b(translate|translation|localization|Spanish|French|German|Mandarin|Arabic|Japanese)\b',
         ("a", "professional translator")),
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


def apply_few_shot_hint(text: str) -> str:
    """
    Suggest an example for complex generation tasks where the format
    is custom or ambiguous. Only fires when:
      - prompt is asking to generate/create/write something
      - no example is already present
      - the output format is non-standard (no JSON/markdown/list spec)
    """
    if _already_has(text, "example:", "for example", "e.g.", "such as", "<example>",
                    "input:", "output:", "like this", "as follows", "here's an example"):
        return text

    # Must be a generation task
    generation_triggers = re.compile(
        r'\b(write|generate|create|draft|compose|produce)\b', re.I
    )
    if not generation_triggers.search(text):
        return text

    # Output format already specified — example hint is less critical
    format_specified = re.search(
        r'\b(json|markdown|csv|xml|numbered\s+list|bullet|table)\b', text, re.I
    )
    if format_specified:
        return text

    # Only add for non-trivial writes (not "Write a poem")
    if len(text.split()) < 12:
        return text

    hint = "\n\nIf the desired output format is non-obvious, include a brief example of what you expect."
    return text + hint


TECHNIQUES = [
    ("role_framing",       apply_role_framing),
    ("chain_of_thought",   apply_chain_of_thought),
    ("output_constraints", apply_output_constraints),
    ("specificity",        apply_specificity),
    ("few_shot_hint",      apply_few_shot_hint),
]
