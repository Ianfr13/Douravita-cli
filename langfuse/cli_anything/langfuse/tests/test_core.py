"""Unit tests for cli-anything-langfuse core modules.

All tests use synthetic data — no external dependencies or API calls.
"""

import base64
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


# ══════════════════════════════════════════════════════════════════════
# CONFIG TESTS
# ══════════════════════════════════════════════════════════════════════


class TestConfig:
    """Tests for utils/config.py."""

    def setup_method(self):
        """Create a temp config directory for each test."""
        self._tmpdir = tempfile.mkdtemp()
        self._config_dir = Path(self._tmpdir) / ".cli-anything-langfuse"
        self._config_file = self._config_dir / "config.json"

    def teardown_method(self):
        import shutil
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def _patch_config(self):
        """Patch config module to use temp directory."""
        import cli_anything.langfuse.utils.config as cfg
        return (
            patch.object(cfg, "CONFIG_DIR", self._config_dir),
            patch.object(cfg, "CONFIG_FILE", self._config_file),
        )

    def test_load_empty_config(self):
        from cli_anything.langfuse.utils.config import _load_config
        p1, p2 = self._patch_config()
        with p1, p2:
            config = _load_config()
            assert config == {"profiles": {}, "active_profile": "default"}

    def test_set_and_get_profile(self):
        from cli_anything.langfuse.utils.config import set_profile, get_profile
        p1, p2 = self._patch_config()
        with p1, p2:
            set_profile("test", public_key="pk-test", secret_key="sk-test",
                         base_url="https://test.langfuse.com")
            prof = get_profile("test")
            assert prof["public_key"] == "pk-test"
            assert prof["secret_key"] == "sk-test"
            assert prof["base_url"] == "https://test.langfuse.com"

    def test_list_profiles(self):
        from cli_anything.langfuse.utils.config import set_profile, list_profiles
        p1, p2 = self._patch_config()
        with p1, p2:
            set_profile("prod", public_key="pk-prod", secret_key="sk-prod")
            set_profile("staging", public_key="pk-staging", secret_key="sk-staging")
            profiles = list_profiles()
            assert len(profiles) == 2
            names = {p["name"] for p in profiles}
            assert names == {"prod", "staging"}

    def test_delete_profile(self):
        from cli_anything.langfuse.utils.config import set_profile, delete_profile, list_profiles
        p1, p2 = self._patch_config()
        with p1, p2:
            set_profile("temp", public_key="pk-temp", secret_key="sk-temp")
            assert delete_profile("temp") is True
            assert delete_profile("nonexistent") is False
            assert len(list_profiles()) == 0

    def test_active_profile(self):
        from cli_anything.langfuse.utils.config import set_profile, set_active_profile, get_profile
        p1, p2 = self._patch_config()
        with p1, p2:
            set_profile("default", public_key="pk-def", secret_key="sk-def")
            set_profile("prod", public_key="pk-prod", secret_key="sk-prod")
            set_active_profile("prod")
            # When no profile specified, should use active
            prof = get_profile()
            assert prof["public_key"] == "pk-prod"

    def test_resolve_credentials_priority(self):
        """CLI flags > env vars > config profile."""
        from cli_anything.langfuse.utils.config import resolve_credentials, set_profile
        p1, p2 = self._patch_config()
        # Clear real env vars to isolate test
        clean_env = {k: "" for k in ["LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_BASE_URL", "LANGFUSE_PROFILE"]}
        with p1, p2, patch.dict(os.environ, clean_env):
            set_profile("default", public_key="pk-config", secret_key="sk-config",
                         base_url="https://config.com")

            # Config only
            creds = resolve_credentials()
            assert creds["public_key"] == "pk-config"

            # Env overrides config
            with patch.dict(os.environ, {"LANGFUSE_PUBLIC_KEY": "pk-env"}):
                creds = resolve_credentials()
                assert creds["public_key"] == "pk-env"
                assert creds["secret_key"] == "sk-config"  # falls back to config

            # Flag overrides env
            with patch.dict(os.environ, {"LANGFUSE_PUBLIC_KEY": "pk-env"}):
                creds = resolve_credentials(public_key="pk-flag")
                assert creds["public_key"] == "pk-flag"

    def test_mask_key(self):
        from cli_anything.langfuse.utils.config import _mask_key
        assert _mask_key("") == "(not set)"
        assert _mask_key("pk-lf-abcdef12345") == "pk-lf-abcd****"
        assert _mask_key("short") == "shor****"

    def test_resolve_credentials_with_profile(self):
        from cli_anything.langfuse.utils.config import resolve_credentials, set_profile
        p1, p2 = self._patch_config()
        clean_env = {k: "" for k in ["LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_BASE_URL", "LANGFUSE_PROFILE"]}
        with p1, p2, patch.dict(os.environ, clean_env):
            set_profile("staging", public_key="pk-staging", secret_key="sk-staging",
                         base_url="https://staging.langfuse.com")
            creds = resolve_credentials(profile="staging")
            assert creds["public_key"] == "pk-staging"
            assert creds["base_url"] == "https://staging.langfuse.com"

    def test_default_base_url(self):
        from cli_anything.langfuse.utils.config import resolve_credentials
        p1, p2 = self._patch_config()
        clean_env = {k: "" for k in ["LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_BASE_URL", "LANGFUSE_PROFILE"]}
        with p1, p2, patch.dict(os.environ, clean_env):
            creds = resolve_credentials(public_key="pk", secret_key="sk")
            assert creds["base_url"] == "https://cloud.langfuse.com"


