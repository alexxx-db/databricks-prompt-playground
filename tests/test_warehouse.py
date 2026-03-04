"""Unit tests for server/warehouse.py — SQL warehouse query logic.

Covers:
- list_eval_tables: success, failed state raises, empty result
- get_table_columns: success, filters #-prefixed partition columns, failed state raises
- count_table_rows: success, empty result returns 0, failed state raises
- read_table_rows: success, empty result returns [], failed state raises, limit passed through
"""

import types
import pytest
from unittest.mock import patch, MagicMock

from databricks.sdk.service.sql import StatementState

from server.warehouse import (
    list_eval_tables,
    get_table_columns,
    count_table_rows,
    read_table_rows,
)


# ---------------------------------------------------------------------------
# Mock helpers
# ---------------------------------------------------------------------------

def _make_response(state=StatementState.SUCCEEDED, data_array=None, columns=None):
    """Build a mock statement execution response."""
    resp = MagicMock()
    resp.status.state = state
    resp.status.error = MagicMock()
    resp.status.error.__str__ = lambda self: "execution error"

    if data_array is not None:
        resp.result = MagicMock()
        resp.result.data_array = data_array
    else:
        resp.result = None

    if columns is not None:
        col_mocks = []
        for col_name in columns:
            c = MagicMock()
            c.name = col_name
            col_mocks.append(c)
        resp.manifest = MagicMock()
        resp.manifest.schema.columns = col_mocks

    return resp


def _mock_client(response):
    """Build a mock WorkspaceClient that returns the given response for statement execution."""
    w = MagicMock()
    w.statement_execution.execute_statement.return_value = response
    return w


# ---------------------------------------------------------------------------
# list_eval_tables
# ---------------------------------------------------------------------------

class TestListEvalTables:

    def test_success_returns_table_list(self):
        resp = _make_response(data_array=[["main", "my_table", ""], ["main", "other_table", ""]])
        with patch("server.warehouse._get_client", return_value=_mock_client(resp)):
            result = list_eval_tables("main", "eval_data", "wh-1")

        assert len(result) == 2
        assert result[0] == {"catalog": "main", "schema": "eval_data", "name": "my_table"}
        assert result[1] == {"catalog": "main", "schema": "eval_data", "name": "other_table"}

    def test_empty_result_returns_empty_list(self):
        resp = _make_response(data_array=[])
        with patch("server.warehouse._get_client", return_value=_mock_client(resp)):
            result = list_eval_tables("main", "eval_data", "wh-1")

        assert result == []

    def test_none_result_returns_empty_list(self):
        resp = _make_response()  # result=None
        with patch("server.warehouse._get_client", return_value=_mock_client(resp)):
            result = list_eval_tables("main", "eval_data", "wh-1")

        assert result == []

    def test_failed_state_raises(self):
        resp = _make_response(state=StatementState.FAILED)
        with patch("server.warehouse._get_client", return_value=_mock_client(resp)):
            with pytest.raises(RuntimeError, match="SHOW TABLES failed"):
                list_eval_tables("main", "eval_data", "wh-1")

    def test_uses_backtick_quoting_in_sql(self):
        """SQL should use backtick-quoted identifiers to handle special characters."""
        resp = _make_response(data_array=[])
        mock_w = _mock_client(resp)
        with patch("server.warehouse._get_client", return_value=mock_w):
            list_eval_tables("my-catalog", "my-schema", "wh-1")

        call_kwargs = mock_w.statement_execution.execute_statement.call_args
        sql = call_kwargs[1]["statement"] if "statement" in call_kwargs[1] else call_kwargs[0][0]
        assert "`my-catalog`" in sql
        assert "`my-schema`" in sql


# ---------------------------------------------------------------------------
# get_table_columns
# ---------------------------------------------------------------------------

class TestGetTableColumns:

    def test_success_returns_column_names(self):
        resp = _make_response(data_array=[
            ["col_a", "STRING", ""],
            ["col_b", "INT", ""],
        ])
        with patch("server.warehouse._get_client", return_value=_mock_client(resp)):
            cols = get_table_columns("main", "eval_data", "my_table", "wh-1")

        assert cols == ["col_a", "col_b"]

    def test_filters_out_hash_prefix_columns(self):
        """Columns starting with # are Spark partition markers and should be excluded."""
        resp = _make_response(data_array=[
            ["real_col", "STRING", ""],
            ["# Partition Information", "", ""],
            ["#col", "STRING", ""],
        ])
        with patch("server.warehouse._get_client", return_value=_mock_client(resp)):
            cols = get_table_columns("main", "eval_data", "my_table", "wh-1")

        assert cols == ["real_col"]
        assert all(not c.startswith("#") for c in cols)

    def test_empty_result_returns_empty_list(self):
        resp = _make_response(data_array=[])
        with patch("server.warehouse._get_client", return_value=_mock_client(resp)):
            cols = get_table_columns("main", "eval_data", "my_table", "wh-1")

        assert cols == []

    def test_none_result_returns_empty_list(self):
        resp = _make_response()
        with patch("server.warehouse._get_client", return_value=_mock_client(resp)):
            cols = get_table_columns("main", "eval_data", "my_table", "wh-1")

        assert cols == []

    def test_failed_state_raises(self):
        resp = _make_response(state=StatementState.FAILED)
        with patch("server.warehouse._get_client", return_value=_mock_client(resp)):
            with pytest.raises(RuntimeError, match="DESCRIBE failed"):
                get_table_columns("main", "eval_data", "my_table", "wh-1")

    def test_column_order_preserved(self):
        """Column order from DESCRIBE TABLE must be maintained."""
        resp = _make_response(data_array=[
            ["z_col", "STRING", ""],
            ["a_col", "STRING", ""],
            ["m_col", "STRING", ""],
        ])
        with patch("server.warehouse._get_client", return_value=_mock_client(resp)):
            cols = get_table_columns("main", "eval_data", "my_table", "wh-1")

        assert cols == ["z_col", "a_col", "m_col"]


