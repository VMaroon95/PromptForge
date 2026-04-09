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
    # Anthropic Claude — xml-preferred, latest first
    "claude-opus-4":       ModelConfig("claude-opus-4",       "claude", 200_000, prefers_xml=True, prefers_markdown=False, notes="Strongest reasoning, loves XML"),
    "claude-sonnet-4":     ModelConfig("claude-sonnet-4",     "claude", 200_000, prefers_xml=True, prefers_markdown=False),
    "claude-3-7-sonnet":   ModelConfig("claude-3-7-sonnet",   "claude", 200_000, prefers_xml=True, prefers_markdown=False),
    "claude-3-5-sonnet":   ModelConfig("claude-3-5-sonnet",   "claude", 200_000, prefers_xml=True, prefers_markdown=False, notes="Loves XML tags, structured roles"),
    "claude-3-opus":       ModelConfig("claude-3-opus",       "claude", 200_000, prefers_xml=True, prefers_markdown=False),
    "claude-3-haiku":      ModelConfig("claude-3-haiku",      "claude", 200_000, prefers_xml=True, prefers_concise=True),
    "claude-3-5-haiku":    ModelConfig("claude-3-5-haiku",    "claude", 200_000, prefers_xml=True, prefers_concise=True),

    # OpenAI
    "gpt-4o":              ModelConfig("gpt-4o",              "gpt",   128_000, prefers_markdown=True),
    "gpt-4o-mini":         ModelConfig("gpt-4o-mini",         "gpt",   128_000, prefers_markdown=True, prefers_concise=True),
    "gpt-4-turbo":         ModelConfig("gpt-4-turbo",         "gpt",   128_000, prefers_markdown=True),
    "gpt-4":               ModelConfig("gpt-4",               "gpt",     8_000, prefers_markdown=True),
    "gpt-3.5-turbo":       ModelConfig("gpt-3.5-turbo",       "gpt",    16_000, prefers_markdown=True, prefers_concise=True),
    "o1":                  ModelConfig("o1",                  "gpt",   128_000, prefers_markdown=True, notes="Reasoning model — no system prompt needed"),
    "o3":                  ModelConfig("o3",                  "gpt",   200_000, prefers_markdown=True, notes="Reasoning model"),

    # Google
    "gemini-2.0-flash":    ModelConfig("gemini-2.0-flash",    "gemini", 1_000_000, prefers_markdown=True, prefers_concise=True),
    "gemini-2.5-pro":      ModelConfig("gemini-2.5-pro",      "gemini", 1_000_000, prefers_markdown=True),
    "gemini-1.5-pro":      ModelConfig("gemini-1.5-pro",      "gemini", 1_000_000, prefers_markdown=True),
    "gemini-flash":        ModelConfig("gemini-flash",        "gemini", 1_000_000, prefers_concise=True),

    # Meta Llama
    "llama-3.1-405b":      ModelConfig("llama-3.1-405b",      "llama",  32_000, prefers_concise=True, prefers_markdown=False),
    "llama-3.1-70b":       ModelConfig("llama-3.1-70b",       "llama",  32_000, prefers_concise=True, prefers_markdown=False),
    "llama-3.1-8b":        ModelConfig("llama-3.1-8b",        "llama",  32_000, prefers_concise=True, prefers_markdown=False),
    "llama-3-70b":         ModelConfig("llama-3-70b",         "llama",  32_000, prefers_concise=True, prefers_markdown=False),
    "llama-3-8b":          ModelConfig("llama-3-8b",          "llama",  32_000, prefers_concise=True, prefers_markdown=False),

    # Mistral
    "mistral-large":       ModelConfig("mistral-large",       "mistral", 32_000, prefers_markdown=True),
    "mistral-medium":      ModelConfig("mistral-medium",      "mistral", 32_000, prefers_markdown=True),
    "mistral-small":       ModelConfig("mistral-small",       "mistral", 32_000, prefers_markdown=True, prefers_concise=True),
    "mixtral-8x7b":        ModelConfig("mixtral-8x7b",        "mistral", 32_000, prefers_markdown=True),

    # DeepSeek
    "deepseek-r1":         ModelConfig("deepseek-r1",         "gpt",   128_000, prefers_markdown=True, notes="Strong reasoning model"),
    "deepseek-v3":         ModelConfig("deepseek-v3",         "gpt",   128_000, prefers_markdown=True),
}

# Family-level keyword fallbacks for fuzzy matching
_FAMILY_KEYWORDS = [
    ("claude",   "claude"),
    ("gpt",      "gpt"),
    ("o1",       "gpt"),
    ("o3",       "gpt"),
    ("gemini",   "gemini"),
    ("llama",    "llama"),
    ("mistral",  "mistral"),
    ("mixtral",  "mistral"),
    ("deepseek", "gpt"),
]

def get_model(name: str) -> Optional[ModelConfig]:
    """
    Look up model config by name. Tries exact match first, then
    substring fuzzy match, then family-keyword fallback.
    """
    if not name:
        return None
    name = name.lower().strip()
    # Exact match
    if name in MODELS:
        return MODELS[name]
    # Substring match (longer keys first to prefer specificity)
    for key in sorted(MODELS, key=len, reverse=True):
        if name in key or key in name:
            return MODELS[key]
    # Family-level fallback: return best representative of detected family
    for keyword, family in _FAMILY_KEYWORDS:
        if keyword in name:
            for cfg in MODELS.values():
                if cfg.family == family:
                    return cfg
    return None

def list_models() -> list[str]:
    return list(MODELS.keys())
