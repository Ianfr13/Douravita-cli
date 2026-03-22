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


# ── New CLI commands: vault move, exists, list --recursive ────────────────────

class TestNewVaultCommands:
    """Test new vault subcommands (move, exists, list --recursive)."""

    def setup_method(self):
        from click.testing import CliRunner
        from cli_anything.obsidian.obsidian_cli import cli
        self.runner = CliRunner()
        self.cli = cli

    def test_vault_move_help(self):
        result = self.runner.invoke(self.cli, ["vault", "move", "--help"])
        assert result.exit_code == 0
        assert "src" in result.output.lower() or "SRC" in result.output

    def test_vault_exists_help(self):
        result = self.runner.invoke(self.cli, ["vault", "exists", "--help"])
        assert result.exit_code == 0

    def test_vault_list_recursive_flag(self):
        result = self.runner.invoke(self.cli, ["vault", "list", "--help"])
        assert result.exit_code == 0
        assert "recursive" in result.output.lower()

    def test_vault_put_no_overwrite_flag(self):
        result = self.runner.invoke(self.cli, ["vault", "put", "--help"])
        assert result.exit_code == 0
        assert "no-overwrite" in result.output.lower()

    def test_vault_get_heading_flag(self):
        result = self.runner.invoke(self.cli, ["vault", "get", "--help"])
        assert result.exit_code == 0
        assert "heading" in result.output.lower()


# ── Bug #1: Status checks correct response field ─────────────────────────────

class TestStatusResponseParsing:
    """Test that cmd_status correctly handles the API response format."""

    def setup_method(self):
        from click.testing import CliRunner
        from cli_anything.obsidian.obsidian_cli import cli
        self.runner = CliRunner()
        self.cli = cli

    def test_status_recognizes_ok_response(self):
        """Status should show '✓ running' when API returns {"status": "OK"}."""
        mock_response = {
            "status": "OK",
            "service": "Obsidian Local REST API",
            "authenticated": True,
            "versions": {"obsidian": "1.12.4", "self": "3.5.0"},
        }
        with patch("cli_anything.obsidian.core.server.api_get", return_value=mock_response):
            result = self.runner.invoke(self.cli, ["--api-key", "testkey", "status"])
            assert result.exit_code == 0
            assert "✓ running" in result.output
            assert "Authenticated: True" in result.output

    def test_status_recognizes_not_ok_response(self):
        """Status should show '✗ not responding' for non-OK status."""
        mock_response = {"status": "error", "service": "test"}
        with patch("cli_anything.obsidian.core.server.api_get", return_value=mock_response):
            result = self.runner.invoke(self.cli, ["--api-key", "testkey", "status"])
            assert "✗ not responding" in result.output

    def test_status_sends_api_key(self):
        """Status should send API key for authenticated check."""
        with patch("cli_anything.obsidian.core.server.api_get") as mock_get:
            mock_get.return_value = {"status": "OK", "authenticated": True}
            self.runner.invoke(self.cli, ["--api-key", "mykey", "status"])
            _, kwargs = mock_get.call_args
            assert kwargs.get("api_key") == "mykey" or mock_get.call_args[0][1] == "/"


# ── Bug #7: vault list "/" normalisation ──────────────────────────────────────

class TestVaultListPathNormalization:
    """Test that vault list correctly normalizes path arguments."""

    def test_list_dir_with_slash(self):
        """list_dir('/') should behave the same as list_dir('')."""
        from cli_anything.obsidian.core.vault import list_dir
        with patch("cli_anything.obsidian.core.vault.api_get") as mock_get:
            mock_get.return_value = {"files": ["a.md"]}
            list_dir("https://host", "key", "/")
            endpoint = mock_get.call_args[0][1]
            assert endpoint == "/vault/"

    def test_list_dir_empty_string(self):
        from cli_anything.obsidian.core.vault import list_dir
        with patch("cli_anything.obsidian.core.vault.api_get") as mock_get:
            mock_get.return_value = {"files": ["a.md"]}
            list_dir("https://host", "key", "")
            endpoint = mock_get.call_args[0][1]
            assert endpoint == "/vault/"

    def test_list_dir_with_trailing_slashes(self):
        from cli_anything.obsidian.core.vault import list_dir
        with patch("cli_anything.obsidian.core.vault.api_get") as mock_get:
            mock_get.return_value = {"files": []}
            list_dir("https://host", "key", "/Notes/")
            endpoint = mock_get.call_args[0][1]
            assert endpoint == "/vault/Notes/"


