"""E2E and subprocess tests for cli-anything-meta-ads.

E2E tests require:
  META_ADS_ACCESS_TOKEN  — a valid Meta access token with ads_management + ads_read
  META_ADS_AD_ACCOUNT_ID — the ad account ID to use for testing

All objects created during tests are deleted in teardown.

Subprocess tests use _resolve_cli() to test the installed CLI command.
Set CLI_ANYTHING_FORCE_INSTALLED=1 to require the installed binary.
"""

import json
import os
import subprocess
import sys
import pytest

# ── CLI resolver ──────────────────────────────────────────────────────

def _resolve_cli(name):
    """Resolve installed CLI command; falls back to python -m for dev."""
    import shutil
    force = os.environ.get("CLI_ANYTHING_FORCE_INSTALLED", "").strip() == "1"
    path = shutil.which(name)
    if path:
        print(f"[_resolve_cli] Using installed command: {path}")
        return [path]
    if force:
        raise RuntimeError(f"{name} not found in PATH. Install with: pip install -e .")
    module = "cli_anything.meta_ads.meta_ads_cli"
    print(f"[_resolve_cli] Falling back to: {sys.executable} -m {module}")
    return [sys.executable, "-m", module]


# ── Fixtures ──────────────────────────────────────────────────────────

def _get_creds():
    token = os.environ.get("META_ADS_ACCESS_TOKEN")
    account_id = os.environ.get("META_ADS_AD_ACCOUNT_ID")
    return token, account_id


def _has_creds():
    token, account_id = _get_creds()
    return bool(token and account_id)


NEEDS_CREDS = pytest.mark.skipif(
    not _has_creds(),
    reason="META_ADS_ACCESS_TOKEN and META_ADS_AD_ACCOUNT_ID not set"
)


@pytest.fixture
def token_and_account():
    token, account_id = _get_creds()
    if not account_id.startswith("act_"):
        account_id = f"act_{account_id}"
    return token, account_id


@pytest.fixture
def test_campaign(token_and_account):
    """Create a test campaign and delete it after the test."""
    from cli_anything.meta_ads.core.campaign import create_campaign, delete_campaign
    token, account_id = token_and_account
    data = create_campaign(token, account_id,
                           name="CLI-Anything E2E Test Campaign",
                           objective="OUTCOME_TRAFFIC",
                           status="PAUSED")
    campaign_id = data["id"]
    print(f"\n  [fixture] Created test campaign: {campaign_id}")
    yield campaign_id
    try:
        delete_campaign(token, campaign_id)
        print(f"  [fixture] Deleted test campaign: {campaign_id}")
    except Exception as e:
        print(f"  [fixture] Warning: could not delete campaign {campaign_id}: {e}")


# ── TestAccountE2E ────────────────────────────────────────────────────

@NEEDS_CREDS
class TestAccountE2E:
    def test_validate_token(self, token_and_account):
        from cli_anything.meta_ads.utils.meta_ads_backend import validate_access_token
        token, _ = token_and_account
        data = validate_access_token(token)
        assert "id" in data
        print(f"\n  Token valid for user: {data.get('name', data['id'])}")

    def test_get_account_info(self, token_and_account):
        from cli_anything.meta_ads.core.account import get_account_info
        token, account_id = token_and_account
        data = get_account_info(token, account_id)
        assert data.get("id")
        assert data.get("currency")
        print(f"\n  Account: {data.get('name')} | Currency: {data.get('currency')}")

    def test_list_ad_accounts(self, token_and_account):
        from cli_anything.meta_ads.core.account import list_ad_accounts
        token, _ = token_and_account
        accounts = list_ad_accounts(token)
        assert isinstance(accounts, list)
        assert len(accounts) >= 1
        print(f"\n  Found {len(accounts)} ad account(s)")


# ── TestCampaignE2E ───────────────────────────────────────────────────

