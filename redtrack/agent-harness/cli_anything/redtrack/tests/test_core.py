"""Unit tests for cli-anything-redtrack — no real API calls required.

All network calls are mocked. Tests cover the backend wrapper, all core
modules, CLI argument parsing, session management, and error handling.

Usage:
    python -m pytest cli_anything/redtrack/tests/test_core.py -v
"""

import json
import os
import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from cli_anything.redtrack.redtrack_cli import cli
from cli_anything.redtrack.utils.redtrack_backend import DEFAULT_BASE_URL
from cli_anything.redtrack.core.session import get_session_info, _mask_key


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture(autouse=True)
def set_api_key(monkeypatch):
    """Provide a dummy API key for all tests via environment variable."""
    monkeypatch.setenv("REDTRACK_API_KEY", "test_api_key_1234")


# ── Backend: Constants ────────────────────────────────────────────

class TestBackendConstants:
    def test_default_base_url(self):
        assert DEFAULT_BASE_URL == "https://api.redtrack.io"


# ── Backend: _get_api_key ─────────────────────────────────────────

class TestGetApiKey:
    def test_explicit_key(self):
        from cli_anything.redtrack.utils.redtrack_backend import _get_api_key
        assert _get_api_key("mykey") == "mykey"

    def test_env_key(self, monkeypatch):
        from cli_anything.redtrack.utils.redtrack_backend import _get_api_key
        monkeypatch.setenv("REDTRACK_API_KEY", "env_key_abc")
        assert _get_api_key() == "env_key_abc"

    def test_missing_key_raises(self, monkeypatch):
        from cli_anything.redtrack.utils.redtrack_backend import _get_api_key
        monkeypatch.delenv("REDTRACK_API_KEY", raising=False)
        with pytest.raises(RuntimeError, match="No API key"):
            _get_api_key()

    def test_explicit_key_overrides_env(self, monkeypatch):
        from cli_anything.redtrack.utils.redtrack_backend import _get_api_key
        monkeypatch.setenv("REDTRACK_API_KEY", "env_key")
        assert _get_api_key("explicit_key") == "explicit_key"


# ── Backend: _build_params ────────────────────────────────────────

class TestBuildParams:
    def test_adds_api_key(self):
        from cli_anything.redtrack.utils.redtrack_backend import _build_params
        result = _build_params(None, "mykey")
        assert result == {"api_key": "mykey"}

    def test_merges_params(self):
        from cli_anything.redtrack.utils.redtrack_backend import _build_params
        result = _build_params({"limit": 50, "offset": 0}, "mykey")
        assert result["api_key"] == "mykey"
        assert result["limit"] == 50

    def test_empty_extra_params(self):
        from cli_anything.redtrack.utils.redtrack_backend import _build_params
        result = _build_params({}, "key")
        assert result == {"api_key": "key"}


# ── Backend: api_get ──────────────────────────────────────────────

class TestApiGet:
    @patch("cli_anything.redtrack.utils.redtrack_backend.requests.get")
    def test_success(self, mock_get):
        from cli_anything.redtrack.utils.redtrack_backend import api_get
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = b'{"data": []}'
        mock_resp.json.return_value = {"data": []}
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp
        result = api_get("/campaigns", api_key="testkey")
        assert result == {"data": []}

    @patch("cli_anything.redtrack.utils.redtrack_backend.requests.get")
    def test_url_construction(self, mock_get):
        from cli_anything.redtrack.utils.redtrack_backend import api_get
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = b'{}'
        mock_resp.json.return_value = {}
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp
        api_get("/campaigns", api_key="key", base_url="https://api.redtrack.io")
        call_url = mock_get.call_args[0][0]
        assert call_url == "https://api.redtrack.io/campaigns"

    @patch("cli_anything.redtrack.utils.redtrack_backend.requests.get")
    def test_trailing_slash_stripped(self, mock_get):
        from cli_anything.redtrack.utils.redtrack_backend import api_get
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = b'{}'
        mock_resp.json.return_value = {}
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp
        api_get("/user", api_key="key", base_url="https://api.redtrack.io/")
        call_url = mock_get.call_args[0][0]
        assert call_url == "https://api.redtrack.io/user"

    @patch("cli_anything.redtrack.utils.redtrack_backend.requests.get")
    def test_api_key_in_params(self, mock_get):
        from cli_anything.redtrack.utils.redtrack_backend import api_get
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = b'{}'
        mock_resp.json.return_value = {}
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp
        api_get("/user", api_key="my_secret_key")
        params_used = mock_get.call_args[1]["params"]
        assert params_used.get("api_key") == "my_secret_key"

    @patch("cli_anything.redtrack.utils.redtrack_backend.requests.get")
    def test_api_key_in_header(self, mock_get):
        from cli_anything.redtrack.utils.redtrack_backend import api_get
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = b'{}'
        mock_resp.json.return_value = {}
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp
        api_get("/user", api_key="my_secret_key")
        headers_used = mock_get.call_args[1]["headers"]
        assert headers_used.get("Api-Key") == "my_secret_key"

    @patch("cli_anything.redtrack.utils.redtrack_backend.requests.get")
    def test_connection_error(self, mock_get):
        from cli_anything.redtrack.utils.redtrack_backend import api_get
        import requests
        mock_get.side_effect = requests.exceptions.ConnectionError()
        with pytest.raises(RuntimeError, match="Cannot connect to RedTrack"):
            api_get("/campaigns", api_key="key")

    @patch("cli_anything.redtrack.utils.redtrack_backend.requests.get")
    def test_http_error(self, mock_get):
        from cli_anything.redtrack.utils.redtrack_backend import api_get
        import requests
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.text = "Unauthorized"
        mock_resp.raise_for_status.side_effect = requests.exceptions.HTTPError()
        mock_get.return_value = mock_resp
        with pytest.raises(RuntimeError, match="RedTrack API error 401"):
            api_get("/campaigns", api_key="bad_key")

    @patch("cli_anything.redtrack.utils.redtrack_backend.requests.get")
    def test_timeout(self, mock_get):
        from cli_anything.redtrack.utils.redtrack_backend import api_get
        import requests
        mock_get.side_effect = requests.exceptions.Timeout()
        with pytest.raises(RuntimeError, match="timed out"):
            api_get("/campaigns", api_key="key")

    @patch("cli_anything.redtrack.utils.redtrack_backend.requests.get")
    def test_204_no_content(self, mock_get):
        from cli_anything.redtrack.utils.redtrack_backend import api_get
        mock_resp = MagicMock()
        mock_resp.status_code = 204
        mock_resp.content = b""
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp
        result = api_get("/campaigns/1", api_key="key")
        assert result == {"status": "ok"}


