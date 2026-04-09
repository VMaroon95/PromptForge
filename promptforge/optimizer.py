"""
Optimizer — orchestrates all passes in sequence.
Returns before/after with per-pass diffs.
"""

from dataclasses import dataclass, field
from typing import Optional

from .compress import compress
from .structure import structure
from .techniques import TECHNIQUES
from .guardrails import GUARDRAILS
from .model_adapt import adapt
from .scorer import score_prompt, QualityScore
from .tokenizer import token_delta
from .models import get_model, ModelConfig


@dataclass
class PassResult:
    name: str
    before: str
    after: str
    changed: bool = False

    def __post_init__(self):
        self.changed = self.before != self.after


@dataclass
class OptimizationResult:
    original: str
    optimized: str
    model: Optional[str]
    passes: list[PassResult] = field(default_factory=list)
    score_before: QualityScore = None
    score_after: QualityScore = None
    token_stats: dict = field(default_factory=dict)

    @property
    def quality_delta(self) -> int:
        if self.score_before and self.score_after:
            return self.score_after.total - self.score_before.total
        return 0

    @property
    def passes_applied(self) -> list[str]:
        return [p.name for p in self.passes if p.changed]


def optimize(
    prompt: str,
    model: str = None,
    passes: list[str] = None,
    skip_passes: list[str] = None,
) -> OptimizationResult:
    """
    Run all optimization passes on a prompt.

    Args:
        prompt:      Raw input prompt
        model:       Target model name (for model-aware adaptation)
        passes:      Whitelist of passes to run (default: all)
        skip_passes: Passes to skip

    Returns:
        OptimizationResult with full diff trail
    """
    model_cfg: Optional[ModelConfig] = get_model(model) if model else None
    skip = set(skip_passes or [])

    score_before = score_prompt(prompt)
    current = prompt
    pass_results = []

    def run_pass(name: str, fn, *args):
        nonlocal current
        if passes and name not in passes:
            return
        if name in skip:
            return
        before = current
        current = fn(current, *args) if args else fn(current)
        pass_results.append(PassResult(name=name, before=before, after=current))

    # 1. Compress (reduce tokens)
    run_pass("compress", compress)

    # 2. Structure (organize sections)
    run_pass("structure", structure, model_cfg)

    # 3. Techniques (CoT, role framing, etc.)
    for name, fn in TECHNIQUES:
        if name == "role_framing":
            run_pass(name, fn, model_cfg)
        else:
            run_pass(name, fn)

    # 4. Guardrails (anti-hallucination)
    for name, fn in GUARDRAILS:
        run_pass(name, fn)

    # 5. Model-specific adaptation (final pass)
    if model:
        run_pass("model_adapt", adapt, model)

    score_after = score_prompt(current)
    tok_stats = token_delta(prompt, current, model or "gpt-4")

    return OptimizationResult(
        original=prompt,
        optimized=current,
        model=model,
        passes=pass_results,
        score_before=score_before,
        score_after=score_after,
        token_stats=tok_stats,
    )
