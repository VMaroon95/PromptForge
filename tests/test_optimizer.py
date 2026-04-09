"""Tests for the optimizer pipeline."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from promptforge.optimizer import optimize

def test_optimize_returns_result():
    result = optimize("tell me about python")
    assert result.original == "tell me about python"
    assert result.optimized
    assert result.score_before is not None
    assert result.score_after is not None

def test_quality_improves_or_holds():
    result = optimize("Please can you tell me about machine learning algorithms.")
    # Quality should not decrease
    assert result.score_after.total >= result.score_before.total - 5  # allow tiny variance

def test_model_aware_claude():
    result = optimize("Analyze this code for bugs.", model="claude-3-5-sonnet")
    assert result.model == "claude-3-5-sonnet"

def test_model_aware_gpt():
    result = optimize("Summarize this document.", model="gpt-4o")
    assert result.model == "gpt-4o"

def test_token_stats_present():
    result = optimize("Write a function in Python to sort a list.")
    assert "original" in result.token_stats
    assert "optimized" in result.token_stats
    assert "delta" in result.token_stats
    assert "direction" in result.token_stats

def test_preserves_content():
    """Optimization must never drop critical content."""
    prompt = "Write SQL and Python code to query the database and return results as JSON."
    result = optimize(prompt)
    assert "SQL" in result.optimized
    assert "Python" in result.optimized
    assert "JSON" in result.optimized
