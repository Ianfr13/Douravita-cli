"""Unit tests for cli-anything-meta-ads.

All API calls are mocked — no network calls, no credentials required.
"""

import json
import os
import tempfile
import pytest

# ── Helpers ───────────────────────────────────────────────────────────

try:
    import responses as resp_lib
    HAS_RESPONSES = True
except ImportError:
    HAS_RESPONSES = False

MOCK_TOKEN = "mock_access_token_12345"
MOCK_ACCOUNT_ID = "act_123456789"


# ── TestConfig ────────────────────────────────────────────────────────

class TestConfig:
    def setup_method(self):
        # Patch config file to a temp location for each test
        import cli_anything.meta_ads.core.config as cfg
        self._tmpdir = tempfile.mkdtemp()
        from pathlib import Path
        self._orig_file = cfg.CONFIG_FILE
        cfg.CONFIG_FILE = Path(self._tmpdir) / "config.json"

    def teardown_method(self):
        import cli_anything.meta_ads.core.config as cfg
        cfg.CONFIG_FILE = self._orig_file
        import shutil
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_set_and_get_access_token(self):
        from cli_anything.meta_ads.core.config import set_credentials, get_access_token
        set_credentials(access_token="mytoken123")
        assert get_access_token() == "mytoken123"

    def test_set_and_get_account_id(self):
        from cli_anything.meta_ads.core.config import set_credentials, get_ad_account_id
        set_credentials(ad_account_id="987654321")
        result = get_ad_account_id()
        assert result == "act_987654321"

    def test_set_account_id_with_act_prefix(self):
        from cli_anything.meta_ads.core.config import set_credentials, get_ad_account_id
        set_credentials(ad_account_id="act_987654321")
        result = get_ad_account_id()
        assert result == "act_987654321"

    def test_env_override_token(self, monkeypatch):
        from cli_anything.meta_ads.core.config import set_credentials, get_access_token
        set_credentials(access_token="stored_token")
        monkeypatch.setenv("META_ADS_ACCESS_TOKEN", "env_token")
        assert get_access_token() == "env_token"

    def test_env_override_account(self, monkeypatch):
        from cli_anything.meta_ads.core.config import set_credentials, get_ad_account_id
        set_credentials(ad_account_id="111")
        monkeypatch.setenv("META_ADS_AD_ACCOUNT_ID", "222")
        result = get_ad_account_id()
        assert result == "act_222"

    def test_require_access_token_raises_when_missing(self, monkeypatch):
        from cli_anything.meta_ads.core.config import require_access_token
        monkeypatch.delenv("META_ADS_ACCESS_TOKEN", raising=False)
        with pytest.raises(RuntimeError, match="access token"):
            require_access_token()

    def test_show_config_masks_token(self):
        from cli_anything.meta_ads.core.config import set_credentials, show_config
        token = "abcdefghijklmnopqrstuvwxyz1234"
        set_credentials(access_token=token)
        result = show_config()
        assert result["access_token"] != token
        assert "..." in result["access_token"]

    def test_clear_credentials(self):
        from cli_anything.meta_ads.core.config import set_credentials, clear_credentials, load_config
        set_credentials(access_token="tok", ad_account_id="123")
        clear_credentials()
        cfg = load_config()
        assert cfg == {}


# ── TestBackend ───────────────────────────────────────────────────────

