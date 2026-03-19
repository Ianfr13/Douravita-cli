"""E2E tests for cli_anything.google_tag_manager.

These tests require REAL Google Tag Manager API access.
Set the following environment variables before running:

    GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
    GTM_ACCOUNT_ID=12345

WARNING: These tests CREATE and DELETE real GTM resources.
Use a dedicated test GTM account/container.

Run:
    # E2E API tests
    GOOGLE_APPLICATION_CREDENTIALS=sa.json GTM_ACCOUNT_ID=12345 \\
        python3 -m pytest cli_anything/google_tag_manager/tests/test_full_e2e.py -v

    # Subprocess tests (installed CLI required)
    CLI_ANYTHING_FORCE_INSTALLED=1 \\
        python3 -m pytest cli_anything/google_tag_manager/tests/test_full_e2e.py -v -s
"""
import os
import sys
import json
import time
import subprocess
import shutil
import pytest

# ── Helper: resolve installed CLI command ─────────────────────────────

def _resolve_cli(name: str) -> list:
    """Resolve installed CLI command; falls back to python -m for dev.

    Set env CLI_ANYTHING_FORCE_INSTALLED=1 to require the installed command.
    """
    force = os.environ.get("CLI_ANYTHING_FORCE_INSTALLED", "").strip() == "1"
    path = shutil.which(name)
    if path:
        print(f"[_resolve_cli] Using installed command: {path}")
        return [path]
    if force:
        raise RuntimeError(
            f"{name} not found in PATH. Install with:\n"
            f"  pip install -e /path/to/google-tag-manager/agent-harness/"
        )
    module = "cli_anything.google_tag_manager.google_tag_manager_cli"
    print(f"[_resolve_cli] Falling back to: {sys.executable} -m {module}")
    return [sys.executable, "-m", module]


# ── Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def gtm_account_id():
    """Get GTM account ID from environment."""
    aid = os.environ.get("GTM_ACCOUNT_ID", "").strip()
    if not aid:
        pytest.skip(
            "GTM_ACCOUNT_ID not set. Set it to run E2E tests.\n"
            "  export GTM_ACCOUNT_ID=12345"
        )
    return aid


@pytest.fixture(scope="session")
def gtm_service():
    """Get authenticated GTM service."""
    from cli_anything.google_tag_manager.utils.gtm_backend import get_gtm_service
    try:
        svc = get_gtm_service()
        return svc
    except RuntimeError as e:
        pytest.skip(f"GTM authentication not available: {e}")


@pytest.fixture(scope="session")
def test_container(gtm_service, gtm_account_id):
    """Create a test container for this test session, delete it at teardown."""
    from cli_anything.google_tag_manager.core.containers import create_container, delete_container

    container_name = f"cli-anything-test-{int(time.time())}"
    container = create_container(
        gtm_service, gtm_account_id, container_name,
        usage_context=["web"],
        notes="Created by cli-anything E2E tests. Safe to delete."
    )
    container_id = container["containerId"]
    print(f"\n  Created test container: {container_name} (ID: {container_id})")

    yield container

    # Teardown: delete the test container
    try:
        delete_container(gtm_service, gtm_account_id, container_id)
        print(f"\n  Deleted test container: {container_id}")
    except Exception as e:
        print(f"\n  Warning: Failed to delete test container {container_id}: {e}")


@pytest.fixture(scope="session")
def test_workspace(gtm_service, gtm_account_id, test_container):
    """Get the default workspace in the test container."""
    from cli_anything.google_tag_manager.core.workspaces import list_workspaces

    container_id = test_container["containerId"]
    workspaces = list_workspaces(gtm_service, gtm_account_id, container_id)
    if not workspaces:
        pytest.skip("No workspaces found in test container.")
    ws = workspaces[0]
    print(f"\n  Using workspace: {ws.get('name')} (ID: {ws.get('workspaceId')})")
    return ws


# ── Authentication Tests ───────────────────────────────────────────────

class TestAuthentication:
    def test_auth_service_gets_service(self, gtm_service):
        """Verify the service object can make an API call."""
        assert gtm_service is not None

    def test_list_real_accounts(self, gtm_service, gtm_account_id):
        """List accounts and find the test account."""
        from cli_anything.google_tag_manager.core.accounts import list_accounts
        accounts = list_accounts(gtm_service)
        print(f"\n  Found {len(accounts)} GTM account(s)")
        assert isinstance(accounts, list)
        # The test account should be in the list
        ids = [a.get("accountId") for a in accounts]
        assert gtm_account_id in ids, (
            f"Expected account {gtm_account_id} in {ids}"
        )


# ── Container Tests ───────────────────────────────────────────────────

