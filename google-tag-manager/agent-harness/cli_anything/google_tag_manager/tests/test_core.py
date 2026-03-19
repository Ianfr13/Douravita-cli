"""Unit tests for cli_anything.google_tag_manager core modules.

These tests use mocked API services — no external dependencies or network calls required.
Run with: python3 -m pytest cli_anything/google_tag_manager/tests/test_core.py -v
"""
import os
import json
import tempfile
import pytest
from unittest.mock import MagicMock, patch, call

from cli_anything.google_tag_manager.core.session import Session
from cli_anything.google_tag_manager.core import accounts as acct_mod
from cli_anything.google_tag_manager.core import containers as cont_mod
from cli_anything.google_tag_manager.core import workspaces as ws_mod
from cli_anything.google_tag_manager.core import tags as tags_mod
from cli_anything.google_tag_manager.core import triggers as trig_mod
from cli_anything.google_tag_manager.core import variables as var_mod
from cli_anything.google_tag_manager.core import permissions as perm_mod
from cli_anything.google_tag_manager.core import folders as folder_mod
from cli_anything.google_tag_manager.core import environments as env_mod
from cli_anything.google_tag_manager.core import versions as ver_mod


# ── Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def tmp_session_file(tmp_path):
    """Provide a temporary session file path."""
    return str(tmp_path / "session.json")


@pytest.fixture
def session(tmp_session_file):
    """Session instance backed by a temporary file."""
    return Session(session_file=tmp_session_file)


def make_service():
    """Create a deep MagicMock representing the GTM API service."""
    svc = MagicMock()
    return svc


def make_http_error(code: int = 403, message: str = "Forbidden"):
    """Create a mock HttpError."""
    from googleapiclient.errors import HttpError
    resp = MagicMock()
    resp.status = code
    content = json.dumps({"error": {"code": code, "message": message}}).encode()
    return HttpError(resp=resp, content=content)


# ── Session Tests ─────────────────────────────────────────────────────

class TestSession:
    def test_session_default_init(self, tmp_session_file):
        sess = Session(session_file=tmp_session_file)
        assert sess.account_id is None
        assert sess.container_id is None
        assert sess.workspace_id is None

    def test_session_set_and_get_account_id(self, session):
        session.account_id = "12345"
        session.save()
        # Reload from disk
        sess2 = Session(session_file=session.session_file)
        assert sess2.account_id == "12345"

    def test_session_set_and_get_container_id(self, session):
        session.container_id = "67890"
        session.save()
        sess2 = Session(session_file=session.session_file)
        assert sess2.container_id == "67890"

    def test_session_set_and_get_workspace_id(self, session):
        session.workspace_id = "3"
        session.save()
        sess2 = Session(session_file=session.session_file)
        assert sess2.workspace_id == "3"

    def test_session_env_override(self, session, monkeypatch):
        session.account_id = "from_file"
        session.save()
        monkeypatch.setenv("GTM_ACCOUNT_ID", "from_env")
        # env var takes priority
        assert session.account_id == "from_env"

    def test_session_require_account_raises(self, session):
        with pytest.raises(ValueError, match="Account ID"):
            session.require_account()

    def test_session_require_container_raises(self, session):
        session.account_id = "12345"
        with pytest.raises(ValueError, match="Container ID"):
            session.require_container()

    def test_session_require_workspace_raises(self, session):
        session.account_id = "12345"
        session.container_id = "67890"
        with pytest.raises(ValueError, match="Workspace ID"):
            session.require_workspace()

    def test_session_set_context(self, session):
        session.set_context(account_id="111", container_id="222", workspace_id="3")
        assert session.account_id == "111"
        assert session.container_id == "222"
        assert session.workspace_id == "3"

    def test_session_clear(self, session):
        session.account_id = "123"
        session.container_id = "456"
        session.save()
        session.clear()
        sess2 = Session(session_file=session.session_file)
        assert sess2.account_id is None
        assert sess2.container_id is None

    def test_session_to_dict(self, session):
        session.account_id = "999"
        d = session.to_dict()
        assert d["account_id"] == "999"
        assert "session_file" in d
        assert "credentials_file" in d


# ── Account Tests ─────────────────────────────────────────────────────