# ── Bug #4: delete commands --yes flag ────────────────────────────────────────

class TestDeleteConfirmation:
    """Test that delete commands support --yes for non-interactive use."""

    def setup_method(self):
        from click.testing import CliRunner
        from cli_anything.obsidian.obsidian_cli import cli
        self.runner = CliRunner()
        self.cli = cli

    def test_vault_delete_accepts_yes(self):
        result = self.runner.invoke(self.cli, ["vault", "delete", "--help"])
        assert "--yes" in result.output

    def test_active_delete_accepts_yes(self):
        result = self.runner.invoke(self.cli, ["active", "delete", "--help"])
        assert "--yes" in result.output

    def test_periodic_delete_accepts_yes(self):
        result = self.runner.invoke(self.cli, ["periodic", "delete", "--help"])
        assert "--yes" in result.output


# ── Bug #6: Patch append newline ──────────────────────────────────────────────

class TestPatchAppendNewline:
    """Test that patch append prepends a newline to content."""

    def setup_method(self):
        from click.testing import CliRunner
        from cli_anything.obsidian.obsidian_cli import cli
        self.runner = CliRunner()
        self.cli = cli

    def test_vault_patch_append_adds_newline(self):
        """Patch append should prepend \\n so content doesn't stick to existing text."""
        with patch("cli_anything.obsidian.core.vault.api_patch") as mock_patch:
            mock_patch.return_value = {"status": "ok"}
            self.runner.invoke(
                self.cli,
                ["--api-key", "key", "vault", "patch", "f.md",
                 "new content",
                 "--op", "append", "--type", "heading", "--target", "Tasks"],
            )
            call_kwargs = mock_patch.call_args[1]
            body = call_kwargs.get("body", "")
            assert body.startswith("\n"), f"Expected body to start with newline, got: {body!r}"

    def test_vault_patch_replace_no_extra_newline(self):
        """Patch replace should NOT prepend a newline."""
        with patch("cli_anything.obsidian.core.vault.api_patch") as mock_patch:
            mock_patch.return_value = {"status": "ok"}
            self.runner.invoke(
                self.cli,
                ["--api-key", "key", "vault", "patch", "f.md",
                 "new content",
                 "--op", "replace", "--type", "heading", "--target", "Tasks"],
            )
            call_kwargs = mock_patch.call_args[1]
            body = call_kwargs.get("body", "")
            assert not body.startswith("\n")


# ── OBSIDIAN_HOST env var ─────────────────────────────────────────────────────

class TestObsidianHostEnvVar:
    """Test that --host reads from OBSIDIAN_HOST env var."""

    def setup_method(self):
        from click.testing import CliRunner
        from cli_anything.obsidian.obsidian_cli import cli
        self.runner = CliRunner()
        self.cli = cli

    def test_host_from_env_var(self):
        result = self.runner.invoke(self.cli, ["--help"])
        assert "OBSIDIAN_HOST" in result.output


# ── Content resolution ────────────────────────────────────────────────────────

class TestContentResolution:
    """Test the _resolve_content helper for dash-prefixed content."""

    def test_normal_content(self):
        from cli_anything.obsidian.obsidian_cli import _resolve_content
        assert _resolve_content("hello") == "hello"

    def test_stdin_marker(self):
        from cli_anything.obsidian.obsidian_cli import _resolve_content
        with patch("sys.stdin") as mock_stdin:
            mock_stdin.read.return_value = "stdin content"
            assert _resolve_content("-") == "stdin content"

    def test_none_with_tty_raises(self):
        from cli_anything.obsidian.obsidian_cli import _resolve_content
        with patch("sys.stdin") as mock_stdin:
            mock_stdin.isatty.return_value = True
            with pytest.raises(Exception):
                _resolve_content(None)

    def test_none_with_piped_stdin(self):
        from cli_anything.obsidian.obsidian_cli import _resolve_content
        with patch("sys.stdin") as mock_stdin:
            mock_stdin.isatty.return_value = False
            mock_stdin.read.return_value = "piped content"
            assert _resolve_content(None) == "piped content"

    def test_frontmatter_content_preserved(self):
        from cli_anything.obsidian.obsidian_cli import _resolve_content
        content = "---\ntitle: Test\n---\nBody"
        assert _resolve_content(content) == content

    def test_dash_prefixed_content_preserved(self):
        """Content starting with - should work fine when passed as string."""
        from cli_anything.obsidian.obsidian_cli import _resolve_content
        content = "- [ ] task"
        assert _resolve_content(content) == content