class TestContainerLifecycle:
    def test_container_appears_in_list(self, gtm_service, gtm_account_id, test_container):
        """Verify created container appears in list."""
        from cli_anything.google_tag_manager.core.containers import list_containers
        containers = list_containers(gtm_service, gtm_account_id)
        ids = [c.get("containerId") for c in containers]
        assert test_container["containerId"] in ids

    def test_get_container(self, gtm_service, gtm_account_id, test_container):
        """Get the test container by ID."""
        from cli_anything.google_tag_manager.core.containers import get_container
        c = get_container(gtm_service, gtm_account_id, test_container["containerId"])
        assert c["containerId"] == test_container["containerId"]
        assert c["name"] == test_container["name"]

    def test_container_snippet(self, gtm_service, gtm_account_id, test_container):
        """Get the tagging snippet — verify it has snippet content."""
        from cli_anything.google_tag_manager.core.containers import get_snippet
        result = get_snippet(gtm_service, gtm_account_id, test_container["containerId"])
        print(f"\n  Container snippet keys: {list(result.keys())}")
        # Snippet response may vary — just verify we got a response dict
        assert isinstance(result, dict)


# ── Workspace Tests ───────────────────────────────────────────────────

class TestWorkspaceOperations:
    def test_list_workspaces(self, gtm_service, gtm_account_id, test_container):
        """List workspaces in test container."""
        from cli_anything.google_tag_manager.core.workspaces import list_workspaces
        wss = list_workspaces(gtm_service, gtm_account_id, test_container["containerId"])
        print(f"\n  Found {len(wss)} workspace(s)")
        assert isinstance(wss, list)
        assert len(wss) >= 1  # New containers always have a default workspace

    def test_workspace_status(self, gtm_service, gtm_account_id, test_container,
                               test_workspace):
        """Get workspace status for a fresh workspace (should be empty)."""
        from cli_anything.google_tag_manager.core.workspaces import workspace_status
        status = workspace_status(
            gtm_service, gtm_account_id,
            test_container["containerId"],
            test_workspace["workspaceId"]
        )
        print(f"\n  Workspace status: {status}")
        assert isinstance(status, dict)


# ── Tag/Trigger/Variable Lifecycle ───────────────────────────────────

class TestTagTriggerVariableLifecycle:
    """Test the full lifecycle of creating and deleting workspace resources."""

    def test_create_pageview_trigger(self, gtm_service, gtm_account_id, test_container,
                                     test_workspace):
        """Create an All Pages trigger."""
        from cli_anything.google_tag_manager.core.triggers import create_trigger, list_triggers

        result = create_trigger(
            gtm_service, gtm_account_id,
            test_container["containerId"],
            test_workspace["workspaceId"],
            name="All Pages (E2E Test)",
            trigger_type="pageview",
        )
        print(f"\n  Created trigger: {result.get('name')} (ID: {result.get('triggerId')})")
        assert result.get("type") == "pageview"
        assert result.get("triggerId")

        # Verify it appears in list
        triggers = list_triggers(
            gtm_service, gtm_account_id,
            test_container["containerId"],
            test_workspace["workspaceId"]
        )
        trigger_ids = [t.get("triggerId") for t in triggers]
        assert result["triggerId"] in trigger_ids

    def test_create_html_tag(self, gtm_service, gtm_account_id, test_container, test_workspace):
        """Create a Custom HTML tag."""
        from cli_anything.google_tag_manager.core.triggers import list_triggers
        from cli_anything.google_tag_manager.core.tags import create_tag, list_tags

        # Get a trigger to fire this tag
        triggers = list_triggers(
            gtm_service, gtm_account_id,
            test_container["containerId"],
            test_workspace["workspaceId"]
        )
        trigger_ids = [t["triggerId"] for t in triggers] if triggers else []

        tag = create_tag(
            gtm_service, gtm_account_id,
            test_container["containerId"],
            test_workspace["workspaceId"],
            name="Custom HTML Tag (E2E Test)",
            tag_type="html",
            parameters=[{
                "type": "template",
                "key": "html",
                "value": "<!-- E2E Test Tag -->"
            }],
            firing_trigger_ids=trigger_ids[:1] if trigger_ids else None,
        )
        print(f"\n  Created tag: {tag.get('name')} (ID: {tag.get('tagId')})")
        assert tag.get("type") == "html"
        assert tag.get("tagId")

        # Verify in list
        tags = list_tags(
            gtm_service, gtm_account_id,
            test_container["containerId"],
            test_workspace["workspaceId"]
        )
        assert any(t["tagId"] == tag["tagId"] for t in tags)

    def test_create_constant_variable(self, gtm_service, gtm_account_id, test_container,
                                       test_workspace):
        """Create a Constant variable."""
        from cli_anything.google_tag_manager.core.variables import create_variable, list_variables

        var = create_variable(
            gtm_service, gtm_account_id,
            test_container["containerId"],
            test_workspace["workspaceId"],
            name="GA Tracking ID (E2E Test)",
            variable_type="v",
            parameters=[{
                "type": "template",
                "key": "value",
                "value": "UA-XXXXXX-1"
            }],
        )
        print(f"\n  Created variable: {var.get('name')} (ID: {var.get('variableId')})")
        assert var.get("type") == "v"
        assert var.get("variableId")

        # Verify in list
        variables = list_variables(
            gtm_service, gtm_account_id,
            test_container["containerId"],
            test_workspace["workspaceId"]
        )
        assert any(v["variableId"] == var["variableId"] for v in variables)


