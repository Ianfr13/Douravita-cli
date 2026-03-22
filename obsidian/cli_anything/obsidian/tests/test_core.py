"""Unit tests for cli-anything-obsidian.

These tests do NOT require Obsidian to be running.
All HTTP calls are mocked using unittest.mock.

Run with:
    python -m pytest cli_anything/obsidian/tests/test_core.py -v
"""

import json
import os
import sys
import pytest
from unittest.mock import patch, MagicMock, PropertyMock

# ── Helpers ───────────────────────────────────────────────────────────────────

def _resolve_cli(name: str) -> list[str]:
    """Return argv prefix to invoke a CLI by installed entry-point name.

    Tries: installed script, python -m module, then falls back to direct import.
    Prints the resolved path for debugging.

    Args:
        name: Entry-point name (e.g., 'cli-anything-obsidian').

    Returns:
        List of argv parts (e.g., ['/usr/bin/cli-anything-obsidian']).
    """
    import shutil
    path = shutil.which(name)
    if path:
        print(f"[_resolve_cli] found: {path}")
        return [path]
    # Fallback: python -m
    module = name.replace("cli-anything-", "cli_anything.").replace("-", "_")
    print(f"[_resolve_cli] fallback: python -m {module}")
    return [sys.executable, "-m", module]


# ── Backend URL & header tests ────────────────────────────────────────────────

class TestBackendURLs:
    """Test URL construction in the backend module."""

    def test_url_simple(self):
        from cli_anything.obsidian.utils.obsidian_backend import _url
        result = _url("https://127.0.0.1:27124", "/vault/")
        assert result == "https://127.0.0.1:27124/vault/"

    def test_url_trailing_slash_stripped(self):
        from cli_anything.obsidian.utils.obsidian_backend import _url
        result = _url("https://127.0.0.1:27124/", "/active/")
        assert result == "https://127.0.0.1:27124/active/"

    def test_url_with_path(self):
        from cli_anything.obsidian.utils.obsidian_backend import _url
        result = _url("https://127.0.0.1:27124", "/vault/Notes/My%20Note.md")
        assert "Notes/My%20Note.md" in result

    def test_encode_path_simple(self):
        from cli_anything.obsidian.utils.obsidian_backend import encode_path
        assert encode_path("Notes/My Note.md") == "Notes/My%20Note.md"

    def test_encode_path_no_encoding_needed(self):
        from cli_anything.obsidian.utils.obsidian_backend import encode_path
        assert encode_path("Notes/simple.md") == "Notes/simple.md"

    def test_encode_path_special_chars(self):
        from cli_anything.obsidian.utils.obsidian_backend import encode_path
        result = encode_path("Notes/Meeting (2026).md")
        assert "(" not in result or "%28" in result

    def test_encode_path_preserves_slashes(self):
        from cli_anything.obsidian.utils.obsidian_backend import encode_path
        result = encode_path("folder/subfolder/note.md")
        assert result.count("/") == 2

    def test_encode_path_unicode(self):
        from cli_anything.obsidian.utils.obsidian_backend import encode_path
        result = encode_path("Notes/Café.md")
        assert "%" in result  # Non-ASCII characters should be encoded


class TestAcceptHeaders:
    """Test Accept header selection for output formats."""

    def test_markdown_format(self):
        from cli_anything.obsidian.utils.obsidian_backend import accept_for_format
        assert accept_for_format("markdown") == "text/markdown"

    def test_json_format(self):
        from cli_anything.obsidian.utils.obsidian_backend import accept_for_format
        assert accept_for_format("json") == "application/vnd.olrapi.note+json"

    def test_map_format(self):
        from cli_anything.obsidian.utils.obsidian_backend import accept_for_format
        assert accept_for_format("map") == "application/vnd.olrapi.document-map+json"

    def test_unknown_format_defaults_to_markdown(self):
        from cli_anything.obsidian.utils.obsidian_backend import accept_for_format
        assert accept_for_format("unknown") == "text/markdown"