@pytest.mark.skipif(not HAS_RESPONSES, reason="responses library not installed")
class TestBackend:
    BASE = "https://graph.facebook.com/v21.0"

    @resp_lib.activate
    def test_api_get_success(self):
        from cli_anything.meta_ads.utils.meta_ads_backend import api_get
        resp_lib.add(resp_lib.GET, f"{self.BASE}/me",
                     json={"id": "123", "name": "Test"}, status=200)
        result = api_get("me", MOCK_TOKEN)
        assert result["id"] == "123"
        assert result["name"] == "Test"

    @resp_lib.activate
    def test_api_get_raises_on_error_response(self):
        from cli_anything.meta_ads.utils.meta_ads_backend import api_get, MetaAdsAPIError
        resp_lib.add(resp_lib.GET, f"{self.BASE}/me",
                     json={"error": {"message": "Invalid token", "code": 190}}, status=200)
        with pytest.raises(MetaAdsAPIError, match="Invalid token"):
            api_get("me", MOCK_TOKEN)

    @resp_lib.activate
    def test_api_post_success(self):
        from cli_anything.meta_ads.utils.meta_ads_backend import api_post
        resp_lib.add(resp_lib.POST, f"{self.BASE}/{MOCK_ACCOUNT_ID}/campaigns",
                     json={"id": "campaign_001"}, status=200)
        result = api_post(f"{MOCK_ACCOUNT_ID}/campaigns", MOCK_TOKEN, {"name": "Test"})
        assert result["id"] == "campaign_001"

    @resp_lib.activate
    def test_api_post_serializes_dicts(self):
        from cli_anything.meta_ads.utils.meta_ads_backend import api_post
        resp_lib.add(resp_lib.POST, f"{self.BASE}/{MOCK_ACCOUNT_ID}/adsets",
                     json={"id": "adset_001"}, status=200)
        targeting = {"geo_locations": {"countries": ["US"]}}
        result = api_post(f"{MOCK_ACCOUNT_ID}/adsets", MOCK_TOKEN, {"targeting": targeting})
        assert result["id"] == "adset_001"
        # targeting should have been JSON-encoded in the request
        req_body = resp_lib.calls[0].request.body
        assert "geo_locations" in req_body

    @resp_lib.activate
    def test_api_delete_success(self):
        from cli_anything.meta_ads.utils.meta_ads_backend import api_delete
        resp_lib.add(resp_lib.DELETE, f"{self.BASE}/campaign_001",
                     json={"success": True}, status=200)
        result = api_delete("campaign_001", MOCK_TOKEN)
        assert result.get("success") is True

    @resp_lib.activate
    def test_api_paginate_single_page(self):
        from cli_anything.meta_ads.utils.meta_ads_backend import api_paginate
        resp_lib.add(resp_lib.GET, f"{self.BASE}/{MOCK_ACCOUNT_ID}/campaigns",
                     json={"data": [{"id": "1"}, {"id": "2"}], "paging": {}}, status=200)
        result = api_paginate(f"{MOCK_ACCOUNT_ID}/campaigns", MOCK_TOKEN)
        assert len(result) == 2

    @resp_lib.activate
    def test_api_paginate_follows_cursor(self):
        from cli_anything.meta_ads.utils.meta_ads_backend import api_paginate
        page1 = {
            "data": [{"id": "1"}],
            "paging": {
                "cursors": {"after": "cursor_abc", "before": "cursor_xyz"},
                "next": "https://graph.facebook.com/v21.0/act_123456789/campaigns?after=cursor_abc"
            }
        }
        page2 = {"data": [{"id": "2"}], "paging": {"cursors": {}}}
        resp_lib.add(resp_lib.GET, f"{self.BASE}/{MOCK_ACCOUNT_ID}/campaigns", json=page1, status=200)
        resp_lib.add(resp_lib.GET, f"{self.BASE}/{MOCK_ACCOUNT_ID}/campaigns", json=page2, status=200)
        result = api_paginate(f"{MOCK_ACCOUNT_ID}/campaigns", MOCK_TOKEN)
        assert len(result) == 2
        assert result[0]["id"] == "1"
        assert result[1]["id"] == "2"

    def test_normalize_account_id_adds_prefix(self):
        from cli_anything.meta_ads.utils.meta_ads_backend import normalize_account_id
        assert normalize_account_id("123456") == "act_123456"

    def test_normalize_account_id_keeps_prefix(self):
        from cli_anything.meta_ads.utils.meta_ads_backend import normalize_account_id
        assert normalize_account_id("act_123456") == "act_123456"


# ── TestCampaign ──────────────────────────────────────────────────────

