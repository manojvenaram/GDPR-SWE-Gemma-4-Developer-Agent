"""Unit tests for FastAPI parameter extraction."""

import sys
import os

# Add repo root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.params import QueryParam, extract_query_value


def test_required_param():
    p = QueryParam(default=...)
    assert p.is_required() is True
    try:
        p.get_default()
        assert False, "Should raise ValueError for required param"
    except ValueError:
        pass


def test_optional_none_default():
    # This test exposes the bug in fastapi/params.py
    p = QueryParam(default=None)
    assert p.is_required() is False
    val = extract_query_value(p, raw_value=None)
    assert val is None, f"Expected None default value, got: {val}"


def test_explicit_value():
    p = QueryParam(default="default_val")
    val = extract_query_value(p, raw_value="hello")
    assert val == "hello"


if __name__ == "__main__":
    print("Running tests...")
    test_required_param()
    test_explicit_value()
    try:
        test_optional_none_default()
        print("All tests PASSED!")
    except AssertionError as e:
        print(f"TEST FAILED: {e}")
        sys.exit(1)
