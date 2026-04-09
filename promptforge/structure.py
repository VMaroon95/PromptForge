"""
Structure pass — improve prompt organization without losing content.
Only restructures prompts that genuinely lack structure.
Preserves role-first, XML, multi-step, questions, and already-organized prompts.
"""

import re
from .models import ModelConfig


def has_role(text: str) -> bool:
    return bool(re.search(r'\b(you are|act as|your role|as a|you\'re a)\b', text, re.I))

def has_xml_tags(text: str) -> bool:
    return bool(re.search(r'<(task|context|system|role|output|instruction)[^>]*>', text, re.I))

def has_markdown_structure(text: str) -> bool:
    return bool(re.search(r'(\*\*(task|context|background|instructions|output)[:\s]|\#{1,3}\s)', text, re.I))

def has_numbered_steps(text: str) -> bool:
    return bool(re.search(r'^\s*\d+[.)]\s', text, re.M))

def has_output_format(text: str) -> bool:
    return bool(re.search(
        r'\b(format|json|markdown|bullet|list|table|paragraph|numbered|output as|return a)\b',
        text, re.I
    ))

def is_already_structured(text: str) -> bool:
    """Return True if the prompt is already well-structured and should not be touched."""
    return any([
        has_role(text),
        has_xml_tags(text),
        has_markdown_structure(text),
        has_numbered_steps(text),
        len(text.split()) < 20,
        len([s for s in re.split(r'(?<=[.!?])\s+', text.strip()) if s.strip()]) <= 1,
    ])

def is_question(text: str) -> bool:
    """Detect question-form prompts — restructuring breaks their intent."""
    stripped = text.strip()
    return stripped.endswith('?') or bool(re.match(
        r'^(what|how|why|when|where|who|which|can|could|would|is|are|do|does|did)\b',
        stripped, re.I
    ))

def structure(text: str, model_cfg: ModelConfig = None) -> str:
    """
    Restructure only prompts that genuinely lack organization.
    Skips: role-first, XML, markdown-structured, numbered, questions, short prompts.
    """
    if is_already_structured(text) or is_question(text):
        return text

    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text.strip()) if s.strip()]

    # Need at least 3 sentences to justify restructuring
    if len(sentences) < 3:
        return text

    # Separate constraint sentences from core task sentences
    constraint_pat = re.compile(
        r'\b(format|output|return|include|exclude|avoid|do not|must|should|only|use|provide|ensure)\b',
        re.I
    )
    task_sentences = [s for s in sentences if not constraint_pat.search(s)]
    constraint_sentences = [s for s in sentences if constraint_pat.search(s)]

    # If we can't cleanly separate, don't restructure
    if not task_sentences or not constraint_sentences:
        return text

    task_part = ' '.join(task_sentences)
    constraint_part = ' '.join(constraint_sentences)
    use_xml = model_cfg and model_cfg.prefers_xml

    if use_xml:
        parts = [
            f"<task>\n{task_part}\n</task>",
            f"<requirements>\n{constraint_part}\n</requirements>",
        ]
        if not has_output_format(text):
            parts.append("<output_format>\nProvide a clear, well-organized response.\n</output_format>")
    else:
        parts = [
            f"**Task:**\n{task_part}",
            f"**Requirements:**\n{constraint_part}",
        ]
        if not has_output_format(text):
            parts.append("**Output format:** Provide a clear, well-organized response.")

    return "\n\n".join(parts)