@pytest.mark.skipif(not HAS_RESPONSES, reason="responses library not installed")
class TestCampaign:
    BASE = "https://graph.facebook.com/v21.0"

    @resp_lib.activate
    def test_list_campaigns(self):
        from cli_anything.meta_ads.core.campaign import list_campaigns
        mock = {"data": [
            {"id": "c1", "name": "Camp 1", "objective": "OUTCOME_TRAFFIC",
             "effective_status": "ACTIVE", "daily_budget": "1000"},
        ], "paging": {}}
        resp_lib.add(resp_lib.GET, f"{self.BASE}/{MOCK_ACCOUNT_ID}/campaigns", json=mock, status=200)
        result = list_campaigns(MOCK_TOKEN, MOCK_ACCOUNT_ID)
        assert len(result) == 1
        assert result[0]["name"] == "Camp 1"

    @resp_lib.activate
    def test_get_campaign(self):
        from cli_anything.meta_ads.core.campaign import get_campaign
        mock = {"id": "c1", "name": "My Campaign", "objective": "OUTCOME_TRAFFIC"}
        resp_lib.add(resp_lib.GET, f"{self.BASE}/c1", json=mock, status=200)
        result = get_campaign(MOCK_TOKEN, "c1")
        assert result["id"] == "c1"

    @resp_lib.activate
    def test_create_campaign_minimal(self):
        from cli_anything.meta_ads.core.campaign import create_campaign
        resp_lib.add(resp_lib.POST, f"{self.BASE}/{MOCK_ACCOUNT_ID}/campaigns",
                     json={"id": "c_new"}, status=200)
        result = create_campaign(MOCK_TOKEN, MOCK_ACCOUNT_ID,
                                 name="Test", objective="OUTCOME_TRAFFIC", status="PAUSED")
        assert result["id"] == "c_new"

    @resp_lib.activate
    def test_create_campaign_with_budget(self):
        from cli_anything.meta_ads.core.campaign import create_campaign
        resp_lib.add(resp_lib.POST, f"{self.BASE}/{MOCK_ACCOUNT_ID}/campaigns",
                     json={"id": "c_budget"}, status=200)
        result = create_campaign(MOCK_TOKEN, MOCK_ACCOUNT_ID,
                                 name="Budget Camp", objective="OUTCOME_TRAFFIC",
                                 daily_budget=5000)
        assert result["id"] == "c_budget"
        req_body = resp_lib.calls[0].request.body
        assert "daily_budget=5000" in req_body

    @resp_lib.activate
    def test_update_campaign_name(self):
        from cli_anything.meta_ads.core.campaign import update_campaign
        resp_lib.add(resp_lib.POST, f"{self.BASE}/c1", json={"success": True}, status=200)
        update_campaign(MOCK_TOKEN, "c1", name="New Name")
        req_body = resp_lib.calls[0].request.body
        assert "New+Name" in req_body or "New%20Name" in req_body or "New Name" in req_body

    @resp_lib.activate
    def test_set_campaign_status_paused(self):
        from cli_anything.meta_ads.core.campaign import set_campaign_status
        resp_lib.add(resp_lib.POST, f"{self.BASE}/c1", json={"success": True}, status=200)
        set_campaign_status(MOCK_TOKEN, "c1", "PAUSED")
        assert "PAUSED" in resp_lib.calls[0].request.body

    @resp_lib.activate
    def test_delete_campaign(self):
        from cli_anything.meta_ads.core.campaign import delete_campaign
        resp_lib.add(resp_lib.DELETE, f"{self.BASE}/c1", json={"success": True}, status=200)
        result = delete_campaign(MOCK_TOKEN, "c1")
        assert result.get("success") is True

    def test_update_campaign_no_fields_raises(self):
        from cli_anything.meta_ads.core.campaign import update_campaign
        with pytest.raises(ValueError, match="No fields"):
            update_campaign(MOCK_TOKEN, "c1")


# ── TestAdSet ─────────────────────────────────────────────────────────

