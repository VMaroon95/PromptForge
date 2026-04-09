"""
Model definitions and per-model configuration.
Knows what each model responds best to.
"""

from dataclasses import dataclass, field
from typing import Optional

@dataclass
class ModelConfig:
    name: str
    family: str                     # claude | gpt | gemini | llama | mistral
    context_window: int
    prefers_xml: bool = False
    prefers_markdown: bool = True
    prefers_concise: bool = False
    supports_system_prompt: bool = True
    max_few_shot: int = 5
    notes: str = ""

MODELS: dict[str, ModelConfig] = {
    # Anthropic Claude
    "claude-3-5-sonnet": ModelConfig("claude-3-5-sonnet", "claude", 200_000, prefers_xml=True, prefers_markdown=False, notes="Loves XML tags, structured roles"),
    "claude-3-opus":     ModelConfig("claude-3-opus",     "claude", 200_000, prefers_xml=True, prefers_markdown=False),
    "claude-3-haiku":    ModelConfig("claude-3-haiku",    "claude", 200_000, prefers_xml=True, prefers_concise=True),

    # OpenAI
    "gpt-4o":            ModelConfig("gpt-4o",            "gpt",   128_000, prefers_markdown=True),
    "gpt-4-turbo":       ModelConfig("gpt-4-turbo",       "gpt",   128_000, prefers_markdown=True),
    "gpt-3.5-turbo":     ModelConfig("gpt-3.5-turbo",     "gpt",    16_000, prefers_markdown=True, prefers_concise=True),

    # Google
    "gemini-1.5-pro":    ModelConfig("gemini-1.5-pro",    "gemini", 1_000_000, prefers_markdown=True),
    "gemini-flash":      ModelConfig("gemini-flash",      "gemini",  1_000_000, prefers_concise=True),

    # Meta Llama
    "llama-3-70b":       ModelConfig("llama-3-70b",       "llama",  32_000, prefers_concise=True, prefers_markdown=False),
    "llama-3-8b":        ModelConfig("llama-3-8b",        "llama",  32_000, prefers_concise=True, prefers_markdown=False),

    # Mistral
    "mistral-large":     ModelConfig("mistral-large",     "mistral", 32_000, prefers_markdown=True),
}

def get_model(name: str) -> Optional[ModelConfig]:
    name = name.lower().strip()
    if name in MODELS:
        return MODELS[name]
    # fuzzy match
    for key, cfg in MODELS.items():
        if name in key or key in name:
            return cfg
    return None

def list_models() -> list[str]:
    return list(MODELS.keys())