# ---------------------------------------------------------------------------
# count_table_rows
# ---------------------------------------------------------------------------

class TestCountTableRows:

    def test_returns_row_count(self):
        resp = _make_response(data_array=[["42"]])
        with patch("server.warehouse._get_client", return_value=_mock_client(resp)):
            count = count_table_rows("main", "eval_data", "my_table", "wh-1")

        assert count == 42

    def test_none_result_returns_zero(self):
        resp = _make_response()
        with patch("server.warehouse._get_client", return_value=_mock_client(resp)):
            count = count_table_rows("main", "eval_data", "my_table", "wh-1")

        assert count == 0

    def test_empty_data_array_returns_zero(self):
        resp = _make_response(data_array=[])
        with patch("server.warehouse._get_client", return_value=_mock_client(resp)):
            count = count_table_rows("main", "eval_data", "my_table", "wh-1")

        assert count == 0

    def test_failed_state_raises(self):
        resp = _make_response(state=StatementState.FAILED)
        with patch("server.warehouse._get_client", return_value=_mock_client(resp)):
            with pytest.raises(RuntimeError, match="COUNT failed"):
                count_table_rows("main", "eval_data", "my_table", "wh-1")

    def test_large_count(self):
        resp = _make_response(data_array=[["1000000"]])
        with patch("server.warehouse._get_client", return_value=_mock_client(resp)):
            count = count_table_rows("main", "eval_data", "my_table", "wh-1")

        assert count == 1_000_000


# ---------------------------------------------------------------------------
# read_table_rows
# ---------------------------------------------------------------------------

class TestReadTableRows:

    def test_returns_rows_as_dicts(self):
        resp = _make_response(
            data_array=[["Alice", "30"], ["Bob", "25"]],
            columns=["name", "age"],
        )
        with patch("server.warehouse._get_client", return_value=_mock_client(resp)):
            rows = read_table_rows("main", "eval_data", "my_table", "wh-1")

        assert rows == [{"name": "Alice", "age": "30"}, {"name": "Bob", "age": "25"}]

    def test_empty_data_array_returns_empty_list(self):
        resp = _make_response()  # result=None
        with patch("server.warehouse._get_client", return_value=_mock_client(resp)):
            rows = read_table_rows("main", "eval_data", "my_table", "wh-1")

        assert rows == []

    def test_failed_state_raises(self):
        resp = _make_response(state=StatementState.FAILED)
        with patch("server.warehouse._get_client", return_value=_mock_client(resp)):
            with pytest.raises(RuntimeError, match="SELECT failed"):
                read_table_rows("main", "eval_data", "my_table", "wh-1")

    def test_default_limit_is_50(self):
        """Default limit should be 50 rows."""
        resp = _make_response(data_array=[], columns=[])
        mock_w = _mock_client(resp)
        with patch("server.warehouse._get_client", return_value=mock_w):
            read_table_rows("main", "eval_data", "my_table", "wh-1")

        call_kwargs = mock_w.statement_execution.execute_statement.call_args
        sql = call_kwargs[1]["statement"] if "statement" in call_kwargs[1] else call_kwargs[0][0]
        assert "LIMIT 50" in sql

    def test_custom_limit_passed_through(self):
        resp = _make_response(data_array=[], columns=[])
        mock_w = _mock_client(resp)
        with patch("server.warehouse._get_client", return_value=mock_w):
            read_table_rows("main", "eval_data", "my_table", "wh-1", limit=10)

        call_kwargs = mock_w.statement_execution.execute_statement.call_args
        sql = call_kwargs[1]["statement"] if "statement" in call_kwargs[1] else call_kwargs[0][0]
        assert "LIMIT 10" in sql

    def test_column_names_from_manifest(self):
        """Column names come from manifest.schema.columns, not from data_array."""
        resp = _make_response(
            data_array=[["val1", "val2"]],
            columns=["first_col", "second_col"],
        )
        with patch("server.warehouse._get_client", return_value=_mock_client(resp)):
            rows = read_table_rows("main", "eval_data", "my_table", "wh-1")

        assert rows[0] == {"first_col": "val1", "second_col": "val2"}

    def test_multiple_rows_all_returned(self):
        resp = _make_response(
            data_array=[["a", "1"], ["b", "2"], ["c", "3"]],
            columns=["letter", "number"],
        )
        with patch("server.warehouse._get_client", return_value=_mock_client(resp)):
            rows = read_table_rows("main", "eval_data", "my_table", "wh-1")

        assert len(rows) == 3
        assert rows[2] == {"letter": "c", "number": "3"}