@pytest.mark.skipif(not HAS_RESPONSES, reason="responses library not installed")
class TestAdSet:
    BASE = "https://graph.facebook.com/v21.0"

    @resp_lib.activate
    def test_list_adsets(self):
        from cli_anything.meta_ads.core.adset import list_adsets
        mock = {"data": [{"id": "as1", "name": "AdSet 1", "campaign_id": "c1"}], "paging": {}}
        resp_lib.add(resp_lib.GET, f"{self.BASE}/{MOCK_ACCOUNT_ID}/adsets", json=mock, status=200)
        result = list_adsets(MOCK_TOKEN, MOCK_ACCOUNT_ID)
        assert result[0]["id"] == "as1"

    @resp_lib.activate
    def test_create_adset_with_targeting(self):
        from cli_anything.meta_ads.core.adset import create_adset
        resp_lib.add(resp_lib.POST, f"{self.BASE}/{MOCK_ACCOUNT_ID}/adsets",
                     json={"id": "as_new"}, status=200)
        targeting = {"geo_locations": {"countries": ["BR"]}}
        result = create_adset(MOCK_TOKEN, MOCK_ACCOUNT_ID, name="BR Set",
                              campaign_id="c1", targeting=targeting)
        assert result["id"] == "as_new"
        req_body = resp_lib.calls[0].request.body
        assert "geo_locations" in req_body

    @resp_lib.activate
    def test_set_adset_status_active(self):
        from cli_anything.meta_ads.core.adset import set_adset_status
        resp_lib.add(resp_lib.POST, f"{self.BASE}/as1", json={"success": True}, status=200)
        set_adset_status(MOCK_TOKEN, "as1", "ACTIVE")
        assert "ACTIVE" in resp_lib.calls[0].request.body

    @resp_lib.activate
    def test_delete_adset(self):
        from cli_anything.meta_ads.core.adset import delete_adset
        resp_lib.add(resp_lib.DELETE, f"{self.BASE}/as1", json={"success": True}, status=200)
        result = delete_adset(MOCK_TOKEN, "as1")
        assert result.get("success") is True


# ── TestAd ────────────────────────────────────────────────────────────

@pytest.mark.skipif(not HAS_RESPONSES, reason="responses library not installed")
class TestAd:
    BASE = "https://graph.facebook.com/v21.0"

    @resp_lib.activate
    def test_create_ad(self):
        from cli_anything.meta_ads.core.ad import create_ad
        resp_lib.add(resp_lib.POST, f"{self.BASE}/{MOCK_ACCOUNT_ID}/ads",
                     json={"id": "ad_new"}, status=200)
        result = create_ad(MOCK_TOKEN, MOCK_ACCOUNT_ID,
                           name="My Ad", adset_id="as1", creative_id="cr1")
        assert result["id"] == "ad_new"

    @resp_lib.activate
    def test_set_ad_status_paused(self):
        from cli_anything.meta_ads.core.ad import set_ad_status
        resp_lib.add(resp_lib.POST, f"{self.BASE}/ad1", json={"success": True}, status=200)
        set_ad_status(MOCK_TOKEN, "ad1", "PAUSED")
        assert "PAUSED" in resp_lib.calls[0].request.body

    @resp_lib.activate
    def test_delete_ad(self):
        from cli_anything.meta_ads.core.ad import delete_ad
        resp_lib.add(resp_lib.DELETE, f"{self.BASE}/ad1", json={"success": True}, status=200)
        result = delete_ad(MOCK_TOKEN, "ad1")
        assert result.get("success") is True


# ── TestCreative ──────────────────────────────────────────────────────