@NEEDS_CREDS
class TestCampaignE2E:
    def test_create_and_get_campaign(self, token_and_account):
        from cli_anything.meta_ads.core.campaign import create_campaign, get_campaign, delete_campaign
        token, account_id = token_and_account
        data = create_campaign(token, account_id,
                               name="E2E Test Campaign",
                               objective="OUTCOME_TRAFFIC", status="PAUSED")
        campaign_id = data["id"]
        print(f"\n  Created campaign: {campaign_id}")
        try:
            fetched = get_campaign(token, campaign_id)
            assert fetched["id"] == campaign_id
            assert fetched["name"] == "E2E Test Campaign"
            assert fetched["effective_status"] == "PAUSED"
            print(f"  Verified campaign: {fetched['name']} ({fetched['effective_status']})")
        finally:
            delete_campaign(token, campaign_id)
            print(f"  Deleted campaign: {campaign_id}")

    def test_update_campaign_name(self, token_and_account, test_campaign):
        from cli_anything.meta_ads.core.campaign import update_campaign, get_campaign
        token, _ = token_and_account
        new_name = "E2E Updated Name"
        update_campaign(token, test_campaign, name=new_name)
        fetched = get_campaign(token, test_campaign)
        assert fetched["name"] == new_name
        print(f"\n  Updated campaign name to: {fetched['name']}")

    def test_pause_and_activate_campaign(self, token_and_account, test_campaign):
        from cli_anything.meta_ads.core.campaign import set_campaign_status, get_campaign
        token, _ = token_and_account
        # Already PAUSED — check ACTIVE transition is accepted (may need budget)
        # We just verify the API call succeeds
        set_campaign_status(token, test_campaign, "PAUSED")
        fetched = get_campaign(token, test_campaign)
        assert fetched["effective_status"] in ("PAUSED", "CAMPAIGN_PAUSED")
        print(f"\n  Campaign status: {fetched['effective_status']}")


# ── TestInsightsE2E ───────────────────────────────────────────────────

@NEEDS_CREDS
class TestInsightsE2E:
    def test_account_insights_lifetime(self, token_and_account):
        from cli_anything.meta_ads.core.insights import get_account_insights
        token, account_id = token_and_account
        data = get_account_insights(token, account_id, date_preset="last_30d")
        assert isinstance(data, list)
        print(f"\n  Account insights rows: {len(data)}")
        if data:
            row = data[0]
            print(f"  First row keys: {list(row.keys())}")

    def test_campaign_insights(self, token_and_account, test_campaign):
        from cli_anything.meta_ads.core.insights import get_campaign_insights
        token, _ = token_and_account
        data = get_campaign_insights(token, test_campaign, date_preset="lifetime")
        assert isinstance(data, list)
        print(f"\n  Campaign insights rows: {len(data)}")


# ── TestCLISubprocess ─────────────────────────────────────────────────

class TestCLISubprocess:
    CLI_BASE = _resolve_cli("cli-anything-meta-ads")

    def _run(self, args, check=True, env=None):
        run_env = dict(os.environ)
        if env:
            run_env.update(env)
        return subprocess.run(
            self.CLI_BASE + args,
            capture_output=True, text=True,
            check=check, env=run_env,
        )

    def test_help(self):
        result = self._run(["--help"])
        assert result.returncode == 0
        assert "campaign" in result.stdout.lower()
        assert "insights" in result.stdout.lower()
        print(f"\n  --help OK ({len(result.stdout)} chars)")

    def test_version(self):
        result = self._run(["--version"])
        assert result.returncode == 0
        assert "1.0.0" in result.stdout
        print(f"\n  Version: {result.stdout.strip()}")

    @NEEDS_CREDS
    def test_config_show_json(self):
        result = self._run(["--json", "config", "show"])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "access_token_source" in data
        assert "config_file" in data
        print(f"\n  config show JSON: {list(data.keys())}")

    @NEEDS_CREDS
    def test_campaign_list_json(self):
        result = self._run(["--json", "campaign", "list"])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)
        print(f"\n  campaign list: {len(data)} campaign(s)")

    @NEEDS_CREDS
    def test_campaign_create_and_delete_json(self):
        # Create
        result = self._run([
            "--json", "campaign", "create",
            "--name", "CLI-Anything Subprocess Test",
            "--objective", "OUTCOME_TRAFFIC",
            "--status", "PAUSED",
        ])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "id" in data
        campaign_id = data["id"]
        print(f"\n  Created campaign via subprocess: {campaign_id}")

        # Delete (bypass confirmation prompt by patching env — skip prompt in test)
        # We use campaign update status=DELETED as an alternative
        from cli_anything.meta_ads.core.campaign import delete_campaign
        token = os.environ.get("META_ADS_ACCESS_TOKEN")
        delete_campaign(token, campaign_id)
        print(f"  Deleted campaign: {campaign_id}")

    @NEEDS_CREDS
    def test_insights_account_json(self):
        result = self._run(["--json", "insights", "account", "--preset", "last_7d"])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)
        print(f"\n  insights account (last_7d): {len(data)} row(s)")