class TestAPIKeyResolution:
    """Test API key resolution from argument vs environment."""

    def test_explicit_key(self):
        from cli_anything.obsidian.utils.obsidian_backend import _get_api_key
        assert _get_api_key("mykey") == "mykey"

    def test_env_var_fallback(self):
        from cli_anything.obsidian.utils.obsidian_backend import _get_api_key
        with patch.dict(os.environ, {"OBSIDIAN_API_KEY": "envkey"}):
            assert _get_api_key(None) == "envkey"

    def test_missing_key_raises(self):
        from cli_anything.obsidian.utils.obsidian_backend import _get_api_key
        env = {k: v for k, v in os.environ.items() if k != "OBSIDIAN_API_KEY"}
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(RuntimeError, match="OBSIDIAN_API_KEY"):
                _get_api_key(None)

    def test_headers_include_bearer(self):
        from cli_anything.obsidian.utils.obsidian_backend import _headers
        h = _headers("testkey")
        assert h["Authorization"] == "Bearer testkey"

    def test_headers_accept(self):
        from cli_anything.obsidian.utils.obsidian_backend import _headers
        h = _headers("testkey", accept="text/markdown")
        assert h["Accept"] == "text/markdown"

    def test_headers_content_type(self):
        from cli_anything.obsidian.utils.obsidian_backend import _headers
        h = _headers("testkey", content_type="text/markdown")
        assert h["Content-Type"] == "text/markdown"

    def test_headers_extra(self):
        from cli_anything.obsidian.utils.obsidian_backend import _headers
        h = _headers("testkey", extra={"Operation": "append"})
        assert h["Operation"] == "append"


# ── Connection error handling ─────────────────────────────────────────────────

class TestConnectionErrors:
    """Test that network errors produce clear RuntimeError messages."""

    def _make_response(self, status_code=200, json_data=None, text=""):
        """Build a mock requests.Response."""
        resp = MagicMock()
        resp.status_code = status_code
        resp.content = b"content"
        resp.headers = {"Content-Type": "application/json"}
        if json_data is not None:
            resp.json.return_value = json_data
            resp.text = json.dumps(json_data)
        else:
            resp.json.side_effect = ValueError("no json")
            resp.text = text
        resp.raise_for_status = MagicMock()
        return resp

    def test_connection_error_get(self):
        import requests
        from cli_anything.obsidian.utils.obsidian_backend import api_get
        with patch("requests.get", side_effect=requests.exceptions.ConnectionError):
            with pytest.raises(RuntimeError, match="Cannot connect"):
                api_get("https://127.0.0.1:27124", "/vault/", api_key="key")

    def test_connection_error_post(self):
        import requests
        from cli_anything.obsidian.utils.obsidian_backend import api_post
        with patch("requests.post", side_effect=requests.exceptions.ConnectionError):
            with pytest.raises(RuntimeError, match="Cannot connect"):
                api_post("https://127.0.0.1:27124", "/active/", api_key="key", body="text")

    def test_connection_error_put(self):
        import requests
        from cli_anything.obsidian.utils.obsidian_backend import api_put
        with patch("requests.put", side_effect=requests.exceptions.ConnectionError):
            with pytest.raises(RuntimeError, match="Cannot connect"):
                api_put("https://127.0.0.1:27124", "/active/", api_key="key", body="text")

    def test_connection_error_delete(self):
        import requests
        from cli_anything.obsidian.utils.obsidian_backend import api_delete
        with patch("requests.delete", side_effect=requests.exceptions.ConnectionError):
            with pytest.raises(RuntimeError, match="Cannot connect"):
                api_delete("https://127.0.0.1:27124", "/active/", api_key="key")

    def test_timeout_error(self):
        import requests
        from cli_anything.obsidian.utils.obsidian_backend import api_get
        with patch("requests.get", side_effect=requests.exceptions.Timeout):
            with pytest.raises(RuntimeError, match="timed out"):
                api_get("https://127.0.0.1:27124", "/vault/", api_key="key")

    def test_is_available_false_on_connection_error(self):
        import requests
        from cli_anything.obsidian.utils.obsidian_backend import is_available
        with patch("requests.get", side_effect=requests.exceptions.ConnectionError):
            assert is_available() is False


# ── Periodic endpoint generation ──────────────────────────────────────────────

