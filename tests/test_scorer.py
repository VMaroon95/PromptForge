"""Tests for quality scorer."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from promptforge.scorer import score_prompt

def test_vague_prompt_scores_low():
    score = score_prompt("tell me stuff")
    assert score.total < 40, f"Vague prompt should score low, got {score.total}"

def test_detailed_prompt_scores_higher():
    prompt = (
        "You are an expert Python developer. "
        "Analyze the following code for security vulnerabilities. "
        "Focus only on SQL injection and XSS risks. "
        "Return a JSON array with fields: issue, severity, line, fix. "
        "If you are unsure about a finding, say so rather than guessing."
    )
    score = score_prompt(prompt)
    assert score.total >= 60, f"Detailed prompt should score higher, got {score.total}"

def test_score_dimensions_sum():
    score = score_prompt("Write a blog post about AI.")
    assert score.total == score.clarity + score.specificity + score.structure + score.grounding

def test_scores_bounded():
    import random
    prompts = [
        "hi",
        "Write a detailed technical analysis of quantum computing advances in 2025, "
        "citing peer-reviewed sources. Format as markdown with headers. Be concise.",
        "You are a legal analyst. Based on the attached contract, identify clauses "
        "that conflict with GDPR Article 17. Return a numbered list. If uncertain, say so.",
    ]
    for p in prompts:
        s = score_prompt(p)
        assert 0 <= s.clarity <= 25
        assert 0 <= s.specificity <= 25
        assert 0 <= s.structure <= 25
        assert 0 <= s.grounding <= 25
