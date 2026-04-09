"""
Token counting — tiktoken for GPT models, estimates for others.
"""

from typing import Optional

def count_tokens(text: str, model: str = "gpt-4") -> int:
    """Count tokens for given text and model."""
    try:
        import tiktoken
        try:
            enc = tiktoken.encoding_for_model(model)
        except KeyError:
            enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except ImportError:
        # Fallback: ~4 chars per token (rough estimate)
        return max(1, len(text) // 4)

def token_delta(original: str, optimized: str, model: str = "gpt-4") -> dict:
    """Return token stats comparing original vs optimized prompt."""
    orig_tokens = count_tokens(original, model)
    opt_tokens = count_tokens(optimized, model)
    delta = opt_tokens - orig_tokens
    pct = (delta / orig_tokens * 100) if orig_tokens > 0 else 0

    return {
        "original": orig_tokens,
        "optimized": opt_tokens,
        "delta": delta,
        "pct_change": round(pct, 1),
        "saved": max(0, -delta),
        "added": max(0, delta),
        "direction": "reduced" if delta < 0 else "increased" if delta > 0 else "unchanged",
    }

def format_token_stats(stats: dict) -> str:
    """Human-readable token stats, honest about increases."""
    d, o, opt = stats["delta"], stats["original"], stats["optimized"]
    pct = abs(stats["pct_change"])

    if d < 0:
        return f"{o} → {opt} tokens ({pct:.1f}% reduction, saved {abs(d)})"
    elif d > 0:
        return f"{o} → {opt} tokens (+{d} added, {pct:.1f}% increase — quality trade-off)"
    else:
        return f"{o} tokens (unchanged)"
