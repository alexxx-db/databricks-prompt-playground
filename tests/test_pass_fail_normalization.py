"""Tests for pass/fail string normalization in evaluation scoring.

Covers:
- MLflow builtin scorer string values normalized to 1.0/0.0
- Standard pass/fail strings (true/false, yes/no, pass/fail, 1/0)
- Non-string values pass through unchanged
- Unknown strings pass through unchanged
"""

import pytest
from server.evaluation import _normalize_pass_fail, _is_pass, _PASS_STRINGS, _FAIL_STRINGS


class TestNormalizePassFail:

    @pytest.mark.parametrize("val", [
        "true", "True", "TRUE",
        "yes", "Yes", "YES",
        "pass", "Pass", "PASS",
        "1",
    ])
    def test_standard_pass_strings_normalize_to_1(self, val):
        assert _normalize_pass_fail(val) == 1.0

    @pytest.mark.parametrize("val", [
        "false", "False", "FALSE",
        "no", "No", "NO",
        "fail", "Fail", "FAIL",
        "0",
    ])
    def test_standard_fail_strings_normalize_to_0(self, val):
        assert _normalize_pass_fail(val) == 0.0

    @pytest.mark.parametrize("val", [
        "fluent", "safe", "relevant", "complete", "correct",
    ])
    def test_mlflow_builtin_pass_values_normalize_to_1(self, val):
        assert _normalize_pass_fail(val) == 1.0

    @pytest.mark.parametrize("val", [
        "not fluent", "not safe", "unsafe", "not relevant", "irrelevant",
        "not complete", "incomplete", "not correct", "incorrect",
    ])
    def test_mlflow_builtin_fail_values_normalize_to_0(self, val):
        assert _normalize_pass_fail(val) == 0.0

    def test_numeric_float_passes_through(self):
        assert _normalize_pass_fail(4.5) == 4.5

    def test_none_passes_through(self):
        assert _normalize_pass_fail(None) is None

    def test_unknown_string_passes_through(self):
        assert _normalize_pass_fail("some random text") == "some random text"

    def test_case_insensitive(self):
        assert _normalize_pass_fail("FLUENT") == 1.0
        assert _normalize_pass_fail("Unsafe") == 0.0


class TestIsPass:

    def test_bool_true(self):
        assert _is_pass(True) is True

    def test_bool_false(self):
        assert _is_pass(False) is False

    def test_int_1_passes(self):
        assert _is_pass(1) is True

    def test_int_0_fails(self):
        assert _is_pass(0) is False

    def test_float_1_passes(self):
        assert _is_pass(1.0) is True

    def test_float_below_1_fails(self):
        assert _is_pass(0.5) is False

    def test_mlflow_builtin_pass_string(self):
        assert _is_pass("fluent") is True
        assert _is_pass("safe") is True

    def test_mlflow_builtin_fail_string(self):
        assert _is_pass("not fluent") is False
        assert _is_pass("unsafe") is False

    def test_pass_and_fail_sets_are_disjoint(self):
        """Pass and fail sets must not overlap."""
        assert _PASS_STRINGS.isdisjoint(_FAIL_STRINGS)