class TestPeriodicEndpoints:
    """Test periodic note endpoint path generation."""

    def test_daily_current(self):
        from cli_anything.obsidian.core.periodic import _endpoint
        assert _endpoint("daily") == "/periodic/daily/"

    def test_weekly_current(self):
        from cli_anything.obsidian.core.periodic import _endpoint
        assert _endpoint("weekly") == "/periodic/weekly/"

    def test_monthly_current(self):
        from cli_anything.obsidian.core.periodic import _endpoint
        assert _endpoint("monthly") == "/periodic/monthly/"

    def test_quarterly_current(self):
        from cli_anything.obsidian.core.periodic import _endpoint
        assert _endpoint("quarterly") == "/periodic/quarterly/"

    def test_yearly_current(self):
        from cli_anything.obsidian.core.periodic import _endpoint
        assert _endpoint("yearly") == "/periodic/yearly/"

    def test_daily_with_date(self):
        from cli_anything.obsidian.core.periodic import _endpoint
        result = _endpoint("daily", "2026-03-22")
        assert result == "/periodic/daily/2026/3/22/"

    def test_monthly_with_date(self):
        from cli_anything.obsidian.core.periodic import _endpoint
        result = _endpoint("monthly", "2026-01-01")
        assert "/periodic/monthly/2026/1/1/" == result

    def test_invalid_period_raises(self):
        from cli_anything.obsidian.core.periodic import _endpoint
        with pytest.raises(ValueError, match="Invalid period"):
            _endpoint("hourly")

    def test_invalid_date_format_raises(self):
        from cli_anything.obsidian.core.periodic import _endpoint
        with pytest.raises(ValueError, match="Invalid date"):
            _endpoint("daily", "22-03-2026")


# ── CLI argument parsing ──────────────────────────────────────────────────────

class TestCLIArgParsing:
    """Test CLI argument parsing via Click's test runner (no server needed)."""

    def setup_method(self):
        from click.testing import CliRunner
        from cli_anything.obsidian.obsidian_cli import cli
        self.runner = CliRunner()
        self.cli = cli

    def test_help_shows(self):
        result = self.runner.invoke(self.cli, ["--help"])
        assert result.exit_code == 0
        assert "vault" in result.output.lower()

    def test_status_help(self):
        result = self.runner.invoke(self.cli, ["status", "--help"])
        assert result.exit_code == 0

    def test_vault_help(self):
        result = self.runner.invoke(self.cli, ["vault", "--help"])
        assert result.exit_code == 0

    def test_active_help(self):
        result = self.runner.invoke(self.cli, ["active", "--help"])
        assert result.exit_code == 0

    def test_periodic_help(self):
        result = self.runner.invoke(self.cli, ["periodic", "--help"])
        assert result.exit_code == 0

    def test_search_help(self):
        result = self.runner.invoke(self.cli, ["search", "--help"])
        assert result.exit_code == 0

    def test_commands_help(self):
        result = self.runner.invoke(self.cli, ["commands", "--help"])
        assert result.exit_code == 0

    def test_tags_help(self):
        result = self.runner.invoke(self.cli, ["tags", "--help"])
        assert result.exit_code == 0

    def test_open_help(self):
        result = self.runner.invoke(self.cli, ["open", "--help"])
        assert result.exit_code == 0

    def test_vault_get_requires_file(self):
        result = self.runner.invoke(self.cli, ["vault", "get"])
        assert result.exit_code != 0

    def test_periodic_get_requires_valid_period(self):
        result = self.runner.invoke(self.cli,
                                    ["--api-key", "key", "periodic", "get", "hourly"])
        assert result.exit_code != 0

    def test_vault_patch_requires_op(self):
        result = self.runner.invoke(self.cli,
                                    ["--api-key", "key", "vault", "patch",
                                     "file.md", "content",
                                     "--type", "heading", "--target", "Tasks"])
        assert result.exit_code != 0

    def test_json_flag_sets_output_mode(self):
        """--json flag should be accepted without error."""
        result = self.runner.invoke(self.cli, ["--json", "--help"])
        assert result.exit_code == 0

    def test_host_flag_accepted(self):
        result = self.runner.invoke(
            self.cli, ["--host", "http://127.0.0.1:27123", "--help"]
        )
        assert result.exit_code == 0

    def test_search_simple_requires_query(self):
        result = self.runner.invoke(self.cli, ["search", "simple"])
        assert result.exit_code != 0