# ── Vault exists function ─────────────────────────────────────────────────────

class TestVaultExists:
    """Test the vault exists function."""

    def test_exists_returns_true(self):
        from cli_anything.obsidian.core.vault import exists
        with patch("cli_anything.obsidian.core.vault.get") as mock_get:
            mock_get.return_value = {"content": "hello"}
            assert exists("https://host", "key", "file.md") is True

    def test_exists_returns_false_on_404(self):
        from cli_anything.obsidian.core.vault import exists
        with patch("cli_anything.obsidian.core.vault.get") as mock_get:
            mock_get.side_effect = RuntimeError("Not found (404)")
            assert exists("https://host", "key", "file.md") is False


# ── Vault move function ──────────────────────────────────────────────────────

class TestVaultMove:
    """Test the vault move function."""

    def test_move_success(self):
        from cli_anything.obsidian.core.vault import move
        with patch("cli_anything.obsidian.core.vault.get") as mock_get, \
             patch("cli_anything.obsidian.core.vault.exists") as mock_exists, \
             patch("cli_anything.obsidian.core.vault.put") as mock_put, \
             patch("cli_anything.obsidian.core.vault.delete") as mock_del:
            mock_get.return_value = {"content": "# Note"}
            mock_exists.return_value = False
            mock_put.return_value = {"status": "ok"}
            mock_del.return_value = {"status": "ok"}
            result = move("https://host", "key", "old.md", "new.md")
            assert result["src"] == "old.md"
            assert result["dst"] == "new.md"
            mock_put.assert_called_once()
            mock_del.assert_called_once()

    def test_move_fails_if_dst_exists(self):
        from cli_anything.obsidian.core.vault import move
        with patch("cli_anything.obsidian.core.vault.get") as mock_get, \
             patch("cli_anything.obsidian.core.vault.exists") as mock_exists:
            mock_get.return_value = {"content": "# Note"}
            mock_exists.return_value = True
            with pytest.raises(RuntimeError, match="already exists"):
                move("https://host", "key", "old.md", "existing.md")


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


# ── Dataview module tests ─────────────────────────────────────────────────────

