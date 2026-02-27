"""Tests for prompt template variable parsing."""

from server.mlflow_client import parse_template_variables


def test_single_variable():
    template = "Hello, {{name}}!"
    assert parse_template_variables(template) == ["name"]


def test_multiple_variables():
    template = "Dear {{first_name}}, your order {{order_id}} is ready."
    assert parse_template_variables(template) == ["first_name", "order_id"]


def test_preserves_order_of_appearance():
    template = "{{z}} then {{a}} then {{m}}"
    assert parse_template_variables(template) == ["z", "a", "m"]


def test_deduplicates_repeated_variables():
    template = "{{name}} said hello. {{name}} said goodbye."
    assert parse_template_variables(template) == ["name"]


def test_variables_with_spaces():
    template = "{{ greeting }} {{ name }}"
    assert parse_template_variables(template) == ["greeting", "name"]


def test_no_variables():
    template = "This prompt has no variables."
    assert parse_template_variables(template) == []


def test_empty_template():
    assert parse_template_variables("") == []


def test_multiline_template():
    template = """You are an assistant helping with {{task}}.

The user's name is {{user_name}}.
Please respond in {{language}}."""
    result = parse_template_variables(template)
    assert result == ["task", "user_name", "language"]


def test_template_with_json_like_content():
    # Curly braces in non-template context should not be matched
    template = 'Use {{variable}} and ignore {"key": "value"}'
    assert parse_template_variables(template) == ["variable"]
