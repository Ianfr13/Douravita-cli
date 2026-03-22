"""End-to-end tests for cli-anything-obsidian.

These tests REQUIRE Obsidian to be running with the Local REST API plugin enabled.
Set OBSIDIAN_API_KEY to your API key before running.

Skips automatically if Obsidian is not reachable.

Run with:
    export OBSIDIAN_API_KEY="your-api-key"
    python -m pytest cli_anything/obsidian/tests/test_full_e2e.py -v -s
"""

import os
import sys
import json
import subprocess
import pytest

from cli_anything.obsidian.utils.obsidian_backend import (
    DEFAULT_BASE_URL, is_available,
)

# ── Skip guard ────────────────────────────────────────────────────────────────

OBSIDIAN_AVAILABLE = is_available(DEFAULT_BASE_URL)
API_KEY = os.environ.get("OBSIDIAN_API_KEY", "")

pytestmark = pytest.mark.skipif(
    not OBSIDIAN_AVAILABLE or not API_KEY,
    reason="Obsidian not running or OBSIDIAN_API_KEY not set",
)

# ── Test fixture file path ────────────────────────────────────────────────────

TEST_NOTE_PATH = "cli-anything-obsidian-test/test-note.md"
TEST_NOTE_CONTENT = "# CLI Test Note\n\n## Tasks\n\n## Done\n\nfrontmatter_test: initial"


# ── Helper ────────────────────────────────────────────────────────────────────

def _resolve_cli(name: str) -> list[str]:
    """Return argv prefix to invoke the CLI."""
    import shutil
    path = shutil.which(name)
    if path:
        print(f"[_resolve_cli] found: {path}")
        return [path]
    module = name.replace("cli-anything-", "cli_anything.").replace("-", "_")
    print(f"[_resolve_cli] fallback: python -m {module}")
    return [sys.executable, "-m", module]