@pytest.mark.skipif(not HAS_RESPONSES, reason="responses library not installed")
class TestCreative:
    BASE = "https://graph.facebook.com/v21.0"

    @resp_lib.activate
    def test_create_creative_link(self):
        from cli_anything.meta_ads.core.creative import create_creative
        resp_lib.add(resp_lib.POST, f"{self.BASE}/{MOCK_ACCOUNT_ID}/adcreatives",
                     json={"id": "cr_new"}, status=200)
        result = create_creative(MOCK_TOKEN, MOCK_ACCOUNT_ID,
                                 name="Link Creative", page_id="page_1",
                                 message="Check this out", link="https://example.com",
                                 call_to_action_type="LEARN_MORE")
        assert result["id"] == "cr_new"
        req_body = resp_lib.calls[0].request.body
        assert "link_data" in req_body or "object_story_spec" in req_body

    @resp_lib.activate
    def test_delete_creative(self):
        from cli_anything.meta_ads.core.creative import delete_creative
        resp_lib.add(resp_lib.DELETE, f"{self.BASE}/cr1", json={"success": True}, status=200)
        result = delete_creative(MOCK_TOKEN, "cr1")
        assert result.get("success") is True


# ── TestAudience ──────────────────────────────────────────────────────

@pytest.mark.skipif(not HAS_RESPONSES, reason="responses library not installed")
class TestAudience:
    BASE = "https://graph.facebook.com/v21.0"

    @resp_lib.activate
    def test_create_custom_audience(self):
        from cli_anything.meta_ads.core.audience import create_custom_audience
        resp_lib.add(resp_lib.POST, f"{self.BASE}/{MOCK_ACCOUNT_ID}/customaudiences",
                     json={"id": "aud_new"}, status=200)
        result = create_custom_audience(MOCK_TOKEN, MOCK_ACCOUNT_ID,
                                        name="My Buyers", subtype="CUSTOM")
        assert result["id"] == "aud_new"

    @resp_lib.activate
    def test_create_lookalike_audience(self):
        from cli_anything.meta_ads.core.audience import create_lookalike_audience
        resp_lib.add(resp_lib.POST, f"{self.BASE}/{MOCK_ACCOUNT_ID}/customaudiences",
                     json={"id": "lal_new"}, status=200)
        result = create_lookalike_audience(
            MOCK_TOKEN, MOCK_ACCOUNT_ID, name="LAL Buyers",
            origin_audience_id="aud_123", country="BR", ratio=0.02)
        assert result["id"] == "lal_new"
        req_body = resp_lib.calls[0].request.body
        assert "lookalike_spec" in req_body
        assert "BR" in req_body

    @resp_lib.activate
    def test_delete_audience(self):
        from cli_anything.meta_ads.core.audience import delete_audience
        resp_lib.add(resp_lib.DELETE, f"{self.BASE}/aud1", json={"success": True}, status=200)
        result = delete_audience(MOCK_TOKEN, "aud1")
        assert result.get("success") is True


# ── TestSession ───────────────────────────────────────────────────────

class TestSession:
    def setup_method(self):
        import cli_anything.meta_ads.core.session as sess_mod
        self._tmpdir = tempfile.mkdtemp()
        from pathlib import Path
        self._orig = sess_mod.SESSION_FILE
        sess_mod.SESSION_FILE = Path(self._tmpdir) / "session.json"

    def teardown_method(self):
        import cli_anything.meta_ads.core.session as sess_mod
        sess_mod.SESSION_FILE = self._orig
        import shutil
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_set_account(self):
        from cli_anything.meta_ads.core.session import Session
        s = Session()
        s.set_account("act_123")
        s2 = Session()
        assert s2.ad_account_id == "act_123"

    def test_set_campaign_clears_adset(self):
        from cli_anything.meta_ads.core.session import Session
        s = Session()
        s.set_adset("as1", "AdSet 1")
        s.set_campaign("c1", "Campaign 1")
        assert s.active_adset_id is None

    def test_context_label_shows_account(self):
        from cli_anything.meta_ads.core.session import Session
        s = Session()
        s.set_account("act_987")
        assert "987" in s.context_label

    def test_clear_session(self):
        from cli_anything.meta_ads.core.session import Session
        s = Session()
        s.set_account("act_123")
        s.clear()
        s2 = Session()
        assert s2.ad_account_id is None