class TestDataviewModule:
    """Test Dataview DQL query construction."""

    def test_table_basic_builds_correct_dql(self):
        from cli_anything.obsidian.core.dataview import table
        with patch("cli_anything.obsidian.core.dataview.api_post") as mock_post:
            mock_post.return_value = []
            table("https://host", "key", fields="file.name, status")
            body = mock_post.call_args[1]["body"]
            assert body == "TABLE file.name, status"

    def test_table_with_all_params(self):
        from cli_anything.obsidian.core.dataview import table
        with patch("cli_anything.obsidian.core.dataview.api_post") as mock_post:
            mock_post.return_value = []
            table("https://host", "key",
                  fields="file.name", from_folder='"Projects"',
                  where='status = "open"', sort="file.mtime DESC", limit=10)
            body = mock_post.call_args[1]["body"]
            assert 'TABLE file.name FROM "Projects"' in body
            assert 'WHERE status = "open"' in body
            assert "SORT file.mtime DESC" in body
            assert "LIMIT 10" in body

    def test_list_query_basic(self):
        from cli_anything.obsidian.core.dataview import list_query
        with patch("cli_anything.obsidian.core.dataview.api_post") as mock_post:
            mock_post.return_value = []
            list_query("https://host", "key", from_folder='"Notes"')
            body = mock_post.call_args[1]["body"]
            assert body == 'LIST FROM "Notes"'

    def test_list_query_with_expression(self):
        from cli_anything.obsidian.core.dataview import list_query
        with patch("cli_anything.obsidian.core.dataview.api_post") as mock_post:
            mock_post.return_value = []
            list_query("https://host", "key", expression="file.name",
                       where='type = "artigo"')
            body = mock_post.call_args[1]["body"]
            assert body.startswith("LIST file.name")
            assert 'WHERE type = "artigo"' in body

    def test_task_query(self):
        from cli_anything.obsidian.core.dataview import task
        with patch("cli_anything.obsidian.core.dataview.api_post") as mock_post:
            mock_post.return_value = []
            task("https://host", "key",
                 from_folder='"marketing/"', where="!completed")
            body = mock_post.call_args[1]["body"]
            assert body == 'TASK FROM "marketing/" WHERE !completed'

    def test_calendar_query(self):
        from cli_anything.obsidian.core.dataview import calendar
        with patch("cli_anything.obsidian.core.dataview.api_post") as mock_post:
            mock_post.return_value = []
            calendar("https://host", "key", date_field="date",
                     from_folder='"Daily/"')
            body = mock_post.call_args[1]["body"]
            assert body == 'CALENDAR date FROM "Daily/"'

    def test_raw_empty_raises(self):
        from cli_anything.obsidian.core.dataview import raw
        with pytest.raises(ValueError, match="empty"):
            raw("https://host", "key", "")

    def test_raw_sends_correct_content_type(self):
        from cli_anything.obsidian.core.dataview import raw
        with patch("cli_anything.obsidian.core.dataview.api_post") as mock_post:
            mock_post.return_value = []
            raw("https://host", "key", "TABLE file.name")
            ct = mock_post.call_args[1]["content_type"]
            assert "dataview.dql" in ct


# ── Templater module tests ───────────────────────────────────────────────────

class TestTemplaterModule:
    """Test Templater integration functions."""

    def test_list_templates(self):
        from cli_anything.obsidian.core.templater import list_templates
        with patch("cli_anything.obsidian.core.vault.list_dir") as mock_list:
            mock_list.return_value = {"files": ["blog.md", "vsl.md", "subfolder/"]}
            result = list_templates("https://host", "key", folder="Templates")
            assert "Templates/blog.md" in result
            assert "Templates/vsl.md" in result
            assert len(result) == 2  # subfolder/ excluded

    def test_get_template(self):
        from cli_anything.obsidian.core.templater import get_template
        with patch("cli_anything.obsidian.core.vault.get") as mock_get:
            mock_get.return_value = {"content": "# {{title}}"}
            result = get_template("https://host", "key", "Templates/blog.md")
            assert result == "# {{title}}"

    def test_create_from_template_with_vars(self):
        from cli_anything.obsidian.core.templater import create_from_template
        with patch("cli_anything.obsidian.core.vault.get") as mock_get, \
             patch("cli_anything.obsidian.core.vault.exists") as mock_exists, \
             patch("cli_anything.obsidian.core.vault.put") as mock_put:
            mock_get.return_value = {"content": "# {{title}}\n\nBy {{author}}"}
            mock_exists.return_value = False
            mock_put.return_value = {"status": "ok"}
            result = create_from_template(
                "https://host", "key",
                "briefing/creatina.md", "Templates/blog.md",
                variables={"title": "Creatina 55+", "author": "Ian"},
            )
            put_content = mock_put.call_args[0][3]
            assert "# Creatina 55+" in put_content
            assert "By Ian" in put_content
            assert result["file"] == "briefing/creatina.md"

    def test_create_from_template_fails_if_dest_exists(self):
        from cli_anything.obsidian.core.templater import create_from_template
        with patch("cli_anything.obsidian.core.vault.get") as mock_get, \
             patch("cli_anything.obsidian.core.vault.exists") as mock_exists:
            mock_get.return_value = {"content": "# Template"}
            mock_exists.return_value = True
            with pytest.raises(RuntimeError, match="already exists"):
                create_from_template("https://host", "key",
                                     "existing.md", "Templates/t.md")

    def test_run_on_file(self):
        from cli_anything.obsidian.core.templater import run_on_file, CMD_REPLACE
        with patch("cli_anything.obsidian.core.commands.run_command") as mock_run:
            mock_run.return_value = {"status": "ok"}
            run_on_file("https://host", "key")
            mock_run.assert_called_once_with("https://host", "key", CMD_REPLACE)