class TestCLISubprocess:
    """Run CLI commands as subprocesses and verify output."""

    CLI = _resolve_cli("cli-anything-obsidian")
    ENV = {**os.environ, "OBSIDIAN_API_KEY": API_KEY}

    def run(self, *args, input_text: str | None = None) -> subprocess.CompletedProcess:
        """Run CLI with given args and return result."""
        cmd = self.CLI + list(args)
        return subprocess.run(
            cmd, capture_output=True, text=True, env=self.ENV,
            input=input_text, timeout=15,
        )

    def run_json(self, *args) -> dict | list:
        """Run CLI with --json and parse output."""
        result = self.run("--json", *args)
        assert result.returncode == 0, (
            f"CLI failed with code {result.returncode}:\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
        return json.loads(result.stdout)


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestServerStatus(TestCLISubprocess):
    """Test server status endpoint."""

    def test_status_human_output(self):
        result = self.run("status")
        assert result.returncode == 0
        assert "running" in result.stdout.lower() or "ok" in result.stdout.lower()

    def test_status_json_output(self):
        data = self.run_json("status")
        # Response may vary but should be a dict
        assert isinstance(data, dict)


class TestVaultList(TestCLISubprocess):
    """Test vault directory listing."""

    def test_vault_list_root(self):
        result = self.run("vault", "list")
        assert result.returncode == 0

    def test_vault_list_json(self):
        data = self.run_json("vault", "list")
        assert isinstance(data, (dict, list))


class TestVaultCRUD(TestCLISubprocess):
    """Test vault file create, read, update, delete cycle."""

    def setup_method(self):
        """Create test note before each test."""
        self.run("vault", "put", TEST_NOTE_PATH, TEST_NOTE_CONTENT)

    def teardown_method(self):
        """Delete test note after each test (best effort)."""
        self.run("vault", "delete", TEST_NOTE_PATH, "--yes")

    def test_vault_put_creates_file(self):
        result = self.run("vault", "get", TEST_NOTE_PATH)
        assert result.returncode == 0
        assert "CLI Test Note" in result.stdout

    def test_vault_get_markdown(self):
        result = self.run("vault", "get", TEST_NOTE_PATH)
        assert result.returncode == 0
        assert "# CLI Test Note" in result.stdout

    def test_vault_get_json_format(self):
        data = self.run_json("vault", "get", TEST_NOTE_PATH, "--format", "json")
        assert isinstance(data, dict)

    def test_vault_get_map_format(self):
        data = self.run_json("vault", "get", TEST_NOTE_PATH, "--format", "map")
        assert isinstance(data, dict)

    def test_vault_append(self):
        append_content = "\n- [ ] New task from CLI test"
        self.run("vault", "append", TEST_NOTE_PATH, append_content)
        result = self.run("vault", "get", TEST_NOTE_PATH)
        assert result.returncode == 0
        assert "New task from CLI test" in result.stdout

    def test_vault_put_replaces_content(self):
        new_content = "# Replaced\n\nNew content."
        self.run("vault", "put", TEST_NOTE_PATH, new_content)
        result = self.run("vault", "get", TEST_NOTE_PATH)
        assert "Replaced" in result.stdout
        assert "CLI Test Note" not in result.stdout

    def test_vault_patch_append_heading(self):
        result = self.run(
            "vault", "patch", TEST_NOTE_PATH, "- [ ] Patched task",
            "--op", "append", "--type", "heading", "--target", "Tasks",
        )
        assert result.returncode == 0
        content_result = self.run("vault", "get", TEST_NOTE_PATH)
        assert "Patched task" in content_result.stdout

    def test_vault_patch_create_if_missing(self):
        result = self.run(
            "vault", "patch", TEST_NOTE_PATH, "Created content",
            "--op", "append", "--type", "heading", "--target", "New Section",
            "--create",
        )
        assert result.returncode == 0

    def test_vault_get_nonexistent_fails(self):
        result = self.run("vault", "get", "nonexistent/note-xyz-12345.md")
        assert result.returncode != 0


class TestSearch(TestCLISubprocess):
    """Test search operations."""

    def setup_method(self):
        self.run("vault", "put", TEST_NOTE_PATH, TEST_NOTE_CONTENT)

    def teardown_method(self):
        self.run("vault", "delete", TEST_NOTE_PATH, "--yes")

    def test_simple_search_returns_results(self):
        result = self.run("search", "simple", "CLI Test Note")
        assert result.returncode == 0

    def test_simple_search_json(self):
        data = self.run_json("search", "simple", "CLI Test Note")
        assert isinstance(data, list)

    def test_simple_search_no_results(self):
        result = self.run("search", "simple", "xyzzy_no_match_9999")
        assert result.returncode == 0
        assert "No results" in result.stdout

    @pytest.mark.skipif(
        True,  # Set to False if Dataview plugin is installed
        reason="Dataview plugin may not be installed",
    )
    def test_dql_search(self):
        data = self.run_json(
            "search", "dql", f'TABLE file.name FROM "{TEST_NOTE_PATH}"'
        )
        assert isinstance(data, list)

    def test_jsonlogic_search(self):
        data = self.run_json(
            "search", "jsonlogic",
            '{"glob": ["*.md", {"var": "path"}]}',
        )
        assert isinstance(data, list)


class TestCommands(TestCLISubprocess):
    """Test Obsidian command listing."""

    def test_commands_list(self):
        result = self.run("commands", "list")
        assert result.returncode == 0

    def test_commands_list_json(self):
        data = self.run_json("commands", "list")
        assert isinstance(data, list)
        if data:
            assert "id" in data[0]
            assert "name" in data[0]

    def test_commands_list_filter(self):
        result = self.run("commands", "list", "--filter", "editor")
        assert result.returncode == 0

    def test_commands_run_invalid_id(self):
        result = self.run("commands", "run", "nonexistent:command-xyz")
        assert result.returncode != 0


class TestTags(TestCLISubprocess):
    """Test tag listing."""

    def test_tags_list(self):
        result = self.run("tags")
        assert result.returncode == 0

    def test_tags_json(self):
        data = self.run_json("tags")
        assert isinstance(data, list)

    def test_tags_filter(self):
        result = self.run("tags", "--filter", "project")
        assert result.returncode == 0


class TestPeriodicNotes(TestCLISubprocess):
    """Test periodic note operations (daily)."""

    def test_periodic_get_daily(self):
        result = self.run("periodic", "get", "daily")
        # May 404 if daily note doesn't exist yet — that's OK
        # The important thing is no crash/exception
        assert result.returncode in (0, 1)

    def test_periodic_append_daily(self):
        result = self.run("periodic", "append", "daily",
                          "\n- [ ] CLI E2E test task")
        assert result.returncode == 0

    def test_periodic_get_with_specific_date(self):
        result = self.run("periodic", "get", "daily", "--date", "2026-03-01")
        # May 404 if that date note doesn't exist
        assert result.returncode in (0, 1)
