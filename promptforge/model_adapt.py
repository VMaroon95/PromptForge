"""
Model-aware adaptation — what works for Claude ≠ GPT-4 ≠ Llama.
Applies model-specific formatting and style preferences.
"""

import re
from .models import ModelConfig, get_model

def adapt_for_claude(text: str) -> str:
    """
    Claude responds best to:
    - XML tags for structure (<task>, <context>, <format>)
    - Explicit role definitions
    - Clear task/context separation
    """
    # Convert markdown headers to XML if not already XML
    if "<task>" not in text and "<context>" not in text:
        text = re.sub(r'\*\*Task:\*\*\s*', '<task>\n', text)
        text = re.sub(r'\*\*Context:\*\*\s*', '<context>\n', text)
        text = re.sub(r'\*\*Output format:\*\*\s*', '<output_format>\n', text)
    return text

def adapt_for_gpt(text: str) -> str:
    """
    GPT models respond best to:
    - Markdown structure (### headings, **bold**)
    - Explicit step-by-step instructions
    - Clear delimiters between sections
    """
    # Convert XML tags to markdown if present
    text = re.sub(r'<task>\s*', '### Task\n', text)
    text = re.sub(r'</task>\s*', '\n', text)
    text = re.sub(r'<context>\s*', '### Context\n', text)
    text = re.sub(r'</context>\s*', '\n', text)
    text = re.sub(r'<output_format>\s*', '### Output Format\n', text)
    text = re.sub(r'</output_format>\s*', '\n', text)
    return text

def adapt_for_llama(text: str) -> str:
    """
    Llama models respond best to:
    - Concise, direct prompts
    - Minimal formatting overhead
    - Clear single-sentence task statement first
    """
    # Strip XML tags
    text = re.sub(r'<[^>]+>\s*', '', text)
    # Strip markdown headers, keep content
    text = re.sub(r'#{1,3}\s+', '', text)
    # Collapse extra whitespace
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    return text

def adapt_for_gemini(text: str) -> str:
    """Gemini is flexible — markdown works well, keep structure clean."""
    return adapt_for_gpt(text)

MODEL_ADAPTERS = {
    "claude":  adapt_for_claude,
    "gpt":     adapt_for_gpt,
    "llama":   adapt_for_llama,
    "mistral": adapt_for_gpt,
    "gemini":  adapt_for_gemini,
}

def adapt(text: str, model_name: str) -> str:
    """Apply model-specific adaptation."""
    cfg = get_model(model_name)
    if cfg and cfg.family in MODEL_ADAPTERS:
        return MODEL_ADAPTERS[cfg.family](text)
    return text
