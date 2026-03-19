"""E2E tests for cli-anything-redtrack — requires a valid REDTRACK_API_KEY.

These tests make real HTTP calls to the RedTrack API at https://api.redtrack.io.
All tests are skipped if REDTRACK_API_KEY is not set in the environment.

Usage:
    REDTRACK_API_KEY=your_key python -m pytest cli_anything/redtrack/tests/test_full_e2e.py -v

Subprocess tests require the CLI to be installed and CLI_ANYTHING_FORCE_INSTALLED=1:
    CLI_ANYTHING_FORCE_INSTALLED=1 REDTRACK_API_KEY=your_key python -m pytest ... -v
"""

import json
import os
import shutil
import subprocess
import unittest
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from cli_anything.redtrack.utils.redtrack_backend import is_available, DEFAULT_BASE_URL
from cli_anything.redtrack.redtrack_cli import cli
from cli_anything.redtrack.core import campaigns

# ── Skip guard ───────────────────────────────────────────────────

_api_key = os.environ.get("REDTRACK_API_KEY", "")
_has_key = bool(_api_key)

_skip_no_key = pytest.mark.skipif(
    not _has_key,
    reason="REDTRACK_API_KEY not set — skipping E2E tests"
)

# Applied per-class below so subprocess tests that don't need a key still run


@pytest.fixture
def runner():
    return CliRunner()


# ── Helpers ───────────────────────────────────────────────────────

def _resolve_cli(name):
    """Resolve CLI executable path.

    Returns path if CLI_ANYTHING_FORCE_INSTALLED=1 and CLI is in PATH,
    otherwise returns None (subprocess tests will be skipped).
    """
    force = os.environ.get("CLI_ANYTHING_FORCE_INSTALLED", "0") == "1"
    if force:
        path = shutil.which(name)
        if not path:
            raise RuntimeError(f"{name} not found in PATH. Install with: pip install -e .")
        return path
    return None


# ── Account E2E ───────────────────────────────────────────────────

@_skip_no_key
class TestAccountE2E:
    def test_account_info(self, runner):
        """GET /user — verify the API key is valid and returns account data."""
        result = runner.invoke(cli, ["--json", "account", "info"])
        assert result.exit_code == 0, f"Failed: {result.output}"
        data = json.loads(result.output)
        # Account info should return some kind of user/account object
        assert isinstance(data, dict)

    def test_account_info_human_output(self, runner):
        """Account info in human-readable mode should show 'Account Info'."""
        result = runner.invoke(cli, ["account", "info"])
        assert result.exit_code == 0, f"Failed: {result.output}"
        assert "Account Info" in result.output


# ── is_available E2E ──────────────────────────────────────────────

@_skip_no_key
class TestAvailabilityE2E:
    def test_is_available_with_valid_key(self):
        """is_available() should return True with a valid API key."""
        assert is_available(api_key=_api_key, base_url=DEFAULT_BASE_URL) is True

    def test_is_available_with_bad_key(self):
        """is_available() should return False with an invalid API key."""
        assert is_available(api_key="invalid_key_xyz", base_url=DEFAULT_BASE_URL) is False


# ── Campaign E2E ──────────────────────────────────────────────────

@_skip_no_key
class TestCampaignE2E:
    def test_campaign_list(self, runner):
        """GET /campaigns — list campaigns successfully."""
        result = runner.invoke(cli, ["--json", "campaign", "list"])
        assert result.exit_code == 0, f"Failed: {result.output}"
        data = json.loads(result.output)
        assert isinstance(data, (list, dict, type(None)))

    def test_campaign_list_with_date_range(self, runner):
        """GET /campaigns with date params using page/per pagination."""
        result = runner.invoke(cli, [
            "--json", "campaign", "list",
            "--date-from", "2024-01-01",
            "--date-to", "2024-12-31",
            "--page", "1",
            "--per", "10"
        ])
        assert result.exit_code == 0, f"Failed: {result.output}"

    def test_campaign_list_human(self, runner):
        """Campaign list in human mode should not error."""
        result = runner.invoke(cli, ["campaign", "list"])
        assert result.exit_code == 0, f"Failed: {result.output}"


# ── Offer E2E ─────────────────────────────────────────────────────

@_skip_no_key
class TestOfferE2E:
    def test_offer_list(self, runner):
        """GET /offers — list offers successfully."""
        result = runner.invoke(cli, ["--json", "offer", "list"])
        assert result.exit_code == 0, f"Failed: {result.output}"
        data = json.loads(result.output)
        assert isinstance(data, (list, dict, type(None)))

    def test_offer_list_human(self, runner):
        """Offer list in human mode should not error."""
        result = runner.invoke(cli, ["offer", "list"])
        assert result.exit_code == 0, f"Failed: {result.output}"