# ── Backend: api_post ─────────────────────────────────────────────

class TestApiPost:
    @patch("cli_anything.redtrack.utils.redtrack_backend.requests.post")
    def test_success(self, mock_post):
        from cli_anything.redtrack.utils.redtrack_backend import api_post
        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_resp.content = b'{"id": "123"}'
        mock_resp.json.return_value = {"id": "123"}
        mock_resp.raise_for_status.return_value = None
        mock_post.return_value = mock_resp
        result = api_post("/campaigns", data={"name": "Test"}, api_key="key")
        assert result == {"id": "123"}

    @patch("cli_anything.redtrack.utils.redtrack_backend.requests.post")
    def test_connection_error(self, mock_post):
        from cli_anything.redtrack.utils.redtrack_backend import api_post
        import requests
        mock_post.side_effect = requests.exceptions.ConnectionError()
        with pytest.raises(RuntimeError, match="Cannot connect to RedTrack"):
            api_post("/campaigns", data={}, api_key="key")

    @patch("cli_anything.redtrack.utils.redtrack_backend.requests.post")
    def test_http_error(self, mock_post):
        from cli_anything.redtrack.utils.redtrack_backend import api_post
        import requests
        mock_resp = MagicMock()
        mock_resp.status_code = 422
        mock_resp.text = "Unprocessable Entity"
        mock_resp.raise_for_status.side_effect = requests.exceptions.HTTPError()
        mock_post.return_value = mock_resp
        with pytest.raises(RuntimeError, match="RedTrack API error 422"):
            api_post("/campaigns", data={}, api_key="key")

    @patch("cli_anything.redtrack.utils.redtrack_backend.requests.post")
    def test_timeout(self, mock_post):
        from cli_anything.redtrack.utils.redtrack_backend import api_post
        import requests
        mock_post.side_effect = requests.exceptions.Timeout()
        with pytest.raises(RuntimeError, match="timed out"):
            api_post("/campaigns", data={}, api_key="key")

    @patch("cli_anything.redtrack.utils.redtrack_backend.requests.post")
    def test_204_no_content(self, mock_post):
        from cli_anything.redtrack.utils.redtrack_backend import api_post
        mock_resp = MagicMock()
        mock_resp.status_code = 204
        mock_resp.content = b""
        mock_resp.raise_for_status.return_value = None
        mock_post.return_value = mock_resp
        result = api_post("/conversions", data={"click_id": "abc"}, api_key="key")
        assert result == {"status": "ok"}


# ── Backend: api_patch ────────────────────────────────────────────

class TestApiPatch:
    @patch("cli_anything.redtrack.utils.redtrack_backend.requests.patch")
    def test_success(self, mock_patch):
        from cli_anything.redtrack.utils.redtrack_backend import api_patch
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = b'{"id": "1", "name": "Updated"}'
        mock_resp.json.return_value = {"id": "1", "name": "Updated"}
        mock_resp.raise_for_status.return_value = None
        mock_patch.return_value = mock_resp
        result = api_patch("/campaigns/1", data={"name": "Updated"}, api_key="key")
        assert result["name"] == "Updated"

    @patch("cli_anything.redtrack.utils.redtrack_backend.requests.patch")
    def test_connection_error(self, mock_patch):
        from cli_anything.redtrack.utils.redtrack_backend import api_patch
        import requests
        mock_patch.side_effect = requests.exceptions.ConnectionError()
        with pytest.raises(RuntimeError, match="Cannot connect to RedTrack"):
            api_patch("/campaigns/1", data={}, api_key="key")

    @patch("cli_anything.redtrack.utils.redtrack_backend.requests.patch")
    def test_timeout(self, mock_patch):
        from cli_anything.redtrack.utils.redtrack_backend import api_patch
        import requests
        mock_patch.side_effect = requests.exceptions.Timeout()
        with pytest.raises(RuntimeError, match="timed out"):
            api_patch("/campaigns/1", data={}, api_key="key")

    @patch("cli_anything.redtrack.utils.redtrack_backend.requests.patch")
    def test_http_error(self, mock_patch):
        from cli_anything.redtrack.utils.redtrack_backend import api_patch
        import requests
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.text = "Not Found"
        mock_resp.raise_for_status.side_effect = requests.exceptions.HTTPError()
        mock_patch.return_value = mock_resp
        with pytest.raises(RuntimeError, match="RedTrack API error 404"):
            api_patch("/campaigns/9999", data={}, api_key="key")