# ── Output formatting tests ───────────────────────────────────────────────────

class TestOutputFormatting:
    """Test human-readable output helpers."""

    def test_print_dict_flat(self, capsys):
        from cli_anything.obsidian.obsidian_cli import _print_dict
        import click
        _print_dict({"key": "value", "num": 42})
        captured = capsys.readouterr()
        assert "key" in captured.out
        assert "value" in captured.out

    def test_print_list_simple(self, capsys):
        from cli_anything.obsidian.obsidian_cli import _print_list
        _print_list(["item1", "item2"])
        captured = capsys.readouterr()
        assert "item1" in captured.out
        assert "item2" in captured.out

    def test_output_json_mode(self, capsys):
        import cli_anything.obsidian.obsidian_cli as cli_mod
        original = cli_mod._json_output
        cli_mod._json_output = True
        try:
            cli_mod.output({"status": "ok"})
            captured = capsys.readouterr()
            data = json.loads(captured.out)
            assert data["status"] == "ok"
        finally:
            cli_mod._json_output = original

    def test_output_human_mode_with_message(self, capsys):
        import cli_anything.obsidian.obsidian_cli as cli_mod
        original = cli_mod._json_output
        cli_mod._json_output = False
        try:
            cli_mod.output({"x": 1}, message="Hello")
            captured = capsys.readouterr()
            assert "Hello" in captured.out
        finally:
            cli_mod._json_output = original


# ── UI module tests ───────────────────────────────────────────────────────────

class TestUIModule:
    """Test open_file function in the ui core module."""

    def test_open_file_builds_correct_endpoint(self):
        """open_file should POST to /open/{encoded_path}."""
        import requests
        from unittest.mock import patch, MagicMock

        mock_resp = MagicMock()
        mock_resp.status_code = 204
        mock_resp.content = b""
        mock_resp.raise_for_status = MagicMock()

        with patch("requests.post", return_value=mock_resp) as mock_post:
            from cli_anything.obsidian.core.ui import open_file
            open_file("https://127.0.0.1:27124", "testkey", "Notes/My Note.md")
            call_url = mock_post.call_args[0][0]
            assert "/open/Notes/My%20Note.md" in call_url

    def test_open_file_with_new_leaf(self):
        """open_file with new_leaf=True should add newLeaf query param."""
        import requests
        from unittest.mock import patch, MagicMock

        mock_resp = MagicMock()
        mock_resp.status_code = 204
        mock_resp.content = b""
        mock_resp.raise_for_status = MagicMock()

        with patch("requests.post", return_value=mock_resp) as mock_post:
            from cli_anything.obsidian.core.ui import open_file
            open_file("https://127.0.0.1:27124", "testkey", "note.md", new_leaf=True)
            call_kwargs = mock_post.call_args[1]
            assert call_kwargs.get("params") == {"newLeaf": "true"}

    def test_open_file_without_new_leaf(self):
        """open_file with new_leaf=False should not send newLeaf param."""
        import requests
        from unittest.mock import patch, MagicMock

        mock_resp = MagicMock()
        mock_resp.status_code = 204
        mock_resp.content = b""
        mock_resp.raise_for_status = MagicMock()

        with patch("requests.post", return_value=mock_resp) as mock_post:
            from cli_anything.obsidian.core.ui import open_file
            open_file("https://127.0.0.1:27124", "testkey", "note.md", new_leaf=False)
            call_kwargs = mock_post.call_args[1]
            assert call_kwargs.get("params") is None


# ── Patch header tests ────────────────────────────────────────────────────────

