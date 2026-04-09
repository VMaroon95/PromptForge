"""
Structure pass — improve prompt organization without losing content.
Adds role, context framing, and output format spec if missing.
"""

import re
from .models import ModelConfig

def has_role(text: str) -> bool:
    return bool(re.search(r'\b(you are|act as|your role|as a|you\'re a)\b', text, re.I))

def has_output_format(text: str) -> bool:
    return bool(re.search(
        r'\b(format|json|markdown|bullet|list|table|paragraph|numbered|output as)\b',
        text, re.I
    ))

def has_context_section(text: str) -> bool:
    return bool(re.search(r'(context:|background:|given|here is|below is)', text, re.I))

def structure(text: str, model_cfg: ModelConfig = None) -> str:
    """
    Restructure prompt for clarity. Preserves ALL original content —
    only adds framing, never removes task requirements.
    """
    # Detect if already well-structured (has multiple sections or XML tags)
    if text.count('\n') >= 4 and (has_role(text) or has_context_section(text)):
        return text  # Already structured, don't over-engineer

    lines = text.strip().splitlines()
    first_line = lines[0].strip() if lines else ""

    use_xml = model_cfg and model_cfg.prefers_xml

    # Split into task + context if long enough
    words = text.split()
    if len(words) < 15:
        # Short prompt — just clean it up
        return text

    # Detect if there's a context block (lines after the main ask)
    # Heuristic: first sentence is the task, rest is context
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    task_part = sentences[0] if sentences else text
    context_part = " ".join(sentences[1:]) if len(sentences) > 1 else ""

    if use_xml:
        parts = []
        if context_part:
            parts.append(f"<context>\n{context_part.strip()}\n</context>")
        parts.append(f"<task>\n{task_part.strip()}\n</task>")
        if not has_output_format(text):
            parts.append("<output_format>\nProvide a clear, well-organized response.\n</output_format>")
        return "\n\n".join(parts)
    else:
        parts = []
        if context_part:
            parts.append(f"**Context:**\n{context_part.strip()}")
        parts.append(f"**Task:**\n{task_part.strip()}")
        if not has_output_format(text):
            parts.append("**Output format:** Provide a clear, well-organized response.")
        return "\n\n".join(parts)