# ── Backend: api_delete ───────────────────────────────────────────

class TestApiDelete:
    @patch("cli_anything.redtrack.utils.redtrack_backend.requests.delete")
    def test_success(self, mock_delete):
        from cli_anything.redtrack.utils.redtrack_backend import api_delete
        mock_resp = MagicMock()
        mock_resp.status_code = 204
        mock_resp.content = b""
        mock_resp.raise_for_status.return_value = None
        mock_delete.return_value = mock_resp
        result = api_delete("/campaigns/1", api_key="key")
        assert result == {"status": "ok"}

    @patch("cli_anything.redtrack.utils.redtrack_backend.requests.delete")
    def test_connection_error(self, mock_delete):
        from cli_anything.redtrack.utils.redtrack_backend import api_delete
        import requests
        mock_delete.side_effect = requests.exceptions.ConnectionError()
        with pytest.raises(RuntimeError, match="Cannot connect to RedTrack"):
            api_delete("/campaigns/1", api_key="key")

    @patch("cli_anything.redtrack.utils.redtrack_backend.requests.delete")
    def test_http_error(self, mock_delete):
        from cli_anything.redtrack.utils.redtrack_backend import api_delete
        import requests
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.text = "Not Found"
        mock_resp.raise_for_status.side_effect = requests.exceptions.HTTPError()
        mock_delete.return_value = mock_resp
        with pytest.raises(RuntimeError, match="RedTrack API error 404"):
            api_delete("/campaigns/9999", api_key="key")

    @patch("cli_anything.redtrack.utils.redtrack_backend.requests.delete")
    def test_timeout(self, mock_delete):
        from cli_anything.redtrack.utils.redtrack_backend import api_delete
        import requests
        mock_delete.side_effect = requests.exceptions.Timeout()
        with pytest.raises(RuntimeError, match="timed out"):
            api_delete("/campaigns/1", api_key="key")


# ── Backend: is_available ─────────────────────────────────────────

class TestIsAvailable:
    @patch("cli_anything.redtrack.utils.redtrack_backend.requests.get")
    def test_available(self, mock_get):
        from cli_anything.redtrack.utils.redtrack_backend import is_available
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_get.return_value = mock_resp
        assert is_available(api_key="key") is True

    @patch("cli_anything.redtrack.utils.redtrack_backend.requests.get")
    def test_not_available_connection_error(self, mock_get):
        from cli_anything.redtrack.utils.redtrack_backend import is_available
        import requests
        mock_get.side_effect = requests.exceptions.ConnectionError()
        assert is_available(api_key="key") is False

    @patch("cli_anything.redtrack.utils.redtrack_backend.requests.get")
    def test_not_available_timeout(self, mock_get):
        from cli_anything.redtrack.utils.redtrack_backend import is_available
        import requests
        mock_get.side_effect = requests.exceptions.Timeout()
        assert is_available(api_key="key") is False

    def test_not_available_no_key(self, monkeypatch):
        from cli_anything.redtrack.utils.redtrack_backend import is_available
        monkeypatch.delenv("REDTRACK_API_KEY", raising=False)
        assert is_available() is False

    @patch("cli_anything.redtrack.utils.redtrack_backend.requests.get")
    def test_not_available_non_200(self, mock_get):
        from cli_anything.redtrack.utils.redtrack_backend import is_available
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_get.return_value = mock_resp
        assert is_available(api_key="bad_key") is False


# ── Session management ────────────────────────────────────────────

class TestSessionManagement:
    def test_mask_key_short(self):
        assert _mask_key("abc") == "***"

    def test_mask_key_long(self):
        masked = _mask_key("abcd12345678efgh")
        assert masked.startswith("abcd")
        assert masked.endswith("efgh")
        assert "****" in masked

    def test_mask_key_none(self):
        assert _mask_key(None) == "(not set)"

    def test_mask_key_empty(self):
        assert _mask_key("") == "(not set)"

    def test_mask_key_exactly_8(self):
        masked = _mask_key("12345678")
        assert masked == "********"

    def test_get_session_info_with_key(self):
        info = get_session_info("mykey", "https://api.redtrack.io")
        assert info["authenticated"] is True
        assert info["base_url"] == "https://api.redtrack.io"
        assert "mykey" not in info["api_key"]  # key must be masked

    def test_get_session_info_no_key(self):
        info = get_session_info(None, "https://api.redtrack.io")
        assert info["authenticated"] is False
        assert info["api_key"] == "(not set)"


# ── CLI: Help and argument parsing ────────────────────────────────