class TestAccounts:
    def test_list_accounts_success(self):
        svc = make_service()
        svc.accounts().list().execute.return_value = {
            "account": [{"accountId": "1", "name": "Test Account"}]
        }
        result = acct_mod.list_accounts(svc)
        assert len(result) == 1
        assert result[0]["accountId"] == "1"

    def test_list_accounts_empty(self):
        svc = make_service()
        svc.accounts().list().execute.return_value = {}
        result = acct_mod.list_accounts(svc)
        assert result == []

    def test_get_account_validates_id(self):
        svc = make_service()
        with pytest.raises(ValueError, match="account_id"):
            acct_mod.get_account(svc, "")

    def test_get_account_success(self):
        svc = make_service()
        svc.accounts().get().execute.return_value = {
            "accountId": "123", "name": "My Account"
        }
        result = acct_mod.get_account(svc, "123")
        assert result["accountId"] == "123"

    def test_update_account_name(self):
        svc = make_service()
        svc.accounts().get().execute.return_value = {
            "accountId": "123", "name": "Old", "shareData": False
        }
        svc.accounts().update().execute.return_value = {
            "accountId": "123", "name": "New"
        }
        result = acct_mod.update_account(svc, "123", name="New")
        assert result["name"] == "New"

    def test_account_format_row(self):
        acct = {"accountId": "1", "name": "Foo", "shareData": True}
        row = acct_mod.format_account_row(acct)
        assert row[0] == "1"
        assert row[1] == "Foo"
        assert row[2] == "True"

    def test_list_accounts_http_error(self):
        svc = make_service()
        svc.accounts().list().execute.side_effect = make_http_error(403)
        with pytest.raises(RuntimeError, match="GTM API Error"):
            acct_mod.list_accounts(svc)


# ── Container Tests ───────────────────────────────────────────────────

class TestContainers:
    def test_list_containers_success(self):
        svc = make_service()
        svc.accounts().containers().list().execute.return_value = {
            "container": [{"containerId": "1", "name": "Web Container"}]
        }
        result = cont_mod.list_containers(svc, "12345")
        assert len(result) == 1

    def test_create_container_validates_name(self):
        svc = make_service()
        with pytest.raises(ValueError, match="name"):
            cont_mod.create_container(svc, "123", "", ["web"])

    def test_create_container_validates_context(self):
        svc = make_service()
        with pytest.raises(ValueError, match="Invalid usage_context"):
            cont_mod.create_container(svc, "123", "My Container", ["invalid_ctx"])

    def test_create_container_valid_contexts(self):
        svc = make_service()
        svc.accounts().containers().create().execute.return_value = {
            "containerId": "5", "name": "Mobile App"
        }
        result = cont_mod.create_container(svc, "123", "Mobile App",
                                            ["androidSdk5", "iosSdk5"])
        assert result["containerId"] == "5"

    def test_create_container_validates_empty_context(self):
        svc = make_service()
        with pytest.raises(ValueError, match="usage_context"):
            cont_mod.create_container(svc, "123", "My Container", [])

    def test_delete_container_returns_dict(self):
        svc = make_service()
        svc.accounts().containers().delete().execute.return_value = None
        result = cont_mod.delete_container(svc, "123", "456")
        assert result["deleted"] is True
        assert result["container_id"] == "456"

    def test_get_snippet_success(self):
        svc = make_service()
        svc.accounts().containers().snippet().execute.return_value = {
            "snippet": "<script>...</script>"
        }
        result = cont_mod.get_snippet(svc, "123", "456")
        assert "snippet" in result

    def test_container_format_row(self):
        c = {
            "containerId": "1", "name": "My Site", "publicId": "GTM-ABC123",
            "usageContext": ["web", "amp"]
        }
        row = cont_mod.format_container_row(c)
        assert row[0] == "1"
        assert row[1] == "My Site"
        assert row[2] == "GTM-ABC123"
        assert "web" in row[3]


# ── Workspace Tests ───────────────────────────────────────────────────