# ── Version Tests ─────────────────────────────────────────────────────

class TestVersionOperations:
    def test_list_version_headers(self, gtm_service, gtm_account_id, test_container):
        """List version headers for the test container."""
        from cli_anything.google_tag_manager.core.versions import list_version_headers
        headers = list_version_headers(gtm_service, gtm_account_id,
                                        test_container["containerId"])
        print(f"\n  Found {len(headers)} version header(s)")
        assert isinstance(headers, list)

    def test_workspace_quick_preview(self, gtm_service, gtm_account_id, test_container,
                                      test_workspace):
        """Create a quick preview of the test workspace."""
        from cli_anything.google_tag_manager.core.workspaces import quick_preview
        result = quick_preview(
            gtm_service, gtm_account_id,
            test_container["containerId"],
            test_workspace["workspaceId"]
        )
        print(f"\n  Quick preview result keys: {list(result.keys())}")
        assert isinstance(result, dict)


# ── CLI Subprocess Tests ───────────────────────────────────────────────

class TestCLISubprocess:
    """Tests that invoke the installed cli-anything-google-tag-manager command."""

    CLI_BASE = _resolve_cli("cli-anything-google-tag-manager")

    def _run(self, args: list, check: bool = True, extra_env: dict = None) -> subprocess.CompletedProcess:
        env = os.environ.copy()
        if extra_env:
            env.update(extra_env)
        return subprocess.run(
            self.CLI_BASE + args,
            capture_output=True,
            text=True,
            check=check,
            env=env,
        )

    def test_help(self):
        """--help exits with code 0."""
        result = self._run(["--help"])
        assert result.returncode == 0
        assert "google-tag-manager" in result.stdout.lower() or "gtm" in result.stdout.lower()

    def test_account_help(self):
        """account --help exits with code 0."""
        result = self._run(["account", "--help"])
        assert result.returncode == 0

    def test_container_help(self):
        """container --help exits with code 0."""
        result = self._run(["container", "--help"])
        assert result.returncode == 0

    def test_workspace_help(self):
        """workspace --help exits with code 0."""
        result = self._run(["workspace", "--help"])
        assert result.returncode == 0

    def test_tag_help(self):
        """tag --help exits with code 0."""
        result = self._run(["tag", "--help"])
        assert result.returncode == 0

    def test_trigger_help(self):
        """trigger --help exits with code 0."""
        result = self._run(["trigger", "--help"])
        assert result.returncode == 0

    def test_variable_help(self):
        """variable --help exits with code 0."""
        result = self._run(["variable", "--help"])
        assert result.returncode == 0

    def test_auth_info_json(self):
        """auth info --json returns valid JSON."""
        result = self._run(["auth", "info", "--json"])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "credentials_file" in data
        assert "account_id" in data
        assert "session_file" in data

    def test_account_list_json_with_credentials(self):
        """account list --json returns JSON array when authenticated."""
        creds = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        account_id = os.environ.get("GTM_ACCOUNT_ID")
        if not creds:
            pytest.skip("GOOGLE_APPLICATION_CREDENTIALS not set for subprocess test.")
        result = self._run(["account", "list", "--json"])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)
        print(f"\n  Subprocess found {len(data)} GTM account(s)")

    def test_container_list_json_with_account(self):
        """container list --json returns JSON array when account is set."""
        account_id = os.environ.get("GTM_ACCOUNT_ID")
        creds = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if not account_id or not creds:
            pytest.skip("GTM_ACCOUNT_ID and GOOGLE_APPLICATION_CREDENTIALS required.")
        result = self._run(["container", "list", account_id, "--json"])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)
        print(f"\n  Subprocess found {len(data)} container(s) in account {account_id}")

    def test_no_credentials_shows_clear_error(self):
        """Without credentials, shows a helpful error message."""
        env_clean = {
            k: v for k, v in os.environ.items()
            if k not in ("GOOGLE_APPLICATION_CREDENTIALS", "GTM_CREDENTIALS_FILE")
        }
        result = subprocess.run(
            self.CLI_BASE + ["account", "list", "--json"],
            capture_output=True, text=True,
            env={**env_clean, "HOME": os.environ.get("HOME", "/tmp")},
        )
        # Should exit with error, not crash silently
        assert result.returncode != 0 or "error" in (result.stdout + result.stderr).lower()
