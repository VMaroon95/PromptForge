"""
Token compression — strip filler words while preserving semantic intent.
"""

import re

# Filler phrases that add tokens without meaning
FILLER_PATTERNS = [
    # Verbose openings
    (r"(?i)\bplease\s+(can\s+you\s+)?", ""),
    (r"(?i)\bI\s+(would|want to|need to|am going to|\'d like to)\s+ask\s+(you\s+)?", ""),
    (r"(?i)\bI\s+(would|\'d)\s+like\s+(you\s+)?to\s+", ""),
    (r"(?i)\bI\s+need\s+(you\s+)?to\s+", ""),
    (r"(?i)\bcan\s+you\s+please\s+", ""),
    (r"(?i)\bcould\s+you\s+please\s+", ""),
    (r"(?i)\bcould\s+you\s+", ""),
    (r"(?i)\bcan\s+you\s+", ""),

    # Redundant qualifiers
    (r"(?i)\bbasically\b\s*", ""),
    (r"(?i)\bactually\b\s*", ""),
    (r"(?i)\bjust\s+(?=\w)", ""),
    (r"(?i)\bsimply\s+(?=\w)", ""),
    (r"(?i)\bkindly\s+", ""),
    (r"(?i)\bfeel\s+free\s+to\s+", ""),

    # Verbose connectors
    (r"(?i)\bin\s+order\s+to\b", "to"),
    (r"(?i)\bdue\s+to\s+the\s+fact\s+that\b", "because"),
    (r"(?i)\bat\s+this\s+point\s+in\s+time\b", "now"),
    (r"(?i)\bfor\s+the\s+purpose\s+of\b", "to"),
    (r"(?i)\bwith\s+regard\s+to\b", "regarding"),
    (r"(?i)\bin\s+the\s+event\s+that\b", "if"),
    (r"(?i)\bprior\s+to\b", "before"),
    (r"(?i)\bsubsequent\s+to\b", "after"),

    # Filler sign-offs embedded in prompts
    (r"(?i)\bthank\s+you\s*(in\s+advance)?\b[,.]?\s*", ""),
    (r"(?i)\bthanks\b[,.]?\s*", ""),

    # Multiple spaces/newlines
    (r"\n{3,}", "\n\n"),
    (r" {2,}", " "),
]

def compress(text: str) -> str:
    """Apply compression passes, preserving semantic content."""
    result = text

    for pattern, replacement in FILLER_PATTERNS:
        result = re.sub(pattern, replacement, result)

    # Trim leading/trailing whitespace per line
    lines = [line.strip() for line in result.splitlines()]
    result = "\n".join(lines).strip()

    return result