class TestWorkspaces:
    def test_list_workspaces_success(self):
        svc = make_service()
        svc.accounts().containers().workspaces().list().execute.return_value = {
            "workspace": [{"workspaceId": "3", "name": "Default Workspace"}]
        }
        result = ws_mod.list_workspaces(svc, "12345", "67890")
        assert len(result) == 1
        assert result[0]["workspaceId"] == "3"

    def test_create_workspace_validates_name(self):
        svc = make_service()
        with pytest.raises(ValueError, match="name"):
            ws_mod.create_workspace(svc, "123", "456", "")

    def test_workspace_status_success(self):
        svc = make_service()
        svc.accounts().containers().workspaces().getStatus().execute.return_value = {
            "workspaceChange": []
        }
        result = ws_mod.workspace_status(svc, "123", "456", "3")
        assert "workspaceChange" in result

    def test_sync_workspace_success(self):
        svc = make_service()
        svc.accounts().containers().workspaces().sync().execute.return_value = {
            "syncStatus": {"mergeConflict": []}
        }
        result = ws_mod.sync_workspace(svc, "123", "456", "3")
        assert "syncStatus" in result

    def test_create_version_success(self):
        svc = make_service()
        svc.accounts().containers().workspaces().create_version().execute.return_value = {
            "containerVersion": {"containerVersionId": "1", "name": "v1.0"}
        }
        result = ws_mod.create_version(svc, "123", "456", "3", name="v1.0")
        assert "containerVersion" in result

    def test_workspace_format_row(self):
        ws = {
            "workspaceId": "3",
            "name": "Dev Workspace",
            "description": "For development",
            "fingerprint": "abcdef123456789012",
        }
        row = ws_mod.format_workspace_row(ws)
        assert row[0] == "3"
        assert row[1] == "Dev Workspace"
        assert len(row[3]) <= 12  # fingerprint truncated


# ── Tag Tests ─────────────────────────────────────────────────────────

class TestTags:
    def test_list_tags_success(self):
        svc = make_service()
        svc.accounts().containers().workspaces().tags().list().execute.return_value = {
            "tag": [{"tagId": "1", "name": "GA4", "type": "googtag"}]
        }
        result = tags_mod.list_tags(svc, "123", "456", "3")
        assert len(result) == 1
        assert result[0]["tagId"] == "1"

    def test_create_tag_validates_name(self):
        svc = make_service()
        with pytest.raises(ValueError, match="name"):
            tags_mod.create_tag(svc, "123", "456", "3", "", "html")

    def test_create_tag_validates_type(self):
        svc = make_service()
        with pytest.raises(ValueError, match="tag_type"):
            tags_mod.create_tag(svc, "123", "456", "3", "My Tag", "")

    def test_create_tag_validates_firing_option(self):
        svc = make_service()
        with pytest.raises(ValueError, match="tag_firing_option"):
            tags_mod.create_tag(svc, "123", "456", "3", "My Tag", "html",
                                tag_firing_option="invalid_option")

    def test_delete_tag_returns_dict(self):
        svc = make_service()
        svc.accounts().containers().workspaces().tags().delete().execute.return_value = None
        result = tags_mod.delete_tag(svc, "123", "456", "3", "99")
        assert result["deleted"] is True
        assert result["tag_id"] == "99"

    def test_tag_format_row(self):
        tag = {
            "tagId": "1",
            "name": "GA4 Config",
            "type": "googtag",
            "firingTriggerId": ["2345"],
            "tagFiringOption": "oncePerEvent",
        }
        row = tags_mod.format_tag_row(tag)
        assert row[0] == "1"
        assert row[1] == "GA4 Config"
        assert row[2] == "googtag"

    def test_create_tag_with_parameters(self):
        svc = make_service()
        svc.accounts().containers().workspaces().tags().create().execute.return_value = {
            "tagId": "10", "name": "GA4", "type": "googtag"
        }
        params = [{"type": "template", "key": "tagId", "value": "G-XXXXXX"}]
        result = tags_mod.create_tag(svc, "123", "456", "3", "GA4", "googtag",
                                      parameters=params, firing_trigger_ids=["22"])
        assert result["tagId"] == "10"

    def test_tag_format_row_truncates_long_triggers(self):
        tag = {
            "tagId": "1",
            "name": "Tag",
            "type": "html",
            "firingTriggerId": ["111", "222", "333", "444", "555"],
            "tagFiringOption": "unlimited",
        }
        row = tags_mod.format_tag_row(tag)
        assert len(row[3]) <= 30


# ── Trigger Tests ─────────────────────────────────────────────────────