# ══════════════════════════════════════════════════════════════════════
# BACKEND CLIENT TESTS
# ══════════════════════════════════════════════════════════════════════


class TestLangfuseClient:
    """Tests for utils/langfuse_backend.py."""

    def test_init_valid(self):
        from cli_anything.langfuse.utils.langfuse_backend import LangfuseClient
        client = LangfuseClient("pk-test", "sk-test", "https://api.langfuse.com")
        assert client.public_key == "pk-test"
        assert client.base_url == "https://api.langfuse.com"
        expected_auth = base64.b64encode(b"pk-test:sk-test").decode()
        assert client._auth_header == f"Basic {expected_auth}"

    def test_init_missing_keys(self):
        from cli_anything.langfuse.utils.langfuse_backend import LangfuseClient
        with pytest.raises(ValueError, match="API keys are required"):
            LangfuseClient("", "", "https://api.langfuse.com")

    def test_init_strips_trailing_slash(self):
        from cli_anything.langfuse.utils.langfuse_backend import LangfuseClient
        client = LangfuseClient("pk", "sk", "https://api.langfuse.com/")
        assert client.base_url == "https://api.langfuse.com"

    def test_parse_error_message_json(self):
        from cli_anything.langfuse.utils.langfuse_backend import _parse_error_message
        body = json.dumps({"message": "Not found"})
        assert _parse_error_message(404, body) == "Not found"

    def test_parse_error_message_plain(self):
        from cli_anything.langfuse.utils.langfuse_backend import _parse_error_message
        assert _parse_error_message(401, "") == "Unauthorized — check your API keys"

    def test_parse_error_message_unknown(self):
        from cli_anything.langfuse.utils.langfuse_backend import _parse_error_message
        assert "999" in _parse_error_message(999, "")

    def test_parse_error_message_invalid_json(self):
        from cli_anything.langfuse.utils.langfuse_backend import _parse_error_message
        assert _parse_error_message(500, "not json{") == "not json{"

    def test_api_error_attributes(self):
        from cli_anything.langfuse.utils.langfuse_backend import LangfuseAPIError
        err = LangfuseAPIError(403, "Forbidden", '{"detail": "no access"}')
        assert err.status_code == 403
        assert "403" in str(err)
        assert err.body == '{"detail": "no access"}'


# ══════════════════════════════════════════════════════════════════════
# FORMATTERS TESTS
# ══════════════════════════════════════════════════════════════════════


class TestFormatters:
    """Tests for utils/formatters.py."""

    def test_format_timestamp_iso_z(self):
        from cli_anything.langfuse.utils.formatters import format_timestamp
        result = format_timestamp("2024-01-15T10:30:00Z")
        assert "2024-01-15" in result
        assert "10:30" in result

    def test_format_timestamp_none(self):
        from cli_anything.langfuse.utils.formatters import format_timestamp
        assert format_timestamp(None) == "-"

    def test_format_cost_small(self):
        from cli_anything.langfuse.utils.formatters import format_cost
        assert format_cost(0.001) == "$0.0010"

    def test_format_cost_normal(self):
        from cli_anything.langfuse.utils.formatters import format_cost
        assert format_cost(1.50) == "$1.50"

    def test_format_cost_none(self):
        from cli_anything.langfuse.utils.formatters import format_cost
        assert format_cost(None) == "-"

    def test_format_latency_ms(self):
        from cli_anything.langfuse.utils.formatters import format_latency
        assert format_latency(0.5) == "500ms"

    def test_format_latency_seconds(self):
        from cli_anything.langfuse.utils.formatters import format_latency
        assert format_latency(2.5) == "2.50s"

    def test_format_latency_none(self):
        from cli_anything.langfuse.utils.formatters import format_latency
        assert format_latency(None) == "-"

    def test_truncate_short(self):
        from cli_anything.langfuse.utils.formatters import truncate
        assert truncate("hello", 20) == "hello"

    def test_truncate_long(self):
        from cli_anything.langfuse.utils.formatters import truncate
        result = truncate("a" * 100, 20)
        assert len(result) == 20
        assert result.endswith("...")

    def test_truncate_none(self):
        from cli_anything.langfuse.utils.formatters import truncate
        assert truncate(None) == "-"

    def test_truncate_newlines(self):
        from cli_anything.langfuse.utils.formatters import truncate
        assert "\n" not in truncate("line1\nline2", 30)