class TestPatchHeaders:
    """Test PATCH operation header construction."""

    def test_patch_headers_include_operation(self):
        """api_patch should set the Operation header correctly."""
        import requests
        from unittest.mock import patch, MagicMock

        mock_resp = MagicMock()
        mock_resp.status_code = 204
        mock_resp.content = b""
        mock_resp.raise_for_status = MagicMock()

        with patch("requests.patch", return_value=mock_resp) as mock_patch:
            from cli_anything.obsidian.utils.obsidian_backend import api_patch
            api_patch(
                "https://127.0.0.1:27124", "/active/",
                api_key="key", body="content",
                operation="append", target_type="heading", target="Tasks",
            )
            sent_headers = mock_patch.call_args[1]["headers"]
            assert sent_headers["Operation"] == "append"
            assert sent_headers["Target-Type"] == "heading"

    def test_patch_create_if_missing_header(self):
        """api_patch should set Create-Target-If-Missing header."""
        import requests
        from unittest.mock import patch, MagicMock

        mock_resp = MagicMock()
        mock_resp.status_code = 204
        mock_resp.content = b""
        mock_resp.raise_for_status = MagicMock()

        with patch("requests.patch", return_value=mock_resp) as mock_patch:
            from cli_anything.obsidian.utils.obsidian_backend import api_patch
            api_patch(
                "https://127.0.0.1:27124", "/active/",
                api_key="key", body="content",
                operation="append", target_type="heading", target="NewSection",
                create_if_missing=True,
            )
            sent_headers = mock_patch.call_args[1]["headers"]
            assert sent_headers["Create-Target-If-Missing"] == "true"


# ── Search validation tests ───────────────────────────────────────────────────

class TestSearchValidation:
    """Test input validation in search module."""

    def test_simple_empty_query_raises(self):
        from cli_anything.obsidian.core.search import simple
        with pytest.raises(ValueError, match="empty"):
            simple("https://127.0.0.1:27124", "key", "")

    def test_simple_whitespace_query_raises(self):
        from cli_anything.obsidian.core.search import simple
        with pytest.raises(ValueError, match="empty"):
            simple("https://127.0.0.1:27124", "key", "   ")

    def test_dql_empty_query_raises(self):
        from cli_anything.obsidian.core.search import dql
        with pytest.raises(ValueError, match="empty"):
            dql("https://127.0.0.1:27124", "key", "")

    def test_jsonlogic_empty_string_raises(self):
        from cli_anything.obsidian.core.search import jsonlogic
        with pytest.raises(ValueError, match="empty"):
            jsonlogic("https://127.0.0.1:27124", "key", "   ")

    def test_jsonlogic_invalid_json_raises(self):
        from cli_anything.obsidian.core.search import jsonlogic
        with pytest.raises(ValueError, match="Invalid JSON"):
            jsonlogic("https://127.0.0.1:27124", "key", "{not valid json}")

    def test_jsonlogic_empty_dict_raises(self):
        from cli_anything.obsidian.core.search import jsonlogic
        with pytest.raises(ValueError, match="empty"):
            jsonlogic("https://127.0.0.1:27124", "key", {})

    def test_to_list_handles_list(self):
        from cli_anything.obsidian.core.search import _to_list
        assert _to_list([1, 2, 3]) == [1, 2, 3]

    def test_to_list_handles_dict_with_results(self):
        from cli_anything.obsidian.core.search import _to_list
        assert _to_list({"results": ["a", "b"]}) == ["a", "b"]

    def test_to_list_handles_empty_dict(self):
        from cli_anything.obsidian.core.search import _to_list
        assert _to_list({}) == []

    def test_to_list_handles_unexpected_type(self):
        from cli_anything.obsidian.core.search import _to_list
        assert _to_list("unexpected") == []
        assert _to_list(None) == []


# ── handle_error decorator tests ─────────────────────────────────────────────

class TestHandleErrorDecorator:
    """Test that handle_error uses functools.wraps correctly."""

    def test_preserves_function_name(self):
        from cli_anything.obsidian.obsidian_cli import handle_error

        @handle_error
        def my_function():
            """My docstring."""
            pass

        assert my_function.__name__ == "my_function"

    def test_preserves_docstring(self):
        from cli_anything.obsidian.obsidian_cli import handle_error

        @handle_error
        def my_function():
            """My docstring."""
            pass

        assert my_function.__doc__ == "My docstring."

    def test_preserves_qualname(self):
        from cli_anything.obsidian.obsidian_cli import handle_error

        @handle_error
        def my_function():
            pass

        assert "my_function" in my_function.__qualname__

    def test_preserves_wrapped_attribute(self):
        from cli_anything.obsidian.obsidian_cli import handle_error

        @handle_error
        def my_function():
            pass

        assert hasattr(my_function, "__wrapped__")
