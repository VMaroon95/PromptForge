"""
Token compression — strip filler words while preserving semantic intent.
Cleans up punctuation artifacts after removal.
"""

import re

FILLER_PATTERNS = [
    # Compound phrases first (most specific → least specific)
    (r"(?i)\bplease\s+can\s+you\s+", ""),
    (r"(?i)\bcould\s+you\s+please\s+", ""),
    (r"(?i)\bcan\s+you\s+please\s+", ""),
    (r"(?i)\bI\s+(?:would|want\s+to|need\s+to|am\s+going\s+to|'d\s+like\s+to)\s+ask\s+(?:you\s+)?", ""),
    (r"(?i)\bI\s+(?:would|'d)\s+like\s+(?:you\s+)?to\s+", ""),
    (r"(?i)\bI\s+need\s+(?:you\s+)?to\s+", ""),
    (r"(?i)\bcould\s+you\s+", ""),
    (r"(?i)\bcan\s+you\s+", ""),
    (r"(?i)(?<!\w)please\s+(?=\w)", ""),

    # Redundant qualifiers — only standalone, not inside compound words
    (r"(?i)(?<![a-z])basically,?\s+", ""),
    (r"(?i)(?<![a-z])actually,?\s+", ""),
    (r"(?i)\bjust\s+(?=(?:help|write|create|make|tell|explain|show|give|find|list|analyze|summarize)\b)", ""),
    (r"(?i)\bsimply\s+(?=[a-z])", ""),
    (r"(?i)\bkindly\s+", ""),
    (r"(?i)\bfeel\s+free\s+to\s+", ""),

    # Verbose connectors → concise equivalents
    (r"(?i)\bin\s+order\s+to\b", "to"),
    (r"(?i)\bdue\s+to\s+the\s+fact\s+that\b", "because"),
    (r"(?i)\bat\s+this\s+point\s+in\s+time\b", "now"),
    (r"(?i)\bfor\s+the\s+purpose\s+of\b", "to"),
    (r"(?i)\bwith\s+regard\s+to\b", "regarding"),
    (r"(?i)\bin\s+the\s+event\s+that\b", "if"),
    (r"(?i)\bprior\s+to\b", "before"),
    (r"(?i)\bsubsequent\s+to\b", "after"),
    (r"(?i)\bin\s+spite\s+of\s+the\s+fact\s+that\b", "although"),

    # Filler sign-offs
    (r"(?i)\bthank\s+you\s*(?:in\s+advance)?[,.]?\s*", ""),
    (r"(?i)\bthanks[,.]?\s*", ""),
]

def _clean_artifacts(text: str) -> str:
    """Fix punctuation left behind after removals."""
    text = re.sub(r',\s*,+', ',', text)          # double commas
    text = re.sub(r'\s+,', ',', text)             # space before comma
    text = re.sub(r'(?m)^,\s*', '', text)         # leading comma on line
    text = re.sub(r'(?<=[.!?])\s*,\s*', ' ', text)  # comma after sentence end
    text = re.sub(r'[^\S\n]{2,}', ' ', text)     # multiple spaces (not newlines)
    text = re.sub(r'\n{3,}', '\n\n', text)        # 3+ newlines → 2
    lines = [line.strip() for line in text.splitlines()]
    return '\n'.join(lines).strip()

def compress(text: str) -> str:
    """Strip filler, then clean punctuation artifacts."""
    result = text
    for pattern, replacement in FILLER_PATTERNS:
        result = re.sub(pattern, replacement, result)
    return _clean_artifacts(result)