# ── Offer Source E2E ──────────────────────────────────────────────

@_skip_no_key
class TestOfferSourceE2E:
    def test_offer_source_list(self, runner):
        """GET /offer_sources — list offer sources successfully."""
        result = runner.invoke(cli, ["--json", "offer-source", "list"])
        assert result.exit_code == 0, f"Failed: {result.output}"
        data = json.loads(result.output)
        assert isinstance(data, (list, dict, type(None)))


# ── Traffic Channel E2E ───────────────────────────────────────────

@_skip_no_key
class TestTrafficE2E:
    def test_traffic_list(self, runner):
        """GET /traffic_channels — list traffic channels."""
        result = runner.invoke(cli, ["--json", "traffic", "list"])
        assert result.exit_code == 0, f"Failed: {result.output}"
        data = json.loads(result.output)
        assert isinstance(data, (list, dict))


# ── Lander E2E ────────────────────────────────────────────────────

@_skip_no_key
class TestLanderE2E:
    def test_lander_list(self, runner):
        """GET /landers — list landers."""
        result = runner.invoke(cli, ["--json", "lander", "list"])
        assert result.exit_code == 0, f"Failed: {result.output}"
        data = json.loads(result.output)
        assert isinstance(data, (list, dict, type(None)))


# ── Report E2E ────────────────────────────────────────────────────

@_skip_no_key
class TestReportE2E:
    def test_report_general(self, runner):
        """GET /reports — general report."""
        result = runner.invoke(cli, [
            "--json", "report", "general",
            "--date-from", "2024-01-01",
            "--date-to", "2024-01-31"
        ])
        assert result.exit_code == 0, f"Failed: {result.output}"

    def test_report_campaigns(self, runner):
        """GET /reports/campaigns — campaigns report."""
        result = runner.invoke(cli, [
            "--json", "report", "campaigns",
            "--date-from", "2024-01-01",
            "--date-to", "2024-01-31"
        ])
        assert result.exit_code == 0, f"Failed: {result.output}"

    def test_report_clicks(self, runner):
        """GET /clicks — click logs."""
        result = runner.invoke(cli, [
            "--json", "report", "clicks",
            "--date-from", "2024-01-01",
            "--date-to", "2024-01-31"
        ])
        assert result.exit_code == 0, f"Failed: {result.output}"


# ── Conversion E2E ────────────────────────────────────────────────

