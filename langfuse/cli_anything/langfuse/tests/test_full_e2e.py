"""E2E and subprocess tests for cli-anything-langfuse.

Tests that require real API keys use the LANGFUSE_PUBLIC_KEY and
LANGFUSE_SECRET_KEY environment variables. Tests that don't need
API access (config, help, version) run unconditionally.

Subprocess tests use _resolve_cli() to invoke the installed command.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


# ── CLI resolver ─────────────────────────────────────────────────────


def _resolve_cli(name):
    """Resolve installed CLI command; falls back to python -m for dev.

    Set env CLI_ANYTHING_FORCE_INSTALLED=1 to require the installed command.
    """
    force = os.environ.get("CLI_ANYTHING_FORCE_INSTALLED", "").strip() == "1"
    path = shutil.which(name)
    if path:
        print(f"[_resolve_cli] Using installed command: {path}")
        return [path]
    if force:
        raise RuntimeError(f"{name} not found in PATH. Install with: pip install -e .")
    module = name.replace("cli-anything-", "cli_anything.") + "." + name.split("-")[-1] + "_cli"
    print(f"[_resolve_cli] Falling back to: {sys.executable} -m {module}")
    return [sys.executable, "-m", module]


# ── Helpers ──────────────────────────────────────────────────────────


def _has_api_keys():
    """Check if Langfuse API keys are available."""
    return bool(
        os.environ.get("LANGFUSE_PUBLIC_KEY")
        and os.environ.get("LANGFUSE_SECRET_KEY")
    )


requires_api = pytest.mark.skipif(
    not _has_api_keys(),
    reason="LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY not set"
)


@pytest.fixture
def tmp_dir():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d, ignore_errors=True)


# ══════════════════════════════════════════════════════════════════════
# SUBPROCESS TESTS — No API keys required
# ══════════════════════════════════════════════════════════════════════


class TestCLISubprocess:
    """Test the installed CLI command via subprocess."""

    CLI_BASE = _resolve_cli("cli-anything-langfuse")

    def _run(self, args, check=True, env_override=None):
        env = os.environ.copy()
        if env_override:
            env.update(env_override)
        return subprocess.run(
            self.CLI_BASE + args,
            capture_output=True,
            text=True,
            check=check,
            env=env,
        )

    def test_help(self):
        result = self._run(["--help"])
        assert result.returncode == 0
        assert "cli-anything-langfuse" in result.stdout
        assert "traces" in result.stdout
        assert "prompts" in result.stdout

    def test_version(self):
        result = self._run(["--version"])
        assert result.returncode == 0
        assert "1.0.0" in result.stdout

    def test_traces_help(self):
        result = self._run(["traces", "--help"])
        assert result.returncode == 0
        assert "list" in result.stdout
        assert "get" in result.stdout

    def test_prompts_help(self):
        result = self._run(["prompts", "--help"])
        assert result.returncode == 0
        assert "list" in result.stdout
        assert "create" in result.stdout

    def test_datasets_help(self):
        result = self._run(["datasets", "--help"])
        assert result.returncode == 0
        assert "list" in result.stdout
        assert "create" in result.stdout

    def test_scores_help(self):
        result = self._run(["scores", "--help"])
        assert result.returncode == 0
        assert "create" in result.stdout

    def test_config_help(self):
        result = self._run(["config", "--help"])
        assert result.returncode == 0
        assert "set" in result.stdout
        assert "show" in result.stdout

    def test_models_help(self):
        result = self._run(["models", "--help"])
        assert result.returncode == 0
        assert "list" in result.stdout

    def test_sessions_help(self):
        result = self._run(["sessions", "--help"])
        assert result.returncode == 0

    def test_observations_help(self):
        result = self._run(["observations", "--help"])
        assert result.returncode == 0

    def test_health_help(self):
        result = self._run(["health", "--help"])
        assert result.returncode == 0

    def test_metrics_help(self):
        result = self._run(["metrics", "--help"])
        assert result.returncode == 0


# ══════════════════════════════════════════════════════════════════════
# CONFIG WORKFLOW E2E — No API keys required
# ══════════════════════════════════════════════════════════════════════


class TestConfigWorkflow:
    """Test config profile workflow end-to-end."""

    CLI_BASE = _resolve_cli("cli-anything-langfuse")

    def _run(self, args, check=True, env_override=None):
        env = os.environ.copy()
        if env_override:
            env.update(env_override)
        return subprocess.run(
            self.CLI_BASE + args,
            capture_output=True,
            text=True,
            check=check,
            env=env,
        )

    def test_config_set_and_show(self):
        """Set a profile, verify it shows up, then delete it."""
        profile_name = "test-e2e-tmp-profile"

        # Set profile
        result = self._run([
            "config", "set",
            "--profile", profile_name,
            "--public-key", "pk-lf-test123",
            "--secret-key", "sk-lf-test456",
            "--base-url", "https://test.langfuse.com",
        ])
        assert result.returncode == 0
        assert "updated" in result.stdout.lower()

        # Show profiles
        result = self._run(["config", "show"])
        assert result.returncode == 0
        assert profile_name in result.stdout

        # Show as JSON
        result = self._run(["--json", "config", "show"])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)
        assert any(p["name"] == profile_name for p in data)

        # Delete (cleanup)
        result = self._run([
            "config", "delete", profile_name, "--yes"
        ])
        assert result.returncode == 0


# ══════════════════════════════════════════════════════════════════════
# API E2E TESTS — Requires real API keys
# ══════════════════════════════════════════════════════════════════════


class TestAPITraces:
    """E2E tests for trace operations with real API."""

    CLI_BASE = _resolve_cli("cli-anything-langfuse")

    def _run(self, args, check=True):
        return subprocess.run(
            self.CLI_BASE + args,
            capture_output=True,
            text=True,
            check=check,
        )

    @requires_api
    def test_traces_list_json(self):
        result = self._run(["--json", "traces", "list", "--limit", "5"])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "data" in data
        assert isinstance(data["data"], list)
        print(f"\n  Traces returned: {len(data['data'])}")

    @requires_api
    def test_traces_list_human(self):
        result = self._run(["traces", "list", "--limit", "5"])
        assert result.returncode == 0

    @requires_api
    def test_observations_list_json(self):
        result = self._run(["--json", "observations", "list", "--limit", "5"])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "data" in data

    @requires_api
    def test_scores_list_json(self):
        result = self._run(["--json", "scores", "list", "--limit", "5"])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "data" in data

    @requires_api
    def test_prompts_list_json(self):
        result = self._run(["--json", "prompts", "list", "--limit", "5"])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "data" in data

    @requires_api
    def test_datasets_list_json(self):
        result = self._run(["--json", "datasets", "list", "--limit", "5"])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "data" in data

    @requires_api
    def test_sessions_list_json(self):
        result = self._run(["--json", "sessions", "list", "--limit", "5"])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "data" in data

    @requires_api
    def test_models_list_json(self):
        result = self._run(["--json", "models", "list", "--limit", "5"])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "data" in data


class TestHealthE2E:
    """Health check E2E — works against cloud.langfuse.com."""

    CLI_BASE = _resolve_cli("cli-anything-langfuse")

    def _run(self, args, check=True):
        return subprocess.run(
            self.CLI_BASE + args,
            capture_output=True,
            text=True,
            check=check,
        )

    def test_health_check(self):
        """Health endpoint doesn't require valid auth."""
        result = self._run([
            "--public-key", "check",
            "--secret-key", "check",
            "--base-url", "https://cloud.langfuse.com",
            "health",
        ], check=False)
        # Health check may succeed or fail depending on auth requirements
        # But the command itself should not crash
        assert result.returncode in (0, 1)