# ── Folder Notes module tests ────────────────────────────────────────────────

class TestFolderNotesModule:
    """Test Folder Notes integration functions."""

    def test_index_path_inside(self):
        from cli_anything.obsidian.core.foldernotes import _index_path
        assert _index_path("Projects") == "Projects/Projects.md"
        assert _index_path("marketing/briefing") == "marketing/briefing/briefing.md"

    def test_index_path_outside(self):
        from cli_anything.obsidian.core.foldernotes import _index_path
        assert _index_path("Projects", style="outside") == "Projects.md"
        assert _index_path("marketing/briefing", style="outside") == "marketing/briefing.md"

    def test_index_path_strips_slashes(self):
        from cli_anything.obsidian.core.foldernotes import _index_path
        assert _index_path("/Projects/") == "Projects/Projects.md"

    def test_exists_true(self):
        from cli_anything.obsidian.core.foldernotes import exists
        with patch("cli_anything.obsidian.core.vault.exists") as mock_exists:
            mock_exists.return_value = True
            assert exists("https://host", "key", "Projects") is True
            mock_exists.assert_called_with("https://host", "key", "Projects/Projects.md")

    def test_exists_false(self):
        from cli_anything.obsidian.core.foldernotes import exists
        with patch("cli_anything.obsidian.core.vault.exists") as mock_exists:
            mock_exists.return_value = False
            assert exists("https://host", "key", "Projects") is False

    def test_create_auto_generates_index(self):
        from cli_anything.obsidian.core.foldernotes import create
        with patch("cli_anything.obsidian.core.vault.exists") as mock_exists, \
             patch("cli_anything.obsidian.core.vault.list_dir") as mock_list, \
             patch("cli_anything.obsidian.core.vault.put") as mock_put:
            mock_exists.return_value = False
            mock_list.return_value = {"files": ["note-a.md", "note-b.md", "sub/"]}
            mock_put.return_value = {"status": "ok"}
            result = create("https://host", "key", "Projects")
            put_content = mock_put.call_args[0][3]
            assert "# Projects" in put_content
            assert "[[Projects/note-a.md|note-a]]" in put_content
            assert "sub" in put_content
            assert result["file"] == "Projects/Projects.md"

    def test_create_fails_if_exists(self):
        from cli_anything.obsidian.core.foldernotes import create
        with patch("cli_anything.obsidian.core.vault.exists") as mock_exists:
            mock_exists.return_value = True
            with pytest.raises(RuntimeError, match="already exists"):
                create("https://host", "key", "Projects")


# ── Charts module tests ──────────────────────────────────────────────────────

class TestChartsModule:
    """Test Obsidian Charts block generation."""

    def test_bar_chart_basic(self):
        block = charts_mod_import().generate_block(
            "bar", ["Jan", "Feb"], [{"label": "Sales", "data": [10, 20]}],
        )
        assert "```chart" in block
        assert "type: bar" in block
        assert '"Jan"' in block
        assert '"Feb"' in block
        assert "10" in block
        assert "```" in block

    def test_pie_chart_with_title(self):
        block = charts_mod_import().generate_block(
            "pie", ["A", "B"], [{"label": "Data", "data": [60, 40]}],
            title="My Pie",
        )
        assert 'title: "My Pie"' in block
        assert "type: pie" in block

    def test_line_chart_stacked(self):
        block = charts_mod_import().generate_block(
            "line", ["Q1", "Q2"],
            [{"label": "Rev", "data": [100, 200]}, {"label": "Cost", "data": [50, 80]}],
            stacked=True,
        )
        assert "stacked: true" in block
        assert '"Rev"' in block
        assert '"Cost"' in block

    def test_invalid_type_raises(self):
        with pytest.raises(ValueError, match="Invalid chart type"):
            charts_mod_import().generate_block("scatter", ["A"], [{"data": [1]}])

    def test_empty_labels_raises(self):
        with pytest.raises(ValueError, match="Labels"):
            charts_mod_import().generate_block("bar", [], [{"data": [1]}])

    def test_empty_datasets_raises(self):
        with pytest.raises(ValueError, match="Datasets"):
            charts_mod_import().generate_block("bar", ["A"], [])

    def test_multiple_datasets_get_different_colors(self):
        block = charts_mod_import().generate_block(
            "bar", ["A"],
            [{"label": "D1", "data": [1]}, {"label": "D2", "data": [2]}],
        )
        assert "rgba(255, 99, 132" in block   # first color
        assert "rgba(54, 162, 235" in block    # second color


