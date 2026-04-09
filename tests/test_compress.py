"""Tests for compression pass."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from promptforge.compress import compress

def test_removes_filler_please():
    result = compress("Please can you write a summary of this document.")
    assert "please" not in result.lower()
    assert "summary" in result.lower()

def test_removes_i_would_like():
    result = compress("I would like you to explain machine learning.")
    assert "would like" not in result.lower()
    assert "machine learning" in result

def test_preserves_core_content():
    original = "Can you please write SQL and Python code to query the database?"
    result = compress(original)
    assert "SQL" in result
    assert "Python" in result
    assert "database" in result

def test_replaces_verbose_phrases():
    result = compress("In order to complete this task, analyze the data.")
    assert "in order to" not in result.lower()
    assert "to complete" in result.lower() or "analyze" in result.lower()

def test_no_double_spaces():
    result = compress("Please   write   this   now")
    assert "  " not in result