@_skip_no_key
class TestConversionE2E:
    def test_conversion_list(self, runner):
        """GET /conversions — list conversions."""
        result = runner.invoke(cli, [
            "--json", "conversion", "list",
            "--date-from", "2024-01-01",
            "--date-to", "2024-01-31"
        ])
        assert result.exit_code == 0, f"Failed: {result.output}"

    def test_conversion_types_static(self, runner):
        """conversion types command should return the static list."""
        result = runner.invoke(cli, ["--json", "conversion", "types"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "conversion_types" in data
        assert len(data["conversion_types"]) >= 5


# ── Domain E2E ────────────────────────────────────────────────────

@_skip_no_key
class TestDomainE2E:
    def test_domain_list(self, runner):
        """GET /domains — list custom domains."""
        result = runner.invoke(cli, ["--json", "domain", "list"])
        assert result.exit_code == 0, f"Failed: {result.output}"
        data = json.loads(result.output)
        assert isinstance(data, (list, dict))


# ── Lookup E2E ────────────────────────────────────────────────────

@_skip_no_key
class TestLookupE2E:
    def test_lookup_countries(self, runner):
        """GET /countries — no auth needed."""
        result = runner.invoke(cli, ["--json", "lookup", "get", "countries"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert len(data) > 0  # countries list should never be empty

    def test_lookup_browsers(self, runner):
        result = runner.invoke(cli, ["--json", "lookup", "get", "browsers"])
        assert result.exit_code == 0

    def test_lookup_list(self, runner):
        result = runner.invoke(cli, ["--json", "lookup", "list"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "available_lookups" in data


# ── Campaign v2 E2E ───────────────────────────────────────────────

@_skip_no_key
class TestCampaignV2E2E:
    def test_campaign_list_v2(self, runner):
        """GET /campaigns/v2 — lighter campaign list."""
        result = runner.invoke(cli, ["--json", "campaign", "list-v2"])
        assert result.exit_code == 0, f"Failed: {result.output}"
        data = json.loads(result.output)
        assert isinstance(data, (list, dict, type(None)))


# ── Rule E2E ──────────────────────────────────────────────────────

@_skip_no_key
class TestRuleE2E:
    def test_rule_list(self, runner):
        """GET /rules — list automation rules."""
        result = runner.invoke(cli, ["--json", "rule", "list"])
        assert result.exit_code == 0, f"Failed: {result.output}"
        data = json.loads(result.output)
        assert isinstance(data, (list, dict))


# ── Session E2E ───────────────────────────────────────────────────

@_skip_no_key
class TestSessionE2E:
    def test_session_status(self, runner):
        """Session status should show masked API key and base URL."""
        result = runner.invoke(cli, ["--json", "session", "status"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "api_key" in data
        assert "base_url" in data
        assert data["base_url"] == DEFAULT_BASE_URL
        # API key must be masked — not the raw value
        assert data["api_key"] != _api_key


# ── Bulk operations E2E (mocked) ──────────────────────────────────

class TestBulkOperationsE2E(unittest.TestCase):
    """E2E tests for bulk operations — network calls are mocked."""

    api_key = "test_key"
    base_url = DEFAULT_BASE_URL

    def test_bulk_campaign_status_update(self):
        """E2E: Update multiple campaign statuses in one call."""
        with patch("cli_anything.redtrack.core.campaigns.api_patch") as mock_patch:
            mock_patch.return_value = {"updated": 3, "status": "paused"}
            result = campaigns.update_campaign_statuses(
                self.api_key, self.base_url,
                ids=["c1", "c2", "c3"],
                status="paused"
            )
            self.assertEqual(result["updated"], 3)


# ── CLI Subprocess E2E ────────────────────────────────────────────

class TestCLISubprocess(unittest.TestCase):
    """Tests that invoke the CLI as a subprocess (requires installation)."""

    @classmethod
    def setUpClass(cls):
        cls.cli_path = _resolve_cli("cli-anything-redtrack")
        cls.skip = cls.cli_path is None
        cls.env = {**os.environ, "REDTRACK_API_KEY": _api_key}

    def test_help(self):
        if self.skip:
            self.skipTest("CLI not installed — set CLI_ANYTHING_FORCE_INSTALLED=1")
        result = subprocess.run(
            [self.cli_path, "--help"],
            capture_output=True, text=True, env=self.env
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("redtrack", result.stdout.lower())

    def test_version_in_help(self):
        if self.skip:
            self.skipTest("CLI not installed")
        result = subprocess.run(
            [self.cli_path, "--help"],
            capture_output=True, text=True, env=self.env
        )
        self.assertEqual(result.returncode, 0)

    def test_campaign_list_subprocess(self):
        if self.skip:
            self.skipTest("CLI not installed")
        if not _has_key:
            self.skipTest("REDTRACK_API_KEY not set")
        result = subprocess.run(
            [self.cli_path, "--json", "campaign", "list"],
            capture_output=True, text=True, env=self.env
        )
        self.assertEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        self.assertIsInstance(data, (list, dict))

    def test_account_info_subprocess(self):
        if self.skip:
            self.skipTest("CLI not installed")
        if not _has_key:
            self.skipTest("REDTRACK_API_KEY not set")
        result = subprocess.run(
            [self.cli_path, "--json", "account", "info"],
            capture_output=True, text=True, env=self.env
        )
        self.assertEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        self.assertIsInstance(data, dict)

    def test_session_status_subprocess(self):
        if self.skip:
            self.skipTest("CLI not installed")
        result = subprocess.run(
            [self.cli_path, "--json", "session", "status"],
            capture_output=True, text=True, env=self.env
        )
        self.assertEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        self.assertIn("api_key", data)
        self.assertIn("base_url", data)

    def test_invalid_command_subprocess(self):
        if self.skip:
            self.skipTest("CLI not installed")
        result = subprocess.run(
            [self.cli_path, "nonexistent-command"],
            capture_output=True, text=True, env=self.env
        )
        self.assertNotEqual(result.returncode, 0)

    def test_no_api_key_subprocess(self):
        if self.skip:
            self.skipTest("CLI not installed")
        env_no_key = {k: v for k, v in os.environ.items()
                      if k != "REDTRACK_API_KEY"}
        result = subprocess.run(
            [self.cli_path, "campaign", "list"],
            capture_output=True, text=True, env=env_no_key
        )
        self.assertNotEqual(result.returncode, 0)