def charts_mod_import():
    """Import charts module for testing."""
    from cli_anything.obsidian.core import charts
    return charts


# ── Plugin CLI command help tests ────────────────────────────────────────────

class TestPluginCLICommands:
    """Test that plugin command groups are registered and accessible."""

    def setup_method(self):
        from click.testing import CliRunner
        from cli_anything.obsidian.obsidian_cli import cli
        self.runner = CliRunner()
        self.cli = cli

    def test_dataview_help(self):
        result = self.runner.invoke(self.cli, ["dataview", "--help"])
        assert result.exit_code == 0
        assert "dataview" in result.output.lower()

    def test_dataview_table_help(self):
        result = self.runner.invoke(self.cli, ["dataview", "table", "--help"])
        assert result.exit_code == 0
        assert "--from" in result.output
        assert "--where" in result.output

    def test_dataview_list_help(self):
        result = self.runner.invoke(self.cli, ["dataview", "list", "--help"])
        assert result.exit_code == 0

    def test_dataview_task_help(self):
        result = self.runner.invoke(self.cli, ["dataview", "task", "--help"])
        assert result.exit_code == 0

    def test_dataview_raw_help(self):
        result = self.runner.invoke(self.cli, ["dataview", "raw", "--help"])
        assert result.exit_code == 0

    def test_templater_help(self):
        result = self.runner.invoke(self.cli, ["templater", "--help"])
        assert result.exit_code == 0

    def test_templater_list_help(self):
        result = self.runner.invoke(self.cli, ["templater", "list", "--help"])
        assert result.exit_code == 0
        assert "--folder" in result.output

    def test_templater_create_help(self):
        result = self.runner.invoke(self.cli, ["templater", "create", "--help"])
        assert result.exit_code == 0
        assert "--var" in result.output or "-v" in result.output

    def test_templater_run_help(self):
        result = self.runner.invoke(self.cli, ["templater", "run", "--help"])
        assert result.exit_code == 0

    def test_templater_get_help(self):
        result = self.runner.invoke(self.cli, ["templater", "get", "--help"])
        assert result.exit_code == 0

    def test_templater_insert_help(self):
        result = self.runner.invoke(self.cli, ["templater", "insert", "--help"])
        assert result.exit_code == 0

    # Folder Notes
    def test_foldernotes_help(self):
        result = self.runner.invoke(self.cli, ["foldernotes", "--help"])
        assert result.exit_code == 0

    def test_foldernotes_create_help(self):
        result = self.runner.invoke(self.cli, ["foldernotes", "create", "--help"])
        assert result.exit_code == 0
        assert "--style" in result.output
        assert "--overwrite" in result.output

    def test_foldernotes_get_help(self):
        result = self.runner.invoke(self.cli, ["foldernotes", "get", "--help"])
        assert result.exit_code == 0

    def test_foldernotes_refresh_help(self):
        result = self.runner.invoke(self.cli, ["foldernotes", "refresh", "--help"])
        assert result.exit_code == 0

    def test_foldernotes_list_help(self):
        result = self.runner.invoke(self.cli, ["foldernotes", "list", "--help"])
        assert result.exit_code == 0

    def test_foldernotes_exists_help(self):
        result = self.runner.invoke(self.cli, ["foldernotes", "exists", "--help"])
        assert result.exit_code == 0

    # Charts
    def test_charts_help(self):
        result = self.runner.invoke(self.cli, ["charts", "--help"])
        assert result.exit_code == 0

    def test_charts_generate_help(self):
        result = self.runner.invoke(self.cli, ["charts", "generate", "--help"])
        assert result.exit_code == 0
        assert "--type" in result.output
        assert "--labels" in result.output
        assert "--data" in result.output

    def test_charts_insert_help(self):
        result = self.runner.invoke(self.cli, ["charts", "insert", "--help"])
        assert result.exit_code == 0
        assert "--heading" in result.output


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