class TestTriggers:
    def test_list_triggers_success(self):
        svc = make_service()
        svc.accounts().containers().workspaces().triggers().list().execute.return_value = {
            "trigger": [{"triggerId": "5", "name": "All Pages", "type": "pageview"}]
        }
        result = trig_mod.list_triggers(svc, "123", "456", "3")
        assert len(result) == 1
        assert result[0]["type"] == "pageview"

    def test_create_trigger_validates_name(self):
        svc = make_service()
        with pytest.raises(ValueError, match="name"):
            trig_mod.create_trigger(svc, "123", "456", "3", "", "pageview")

    def test_create_trigger_validates_type(self):
        svc = make_service()
        with pytest.raises(ValueError, match="trigger_type"):
            trig_mod.create_trigger(svc, "123", "456", "3", "My Trigger", "")

    def test_delete_trigger_returns_dict(self):
        svc = make_service()
        svc.accounts().containers().workspaces().triggers().delete().execute.return_value = None
        result = trig_mod.delete_trigger(svc, "123", "456", "3", "55")
        assert result["deleted"] is True
        assert result["trigger_id"] == "55"

    def test_trigger_format_row(self):
        trig = {"triggerId": "5", "name": "All Pages", "type": "pageview"}
        row = trig_mod.format_trigger_row(trig)
        assert row == ["5", "All Pages", "pageview"]


# ── Variable Tests ────────────────────────────────────────────────────

class TestVariables:
    def test_list_variables_success(self):
        svc = make_service()
        svc.accounts().containers().workspaces().variables().list().execute.return_value = {
            "variable": [{"variableId": "10", "name": "GA ID", "type": "v"}]
        }
        result = var_mod.list_variables(svc, "123", "456", "3")
        assert len(result) == 1
        assert result[0]["type"] == "v"

    def test_create_variable_validates_name(self):
        svc = make_service()
        with pytest.raises(ValueError, match="name"):
            var_mod.create_variable(svc, "123", "456", "3", "", "v")

    def test_create_variable_validates_type(self):
        svc = make_service()
        with pytest.raises(ValueError, match="variable_type"):
            var_mod.create_variable(svc, "123", "456", "3", "My Var", "")

    def test_delete_variable_returns_dict(self):
        svc = make_service()
        svc.accounts().containers().workspaces().variables().delete().execute.return_value = None
        result = var_mod.delete_variable(svc, "123", "456", "3", "10")
        assert result["deleted"] is True
        assert result["variable_id"] == "10"

    def test_variable_format_row(self):
        var = {"variableId": "10", "name": "GA Tracking ID", "type": "v"}
        row = var_mod.format_variable_row(var)
        assert row == ["10", "GA Tracking ID", "v"]


# ── Permission Tests ──────────────────────────────────────────────────

class TestPermissions:
    def test_create_permission_validates_email(self):
        svc = make_service()
        with pytest.raises(ValueError, match="email"):
            perm_mod.create_permission(svc, "123", "not_an_email")

    def test_create_permission_validates_account_access(self):
        svc = make_service()
        with pytest.raises(ValueError, match="account_access"):
            perm_mod.create_permission(svc, "123", "user@example.com",
                                        account_access="superadmin")

    def test_create_permission_validates_container_access(self):
        svc = make_service()
        with pytest.raises(ValueError, match="containerId"):
            perm_mod.create_permission(
                svc, "123", "user@example.com",
                container_accesses=[{"permission": "edit"}]  # missing containerId
            )

    def test_create_permission_validates_container_permission(self):
        svc = make_service()
        with pytest.raises(ValueError, match="container permission"):
            perm_mod.create_permission(
                svc, "123", "user@example.com",
                container_accesses=[{"containerId": "456", "permission": "superpower"}]
            )

    def test_delete_permission_returns_dict(self):
        svc = make_service()
        svc.accounts().user_permissions().delete().execute.return_value = None
        result = perm_mod.delete_permission(svc, "123", "user_perm_99")
        assert result["revoked"] is True
        assert result["user_permission_id"] == "user_perm_99"

    def test_permission_format_row(self):
        perm = {
            "path": "accounts/123/user_permissions/abc",
            "emailAddress": "user@example.com",
            "accountAccess": {"permission": "user"},
            "containerAccess": [{"containerId": "456", "permission": "edit"}],
        }
        row = perm_mod.format_permission_row(perm)
        assert row[0] == "abc"
        assert row[1] == "user@example.com"
        assert row[2] == "user"
        assert "1 containers" in row[3]

    def test_list_permissions_validates_account(self):
        svc = make_service()
        with pytest.raises(ValueError, match="account_id"):
            perm_mod.list_permissions(svc, "")


# ── Folder Tests ──────────────────────────────────────────────────────