# ══════════════════════════════════════════════════════════════════════
# CORE MODULE PARAMETER TESTS
# ══════════════════════════════════════════════════════════════════════


class TestCoreModuleParams:
    """Test that core modules construct correct API parameters."""

    def _mock_client(self):
        """Create a mock LangfuseClient that records calls."""
        client = MagicMock()
        client.get.return_value = {"data": [], "meta": {"totalCount": 0}}
        client.post.return_value = {"id": "test-id"}
        client.delete.return_value = {}
        return client

    def test_traces_list_params(self):
        from cli_anything.langfuse.core.traces import list_traces
        client = self._mock_client()
        list_traces(client, page=2, limit=10, name="test", user_id="u1", tags=["prod"])
        client.get.assert_called_once()
        args = client.get.call_args
        assert args[0][0] == "/api/public/traces"
        params = args[1]["params"] if "params" in args[1] else args[0][1]
        assert params["page"] == 2
        assert params["limit"] == 10
        assert params["name"] == "test"
        assert params["tags"] == ["prod"]

    def test_traces_get_path(self):
        from cli_anything.langfuse.core.traces import get_trace
        client = self._mock_client()
        get_trace(client, "trace-abc")
        client.get.assert_called_with("/api/public/traces/trace-abc")

    def test_scores_create_body(self):
        from cli_anything.langfuse.core.scores import create_score
        client = self._mock_client()
        create_score(client, trace_id="t1", name="quality", value=0.95,
                     observation_id="o1", comment="great")
        client.post.assert_called_once()
        body = client.post.call_args[1]["body"]
        assert body["traceId"] == "t1"
        assert body["name"] == "quality"
        assert body["value"] == 0.95
        assert body["observationId"] == "o1"
        assert body["comment"] == "great"

    def test_prompts_create_body(self):
        from cli_anything.langfuse.core.prompts import create_prompt
        client = self._mock_client()
        create_prompt(client, name="test-prompt", prompt="You are {{role}}",
                      prompt_type="text", labels=["production"], tags=["v1"])
        body = client.post.call_args[1]["body"]
        assert body["name"] == "test-prompt"
        assert body["prompt"] == "You are {{role}}"
        assert body["type"] == "text"
        assert body["labels"] == ["production"]

    def test_datasets_create_body(self):
        from cli_anything.langfuse.core.datasets import create_dataset
        client = self._mock_client()
        create_dataset(client, name="eval-set", description="QA pairs")
        body = client.post.call_args[1]["body"]
        assert body["name"] == "eval-set"
        assert body["description"] == "QA pairs"

    def test_dataset_items_create_body(self):
        from cli_anything.langfuse.core.datasets import create_dataset_item
        client = self._mock_client()
        create_dataset_item(
            client, dataset_name="eval-set",
            input_data={"question": "What is AI?"},
            expected_output={"answer": "Artificial Intelligence"},
        )
        body = client.post.call_args[1]["body"]
        assert body["datasetName"] == "eval-set"
        assert body["input"]["question"] == "What is AI?"
        assert body["expectedOutput"]["answer"] == "Artificial Intelligence"

    def test_models_create_body(self):
        from cli_anything.langfuse.core.models import create_model
        client = self._mock_client()
        create_model(client, model_name="gpt-4o", match_pattern="gpt-4o.*",
                     unit="TOKENS", input_price=0.01)
        body = client.post.call_args[1]["body"]
        assert body["modelName"] == "gpt-4o"
        assert body["matchPattern"] == "gpt-4o.*"
        assert body["inputPrice"] == 0.01

    def test_comments_create_body(self):
        from cli_anything.langfuse.core.comments import create_comment
        client = self._mock_client()
        create_comment(client, object_type="TRACE", object_id="t1", content="looks good")
        body = client.post.call_args[1]["body"]
        assert body["objectType"] == "TRACE"
        assert body["objectId"] == "t1"
        assert body["content"] == "looks good"

    def test_observations_list_params(self):
        from cli_anything.langfuse.core.observations import list_observations
        client = self._mock_client()
        list_observations(client, trace_id="t1", obs_type="GENERATION", limit=5)
        params = client.get.call_args[1]["params"] if "params" in client.get.call_args[1] else client.get.call_args[0][1]
        assert params["traceId"] == "t1"
        assert params["type"] == "GENERATION"
        assert params["limit"] == 5

    def test_sessions_list_path(self):
        from cli_anything.langfuse.core.sessions import list_sessions
        client = self._mock_client()
        list_sessions(client, page=1, limit=10)
        assert client.get.call_args[0][0] == "/api/public/sessions"