class TestCLIParsing:
    def test_help(self, runner):
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "RedTrack" in result.output

    def test_campaign_help(self, runner):
        result = runner.invoke(cli, ["campaign", "--help"])
        assert result.exit_code == 0
        assert "list" in result.output
        assert "get" in result.output
        assert "create" in result.output
        assert "update" in result.output
        assert "delete" in result.output

    def test_offer_help(self, runner):
        result = runner.invoke(cli, ["offer", "--help"])
        assert result.exit_code == 0
        assert "list" in result.output
        assert "create" in result.output

    def test_offer_source_help(self, runner):
        result = runner.invoke(cli, ["offer-source", "--help"])
        assert result.exit_code == 0
        assert "list" in result.output

    def test_traffic_help(self, runner):
        result = runner.invoke(cli, ["traffic", "--help"])
        assert result.exit_code == 0
        assert "list" in result.output

    def test_lander_help(self, runner):
        result = runner.invoke(cli, ["lander", "--help"])
        assert result.exit_code == 0
        assert "list" in result.output

    def test_conversion_help(self, runner):
        result = runner.invoke(cli, ["conversion", "--help"])
        assert result.exit_code == 0
        assert "list" in result.output
        assert "upload" in result.output

    def test_report_help(self, runner):
        result = runner.invoke(cli, ["report", "--help"])
        assert result.exit_code == 0
        assert "general" in result.output
        assert "campaigns" in result.output
        assert "clicks" in result.output

    def test_cost_help(self, runner):
        result = runner.invoke(cli, ["cost", "--help"])
        assert result.exit_code == 0
        assert "list" in result.output

    def test_rule_help(self, runner):
        result = runner.invoke(cli, ["rule", "--help"])
        assert result.exit_code == 0
        assert "list" in result.output
        assert "create" in result.output

    def test_domain_help(self, runner):
        result = runner.invoke(cli, ["domain", "--help"])
        assert result.exit_code == 0
        assert "list" in result.output
        assert "add" in result.output

    def test_session_help(self, runner):
        result = runner.invoke(cli, ["session", "--help"])
        assert result.exit_code == 0
        assert "status" in result.output

    def test_json_flag_session(self, runner):
        result = runner.invoke(cli, ["--json", "session", "status"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "api_key" in data
        assert "base_url" in data

    def test_base_url_flag(self, runner):
        result = runner.invoke(cli, [
            "--base-url", "https://custom.api.example.com",
            "--json", "session", "status"
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["base_url"] == "https://custom.api.example.com"

    def test_api_key_flag_masked_in_session(self, runner):
        result = runner.invoke(cli, [
            "--api-key", "abcd12345678efgh",
            "--json", "session", "status"
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "abcd12345678efgh" not in data["api_key"]


# ── CLI: Campaign commands with mocked API ────────────────────────

class TestCampaignCommands:
    @patch("cli_anything.redtrack.core.campaigns.api_get")
    def test_campaign_list_empty(self, mock_api, runner):
        mock_api.return_value = []
        result = runner.invoke(cli, ["campaign", "list"])
        assert result.exit_code == 0
        assert "No campaigns" in result.output

    @patch("cli_anything.redtrack.core.campaigns.api_get")
    def test_campaign_list_json(self, mock_api, runner):
        mock_api.return_value = [{"id": "1", "name": "Test Campaign", "status": "active"}]
        result = runner.invoke(cli, ["--json", "campaign", "list"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert data[0]["name"] == "Test Campaign"

    @patch("cli_anything.redtrack.core.campaigns.api_get")
    def test_campaign_list_human(self, mock_api, runner):
        mock_api.return_value = [{"id": "1", "name": "Test Campaign", "status": "active"}]
        result = runner.invoke(cli, ["campaign", "list"])
        assert result.exit_code == 0
        assert "Test Campaign" in result.output

    @patch("cli_anything.redtrack.core.campaigns.api_get")
    def test_campaign_get(self, mock_api, runner):
        mock_api.return_value = {"id": "42", "name": "My Campaign", "status": "active"}
        result = runner.invoke(cli, ["--json", "campaign", "get", "42"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["id"] == "42"

    @patch("cli_anything.redtrack.core.campaigns.api_post")
    def test_campaign_create(self, mock_api, runner):
        mock_api.return_value = {"id": "99", "name": "New Campaign"}
        result = runner.invoke(cli, [
            "--json", "campaign", "create",
            "--name", "New Campaign",
            "--traffic-channel-id", "5"
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["id"] == "99"

    @patch("cli_anything.redtrack.core.campaigns.api_post")
    def test_campaign_create_with_all_options(self, mock_api, runner):
        mock_api.return_value = {"id": "100", "name": "Full Campaign"}
        result = runner.invoke(cli, [
            "--json", "campaign", "create",
            "--name", "Full Campaign",
            "--traffic-channel-id", "3",
            "--domain", "track.example.com",
            "--cost-type", "cpc",
            "--cost-value", "0.50"
        ])
        assert result.exit_code == 0

    @patch("cli_anything.redtrack.core.campaigns.api_patch")
    def test_campaign_update(self, mock_api, runner):
        mock_api.return_value = {"id": "1", "name": "Updated", "status": "paused"}
        result = runner.invoke(cli, [
            "campaign", "update", "1",
            "--name", "Updated", "--status", "paused"
        ])
        assert result.exit_code == 0
        assert "updated" in result.output

    @patch("cli_anything.redtrack.core.campaigns.api_delete")
    def test_campaign_delete(self, mock_api, runner):
        mock_api.return_value = {"status": "ok"}
        result = runner.invoke(cli, ["campaign", "delete", "1"])
        assert result.exit_code == 0
        assert "deleted" in result.output

    @patch("cli_anything.redtrack.core.campaigns.api_get")
    def test_campaign_links(self, mock_api, runner):
        mock_api.return_value = {
            "id": "1",
            "name": "Test",
            "tracking_url": "https://track.example.com/click/1"
        }
        result = runner.invoke(cli, ["campaign", "links", "1"])
        assert result.exit_code == 0

    @patch("cli_anything.redtrack.core.campaigns.api_get")
    def test_campaign_error_json(self, mock_api, runner):
        mock_api.side_effect = RuntimeError("RedTrack API error 404 on GET /campaigns/999: not found")
        result = runner.invoke(cli, ["--json", "campaign", "get", "999"])
        assert result.exit_code == 1
        data = json.loads(result.output)
        assert "error" in data

    @patch("cli_anything.redtrack.core.campaigns.api_get")
    def test_campaign_error_human(self, mock_api, runner):
        mock_api.side_effect = RuntimeError("Not found")
        result = runner.invoke(cli, ["campaign", "get", "999"])
        assert result.exit_code == 1


# ── CLI: Offer commands with mocked API ──────────────────────────

class TestOfferCommands:
    @patch("cli_anything.redtrack.core.offers.api_get")
    def test_offer_list_json(self, mock_api, runner):
        mock_api.return_value = [{"id": "1", "name": "Offer One", "payout": 5.0}]
        result = runner.invoke(cli, ["--json", "offer", "list"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data[0]["name"] == "Offer One"

    @patch("cli_anything.redtrack.core.offers.api_get")
    def test_offer_list_empty(self, mock_api, runner):
        mock_api.return_value = []
        result = runner.invoke(cli, ["offer", "list"])
        assert result.exit_code == 0
        assert "No offers" in result.output

    @patch("cli_anything.redtrack.core.offers.api_get")
    def test_offer_get(self, mock_api, runner):
        mock_api.return_value = {"id": "5", "name": "My Offer", "payout": 10.0}
        result = runner.invoke(cli, ["--json", "offer", "get", "5"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["id"] == "5"

    @patch("cli_anything.redtrack.core.offers.api_post")
    def test_offer_create(self, mock_api, runner):
        mock_api.return_value = {"id": "10", "name": "New Offer"}
        result = runner.invoke(cli, [
            "--json", "offer", "create",
            "--name", "New Offer",
            "--payout", "7.50"
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["id"] == "10"

    @patch("cli_anything.redtrack.core.offers.api_patch")
    def test_offer_update(self, mock_api, runner):
        mock_api.return_value = {"id": "5", "name": "Updated Offer"}
        result = runner.invoke(cli, ["offer", "update", "5", "--name", "Updated Offer"])
        assert result.exit_code == 0

    @patch("cli_anything.redtrack.core.offers.api_delete")
    def test_offer_delete(self, mock_api, runner):
        mock_api.return_value = {"status": "ok"}
        result = runner.invoke(cli, ["offer", "delete", "5"])
        assert result.exit_code == 0
        assert "deleted" in result.output


# ── CLI: Offer source commands with mocked API ────────────────────

class TestOfferSourceCommands:
    @patch("cli_anything.redtrack.core.offers.api_get")
    def test_offer_source_list_json(self, mock_api, runner):
        mock_api.return_value = [{"id": "1", "name": "MaxBounty"}]
        result = runner.invoke(cli, ["--json", "offer-source", "list"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data[0]["name"] == "MaxBounty"

    @patch("cli_anything.redtrack.core.offers.api_get")
    def test_offer_source_list_empty(self, mock_api, runner):
        mock_api.return_value = []
        result = runner.invoke(cli, ["offer-source", "list"])
        assert result.exit_code == 0
        assert "No offer sources" in result.output

    @patch("cli_anything.redtrack.core.offers.api_post")
    def test_offer_source_create(self, mock_api, runner):
        mock_api.return_value = {"id": "2", "name": "CJ Affiliate"}
        result = runner.invoke(cli, [
            "--json", "offer-source", "create",
            "--name", "CJ Affiliate"
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["name"] == "CJ Affiliate"

    @patch("cli_anything.redtrack.core.offers.api_delete")
    def test_offer_source_delete(self, mock_api, runner):
        mock_api.return_value = {"status": "ok"}
        result = runner.invoke(cli, ["offer-source", "delete", "2"])
        assert result.exit_code == 0


# ── CLI: Traffic channel commands ────────────────────────────────

class TestTrafficCommands:
    @patch("cli_anything.redtrack.core.traffic.api_get")
    def test_traffic_list_json(self, mock_api, runner):
        mock_api.return_value = [{"id": "1", "name": "Google Ads", "status": "active"}]
        result = runner.invoke(cli, ["--json", "traffic", "list"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data[0]["name"] == "Google Ads"

    @patch("cli_anything.redtrack.core.traffic.api_get")
    def test_traffic_list_empty(self, mock_api, runner):
        mock_api.return_value = []
        result = runner.invoke(cli, ["traffic", "list"])
        assert result.exit_code == 0
        assert "No traffic channels" in result.output

    @patch("cli_anything.redtrack.core.traffic.api_post")
    def test_traffic_create(self, mock_api, runner):
        mock_api.return_value = {"id": "3", "name": "Facebook Ads"}
        result = runner.invoke(cli, [
            "--json", "traffic", "create", "--name", "Facebook Ads"
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["name"] == "Facebook Ads"

    @patch("cli_anything.redtrack.core.traffic.api_delete")
    def test_traffic_delete(self, mock_api, runner):
        mock_api.return_value = {"status": "ok"}
        result = runner.invoke(cli, ["traffic", "delete", "3"])
        assert result.exit_code == 0


# ── CLI: Lander commands ──────────────────────────────────────────

class TestLanderCommands:
    @patch("cli_anything.redtrack.core.landers.api_get")
    def test_lander_list_json(self, mock_api, runner):
        mock_api.return_value = [{"id": "1", "name": "LP1", "status": "active"}]
        result = runner.invoke(cli, ["--json", "lander", "list"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data[0]["name"] == "LP1"

    @patch("cli_anything.redtrack.core.landers.api_get")
    def test_lander_list_empty(self, mock_api, runner):
        mock_api.return_value = []
        result = runner.invoke(cli, ["lander", "list"])
        assert result.exit_code == 0
        assert "No landers" in result.output

    @patch("cli_anything.redtrack.core.landers.api_post")
    def test_lander_create(self, mock_api, runner):
        mock_api.return_value = {"id": "7", "name": "Sales Page"}
        result = runner.invoke(cli, [
            "--json", "lander", "create",
            "--name", "Sales Page",
            "--url", "https://example.com/sales"
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["id"] == "7"

    @patch("cli_anything.redtrack.core.landers.api_delete")
    def test_lander_delete(self, mock_api, runner):
        mock_api.return_value = {"status": "ok"}
        result = runner.invoke(cli, ["lander", "delete", "7"])
        assert result.exit_code == 0


# ── CLI: Conversion commands ──────────────────────────────────────

class TestConversionCommands:
    @patch("cli_anything.redtrack.core.conversions.api_get")
    def test_conversion_list_json(self, mock_api, runner):
        mock_api.return_value = [
            {"id": "cv1", "click_id": "ck123", "status": "approved", "payout": 5.0}
        ]
        result = runner.invoke(cli, ["--json", "conversion", "list"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data[0]["status"] == "approved"

    @patch("cli_anything.redtrack.core.conversions.api_get")
    def test_conversion_list_empty(self, mock_api, runner):
        mock_api.return_value = []
        result = runner.invoke(cli, ["conversion", "list"])
        assert result.exit_code == 0
        assert "No conversions" in result.output

    @patch("cli_anything.redtrack.core.conversions.api_post")
    def test_conversion_upload(self, mock_api, runner):
        mock_api.return_value = {"status": "ok"}
        result = runner.invoke(cli, [
            "conversion", "upload",
            "--click-id", "ck123abc",
            "--status", "approved",
            "--payout", "10.00"
        ])
        assert result.exit_code == 0

    def test_conversion_types(self, runner):
        result = runner.invoke(cli, ["conversion", "types"])
        assert result.exit_code == 0
        assert "conversion" in result.output

    def test_conversion_types_json(self, runner):
        result = runner.invoke(cli, ["--json", "conversion", "types"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "conversion_types" in data
        assert len(data["conversion_types"]) > 0

    @patch("cli_anything.redtrack.core.conversions.api_get")
    def test_conversion_list_with_filters(self, mock_api, runner):
        mock_api.return_value = []
        result = runner.invoke(cli, [
            "conversion", "list",
            "--date-from", "2024-01-01",
            "--date-to", "2024-01-31",
            "--campaign-id", "42",
            "--status", "approved"
        ])
        assert result.exit_code == 0


# ── CLI: Report commands ──────────────────────────────────────────

class TestReportCommands:
    @patch("cli_anything.redtrack.core.reports.api_get")
    def test_report_general(self, mock_api, runner):
        mock_api.return_value = {"data": [], "totals": {}}
        result = runner.invoke(cli, [
            "--json", "report", "general",
            "--date-from", "2024-01-01",
            "--date-to", "2024-01-31"
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "data" in data

    @patch("cli_anything.redtrack.core.reports.api_get")
    def test_report_campaigns(self, mock_api, runner):
        mock_api.return_value = {"data": []}
        result = runner.invoke(cli, ["--json", "report", "campaigns"])
        assert result.exit_code == 0

    @patch("cli_anything.redtrack.core.reports.api_get")
    def test_report_clicks(self, mock_api, runner):
        mock_api.return_value = {"data": [], "total": 0}
        result = runner.invoke(cli, [
            "--json", "report", "clicks",
            "--campaign-id", "5"
        ])
        assert result.exit_code == 0

    @patch("cli_anything.redtrack.core.reports.api_get")
    def test_report_general_with_group_by(self, mock_api, runner):
        mock_api.return_value = {"data": []}
        result = runner.invoke(cli, [
            "report", "general",
            "--group-by", "country"
        ])
        assert result.exit_code == 0
        call_params = mock_api.call_args[1]["params"]
        assert call_params.get("group_by") == "country"


# ── CLI: Cost commands ────────────────────────────────────────────

class TestCostCommands:
    @patch("cli_anything.redtrack.core.costs.api_get")
    def test_cost_list(self, mock_api, runner):
        mock_api.return_value = []
        result = runner.invoke(cli, ["--json", "cost", "list"])
        assert result.exit_code == 0

    @patch("cli_anything.redtrack.core.costs.api_get")
    def test_cost_list_with_dates(self, mock_api, runner):
        mock_api.return_value = []
        result = runner.invoke(cli, [
            "cost", "list",
            "--date-from", "2024-01-01",
            "--date-to", "2024-01-31",
            "--campaign-id", "42"
        ])
        assert result.exit_code == 0
        call_params = mock_api.call_args[1]["params"]
        assert call_params.get("group_by") == "campaign"
        assert call_params.get("date_from") == "2024-01-01"
        assert call_params.get("campaign_id") == "42"


# ── Null response handling ─────────────────────────────────────────

class TestNullResponseHandling:
    def test_output_handles_none(self, runner):
        """CLI should not crash when API returns null."""
        with patch("requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.content = b"null"
            mock_resp.json.return_value = None
            mock_get.return_value = mock_resp
            result = runner.invoke(cli, ["campaign", "list"])
            assert result.exit_code == 0

    def test_output_handles_paginated_response(self, runner):
        """CLI should handle {items: [], total: N} paginated responses."""
        with patch("requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.content = b'{"items": [], "total": 0}'
            mock_resp.json.return_value = {"items": [], "total": 0}
            mock_get.return_value = mock_resp
            result = runner.invoke(cli, ["--json", "conversion", "list",
                                         "--date-from", "2024-01-01",
                                         "--date-to", "2024-01-31"])
            assert result.exit_code == 0


# ── get_cost_from_report ───────────────────────────────────────────

class TestGetCostFromReport:
    def test_cost_from_report(self):
        with patch("requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.content = b'[]'
            mock_resp.json.return_value = []
            mock_get.return_value = mock_resp
            from cli_anything.redtrack.core.costs import get_cost_from_report
            result = get_cost_from_report("key", "https://api.redtrack.io",
                                           date_from="2024-01-01", date_to="2024-01-31")
            call_url = mock_get.call_args[0][0]
            assert "/report" in call_url
            assert result == []


# ── CLI: Rule commands ────────────────────────────────────────────

class TestRuleCommands:
    @patch("cli_anything.redtrack.core.rules.api_get")
    def test_rule_list_json(self, mock_api, runner):
        mock_api.return_value = [{"id": "1", "name": "Pause on low ROI", "status": "active"}]
        result = runner.invoke(cli, ["--json", "rule", "list"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data[0]["name"] == "Pause on low ROI"

    @patch("cli_anything.redtrack.core.rules.api_get")
    def test_rule_list_empty(self, mock_api, runner):
        mock_api.return_value = []
        result = runner.invoke(cli, ["rule", "list"])
        assert result.exit_code == 0
        assert "No rules" in result.output

    @patch("cli_anything.redtrack.core.rules.api_get")
    def test_rule_get(self, mock_api, runner):
        mock_api.return_value = {"id": "5", "name": "Auto pause", "status": "active"}
        result = runner.invoke(cli, ["--json", "rule", "get", "5"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["id"] == "5"

    @patch("cli_anything.redtrack.core.rules.api_post")
    def test_rule_create(self, mock_api, runner):
        mock_api.return_value = {"id": "8", "name": "New Rule"}
        result = runner.invoke(cli, [
            "--json", "rule", "create",
            "--name", "New Rule",
            "--condition", '{"metric": "roi", "op": "<", "value": 0}',
            "--action", "pause_campaign"
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["id"] == "8"

    @patch("cli_anything.redtrack.core.rules.api_patch")
    def test_rule_update_enable(self, mock_api, runner):
        mock_api.return_value = {"id": "5", "status": "active"}
        result = runner.invoke(cli, ["rule", "update", "5", "--status", "active"])
        assert result.exit_code == 0
        assert "updated" in result.output

    @patch("cli_anything.redtrack.core.rules.api_delete")
    def test_rule_delete(self, mock_api, runner):
        mock_api.return_value = {"status": "ok"}
        result = runner.invoke(cli, ["rule", "delete", "5"])
        assert result.exit_code == 0
        assert "deleted" in result.output


# ── CLI: Domain commands ──────────────────────────────────────────

class TestDomainCommands:
    @patch("cli_anything.redtrack.redtrack_cli.api_get")
    def test_domain_list_json(self, mock_api, runner):
        mock_api.return_value = [{"id": "1", "domain": "track.example.com"}]
        result = runner.invoke(cli, ["--json", "domain", "list"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data[0]["domain"] == "track.example.com"

    @patch("cli_anything.redtrack.redtrack_cli.api_get")
    def test_domain_list_empty(self, mock_api, runner):
        mock_api.return_value = []
        result = runner.invoke(cli, ["domain", "list"])
        assert result.exit_code == 0
        assert "No custom domains" in result.output

    @patch("cli_anything.redtrack.redtrack_cli.api_post")
    def test_domain_add(self, mock_api, runner):
        mock_api.return_value = {"id": "2", "domain": "clicks.mysite.com"}
        result = runner.invoke(cli, [
            "--json", "domain", "add", "--domain", "clicks.mysite.com"
        ])
        assert result.exit_code == 0

    @patch("cli_anything.redtrack.redtrack_cli.api_get")
    def test_domain_list_human(self, mock_api, runner):
        mock_api.return_value = [{"id": "1", "domain": "track.example.com"}]
        result = runner.invoke(cli, ["domain", "list"])
        assert result.exit_code == 0
        assert "track.example.com" in result.output


# ── CLI: Account command ──────────────────────────────────────────

class TestAccountCommands:
    @patch("cli_anything.redtrack.redtrack_cli.api_get")
    def test_account_info_json(self, mock_api, runner):
        mock_api.return_value = {
            "id": "user1", "email": "test@example.com", "plan": "Pro"
        }
        result = runner.invoke(cli, ["--json", "account", "info"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["email"] == "test@example.com"

    @patch("cli_anything.redtrack.redtrack_cli.api_get")
    def test_account_info_human(self, mock_api, runner):
        mock_api.return_value = {
            "id": "user1", "email": "test@example.com", "plan": "Pro"
        }
        result = runner.invoke(cli, ["account", "info"])
        assert result.exit_code == 0
        assert "Account Info" in result.output

    @patch("cli_anything.redtrack.redtrack_cli.api_get")
    def test_account_info_error(self, mock_api, runner):
        mock_api.side_effect = RuntimeError("RedTrack API error 401: Unauthorized")
        result = runner.invoke(cli, ["account", "info"])
        assert result.exit_code == 1


# ── Core module: campaigns ────────────────────────────────────────

class TestCoreCampaigns:
    @patch("cli_anything.redtrack.core.campaigns.api_get")
    def test_list_campaigns_params(self, mock_api):
        from cli_anything.redtrack.core.campaigns import list_campaigns
        mock_api.return_value = []
        list_campaigns("key", "https://api.redtrack.io",
                       date_from="2024-01-01", date_to="2024-01-31",
                       limit=50, offset=10)
        call_params = mock_api.call_args[1]["params"]
        assert call_params["date_from"] == "2024-01-01"
        assert call_params["limit"] == 50
        assert call_params["offset"] == 10

    @patch("cli_anything.redtrack.core.campaigns.api_post")
    def test_create_campaign_payload(self, mock_api):
        from cli_anything.redtrack.core.campaigns import create_campaign
        mock_api.return_value = {"id": "1"}
        create_campaign("key", "https://api.redtrack.io",
                        name="Test", traffic_channel_id="5",
                        domain="track.io", cost_type="cpc", cost_value=0.5)
        data = mock_api.call_args[1]["data"]
        assert data["name"] == "Test"
        assert data["traffic_channel_id"] == "5"
        assert data["cost_type"] == "cpc"
        assert data["cost_value"] == 0.5

    @patch("cli_anything.redtrack.core.campaigns.api_patch")
    def test_update_campaign_partial(self, mock_api):
        from cli_anything.redtrack.core.campaigns import update_campaign
        mock_api.return_value = {"id": "1"}
        update_campaign("key", "https://api.redtrack.io", "1", status="paused")
        data = mock_api.call_args[1]["data"]
        assert data["status"] == "paused"
        assert "name" not in data


# ── Core module: conversions ──────────────────────────────────────

class TestCoreConversions:
    @patch("cli_anything.redtrack.core.conversions.api_post")
    def test_upload_conversion_payload(self, mock_api):
        from cli_anything.redtrack.core.conversions import upload_conversion
        mock_api.return_value = {"status": "ok"}
        upload_conversion("key", "https://api.redtrack.io",
                          click_id="ck123", status="approved",
                          payout=10.0, conversion_type="sale")
        data = mock_api.call_args[1]["data"]
        assert data["click_id"] == "ck123"
        assert data["status"] == "approved"
        assert data["payout"] == 10.0
        assert data["type"] == "sale"

    def test_get_conversion_types(self):
        from cli_anything.redtrack.core.conversions import get_conversion_types
        types = get_conversion_types()
        assert isinstance(types, list)
        assert "conversion" in types
        assert "sale" in types
        assert "lead" in types


# ── Error handling: missing API key ──────────────────────────────

class TestMissingApiKey:
    def test_campaign_list_no_key(self, runner, monkeypatch):
        monkeypatch.delenv("REDTRACK_API_KEY", raising=False)
        result = runner.invoke(cli, ["campaign", "list"])
        assert result.exit_code == 1

    def test_campaign_list_no_key_json(self, runner, monkeypatch):
        monkeypatch.delenv("REDTRACK_API_KEY", raising=False)
        result = runner.invoke(cli, ["--json", "campaign", "list"])
        assert result.exit_code == 1
        data = json.loads(result.output)
        assert "error" in data