class TestFolders:
    def test_list_folders_success(self):
        svc = make_service()
        svc.accounts().containers().workspaces().folders().list().execute.return_value = {
            "folder": [{"folderId": "20", "name": "Analytics"}]
        }
        result = folder_mod.list_folders(svc, "123", "456", "3")
        assert len(result) == 1
        assert result[0]["folderId"] == "20"

    def test_create_folder_validates_name(self):
        svc = make_service()
        with pytest.raises(ValueError, match="name"):
            folder_mod.create_folder(svc, "123", "456", "3", "")

    def test_delete_folder_returns_dict(self):
        svc = make_service()
        svc.accounts().containers().workspaces().folders().delete().execute.return_value = None
        result = folder_mod.delete_folder(svc, "123", "456", "3", "20")
        assert result["deleted"] is True

    def test_move_to_folder_requires_entities(self):
        svc = make_service()
        with pytest.raises(ValueError, match="At least one"):
            folder_mod.move_to_folder(svc, "123", "456", "3", "20")

    def test_folder_format_row(self):
        f = {"folderId": "20", "name": "Analytics Tags", "fingerprint": "abc123def456789"}
        row = folder_mod.format_folder_row(f)
        assert row[0] == "20"
        assert row[1] == "Analytics Tags"
        assert len(row[2]) <= 12


# ── Environment Tests ─────────────────────────────────────────────────

class TestEnvironments:
    def test_create_environment_validates_name(self):
        svc = make_service()
        with pytest.raises(ValueError, match="name"):
            env_mod.create_environment(svc, "123", "456", "")

    def test_create_environment_validates_type(self):
        svc = make_service()
        with pytest.raises(ValueError, match="env_type"):
            env_mod.create_environment(svc, "123", "456", "Staging", env_type="production")

    def test_delete_environment_returns_dict(self):
        svc = make_service()
        svc.accounts().containers().environments().delete().execute.return_value = None
        result = env_mod.delete_environment(svc, "123", "456", "99")
        assert result["deleted"] is True

    def test_environment_format_row(self):
        e = {
            "environmentId": "1",
            "name": "Live",
            "type": "live",
            "url": "https://example.com/long-path",
            "authorizationCode": "abc123",
        }
        row = env_mod.format_environment_row(e)
        assert row[0] == "1"
        assert row[2] == "live"


# ── Version Tests ─────────────────────────────────────────────────────

class TestVersions:
    def test_list_version_headers_success(self):
        svc = make_service()
        svc.accounts().containers().version_headers().list().execute.return_value = {
            "containerVersionHeader": [
                {"containerVersionId": "1", "name": "Initial"}
            ]
        }
        result = ver_mod.list_version_headers(svc, "123", "456")
        assert len(result) == 1
        assert result[0]["containerVersionId"] == "1"

    def test_latest_version_header_success(self):
        svc = make_service()
        svc.accounts().containers().version_headers().latest().execute.return_value = {
            "containerVersionId": "5", "name": "Latest"
        }
        result = ver_mod.latest_version_header(svc, "123", "456")
        assert result["containerVersionId"] == "5"

    def test_version_format_row(self):
        vh = {
            "containerVersionId": "3",
            "name": "v3.0",
            "deleted": False,
            "numMacros": "5",
            "fingerprint": "abc123xyz",
        }
        row = ver_mod.format_version_row(vh)
        assert row[0] == "3"
        assert row[1] == "v3.0"


# ── Validation edge cases ─────────────────────────────────────────────

class TestValidationEdgeCases:
    """Test that validation catches edge cases consistently."""

    def test_containers_requires_account_and_container(self):
        svc = make_service()
        with pytest.raises(ValueError):
            cont_mod.list_containers(svc, "")

    def test_workspaces_requires_all_ids(self):
        svc = make_service()
        with pytest.raises(ValueError):
            ws_mod.list_workspaces(svc, "123", "")

    def test_tags_requires_all_ids(self):
        svc = make_service()
        with pytest.raises(ValueError):
            tags_mod.list_tags(svc, "123", "456", "")

    def test_triggers_requires_all_ids(self):
        svc = make_service()
        with pytest.raises(ValueError):
            trig_mod.list_triggers(svc, "123", "456", "")

    def test_variables_requires_all_ids(self):
        svc = make_service()
        with pytest.raises(ValueError):
            var_mod.list_variables(svc, "123", "", "3")
