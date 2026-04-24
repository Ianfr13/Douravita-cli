"""Unit tests for cli-anything-infisical core modules.

All HTTP calls are mocked via unittest.mock so no real network requests are made.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch, PropertyMock

import pytest
from click.testing import CliRunner

from cli_anything.infisical.utils.infisical_backend import (
    InfisicalBackend,
    InfisicalAPIError,
)
from cli_anything.infisical.core.secrets import SecretsClient
from cli_anything.infisical.core.projects import ProjectsClient
from cli_anything.infisical.infisical_cli import main


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

WORKSPACE_ID = "ws-test-123"
ENV = "dev"
TOKEN = "test-token-xyz"
BASE_URL = "https://sec.example.com"


def _mock_response(json_data: dict | list, status_code: int = 200) -> MagicMock:
    """Build a mock requests.Response."""
    resp = MagicMock()
    resp.ok = status_code < 400
    resp.status_code = status_code
    resp.json.return_value = json_data
    resp.text = json.dumps(json_data)
    return resp


# ---------------------------------------------------------------------------
# InfisicalBackend tests
# ---------------------------------------------------------------------------


class TestInfisicalBackend:
    def _backend(self) -> InfisicalBackend:
        return InfisicalBackend(base_url=BASE_URL, token=TOKEN)

    def test_auth_header_set(self):
        backend = self._backend()
        assert backend._session.headers["Authorization"] == f"Bearer {TOKEN}"

    def test_get_success(self):
        backend = self._backend()
        payload = {"secrets": [{"secretKey": "FOO", "secretValue": "bar"}]}
        backend._session.get = MagicMock(return_value=_mock_response(payload))

        result = backend.get("/v3/secrets/raw", params={"workspaceId": WORKSPACE_ID})

        backend._session.get.assert_called_once()
        assert result == payload

    def test_post_success(self):
        backend = self._backend()
        payload = {"secret": {"secretKey": "NEW_KEY", "secretValue": "new_val"}}
        backend._session.post = MagicMock(return_value=_mock_response(payload))

        result = backend.post("/v3/secrets/raw/NEW_KEY", json={"secretValue": "new_val"})

        backend._session.post.assert_called_once()
        assert result == payload

    def test_patch_success(self):
        backend = self._backend()
        payload = {"secret": {"secretKey": "FOO", "secretValue": "updated"}}
        backend._session.patch = MagicMock(return_value=_mock_response(payload))

        result = backend.patch("/v3/secrets/raw/FOO", json={"secretValue": "updated"})

        backend._session.patch.assert_called_once()
        assert result == payload

    def test_get_raises_on_error(self):
        backend = self._backend()
        error_payload = {"message": "Unauthorized", "error": "Forbidden"}
        backend._session.get = MagicMock(
            return_value=_mock_response(error_payload, status_code=401)
        )

        with pytest.raises(InfisicalAPIError) as exc_info:
            backend.get("/v3/secrets/raw")

        assert exc_info.value.status_code == 401
        assert exc_info.value.body == error_payload

    def test_post_raises_on_error(self):
        backend = self._backend()
        error_payload = {"message": "Not found"}
        backend._session.post = MagicMock(
            return_value=_mock_response(error_payload, status_code=404)
        )

        with pytest.raises(InfisicalAPIError) as exc_info:
            backend.post("/v3/secrets/raw/MISSING")

        assert exc_info.value.status_code == 404

    def test_url_construction(self):
        backend = InfisicalBackend(base_url="https://sec.example.com/", token=TOKEN)
        assert backend._url("/v3/secrets/raw") == "https://sec.example.com/api/v3/secrets/raw"

    def test_list_secrets(self):
        backend = self._backend()
        secrets_data = [
            {"secretKey": "DB_HOST", "secretValue": "localhost"},
            {"secretKey": "DB_PORT", "secretValue": "5432"},
        ]
        payload = {"secrets": secrets_data}
        backend._session.get = MagicMock(return_value=_mock_response(payload))

        result = backend.list_secrets(WORKSPACE_ID, ENV)

        assert result == secrets_data

    def test_get_secret(self):
        backend = self._backend()
        secret_data = {"secretKey": "MY_KEY", "secretValue": "my_val"}
        payload = {"secret": secret_data}
        backend._session.get = MagicMock(return_value=_mock_response(payload))

        result = backend.get_secret("MY_KEY", WORKSPACE_ID, ENV)

        assert result == secret_data

    def test_create_secret(self):
        backend = self._backend()
        secret_data = {"secretKey": "NEW", "secretValue": "value123"}
        payload = {"secret": secret_data}
        backend._session.post = MagicMock(return_value=_mock_response(payload))

        result = backend.create_secret("NEW", "value123", WORKSPACE_ID, ENV)

        assert result == secret_data
        call_kwargs = backend._session.post.call_args
        sent_json = call_kwargs[1]["json"]
        assert sent_json["workspaceId"] == WORKSPACE_ID
        assert sent_json["environment"] == ENV
        assert sent_json["secretValue"] == "value123"
        assert sent_json["type"] == "shared"

    def test_update_secret(self):
        backend = self._backend()
        secret_data = {"secretKey": "FOO", "secretValue": "new_val"}
        payload = {"secret": secret_data}
        backend._session.patch = MagicMock(return_value=_mock_response(payload))

        result = backend.update_secret("FOO", "new_val", WORKSPACE_ID, ENV)

        assert result == secret_data

    def test_list_workspaces(self):
        backend = self._backend()
        workspaces = [{"id": "ws1", "name": "My Project"}]
        payload = {"workspaces": workspaces}
        backend._session.get = MagicMock(return_value=_mock_response(payload))

        result = backend.list_workspaces()

        assert result == workspaces

    def test_create_workspace(self):
        backend = self._backend()
        ws_data = {"id": "ws-new", "name": "New Project"}
        payload = {"workspace": ws_data}
        backend._session.post = MagicMock(return_value=_mock_response(payload))

        result = backend.create_workspace("New Project", "org-123")

        assert result == ws_data
        call_kwargs = backend._session.post.call_args
        sent_json = call_kwargs[1]["json"]
        assert sent_json["workspaceName"] == "New Project"
        assert sent_json["organizationId"] == "org-123"


# ---------------------------------------------------------------------------
# SecretsClient tests
# ---------------------------------------------------------------------------


class TestSecretsClient:
    def _client_with_mock_backend(self, mock_methods: dict):
        """Create a SecretsClient with a mocked InfisicalBackend."""
        backend = MagicMock(spec=InfisicalBackend)
        for method, return_value in mock_methods.items():
            getattr(backend, method).return_value = return_value
        return SecretsClient(backend, WORKSPACE_ID, ENV)

    def test_list(self):
        secrets_data = [
            {"secretKey": "A", "secretValue": "1"},
            {"secretKey": "B", "secretValue": "2"},
        ]
        client = self._client_with_mock_backend({"list_secrets": secrets_data})

        result = client.list()

        assert result == secrets_data
        client.backend.list_secrets.assert_called_once_with(
            workspace_id=WORKSPACE_ID,
            environment=ENV,
            secret_path="/",
        )

    def test_get(self):
        secret = {"secretKey": "MY_KEY", "secretValue": "my_val"}
        client = self._client_with_mock_backend({"get_secret": secret})

        result = client.get("MY_KEY")

        assert result == secret
        client.backend.get_secret.assert_called_once_with(
            secret_name="MY_KEY",
            workspace_id=WORKSPACE_ID,
            environment=ENV,
            secret_path="/",
        )

    def test_create(self):
        created = {"secretKey": "NEW", "secretValue": "val"}
        client = self._client_with_mock_backend({"create_secret": created})

        result = client.create("NEW", "val")

        assert result == created
        client.backend.create_secret.assert_called_once_with(
            secret_name="NEW",
            secret_value="val",
            workspace_id=WORKSPACE_ID,
            environment=ENV,
            secret_path="/",
        )

    def test_update(self):
        updated = {"secretKey": "FOO", "secretValue": "new_val"}
        client = self._client_with_mock_backend({"update_secret": updated})

        result = client.update("FOO", "new_val")

        assert result == updated
        client.backend.update_secret.assert_called_once_with(
            secret_name="FOO",
            secret_value="new_val",
            workspace_id=WORKSPACE_ID,
            environment=ENV,
            secret_path="/",
        )

    def test_export_dotenv(self):
        secrets_data = [
            {"secretKey": "DB_HOST", "secretValue": "localhost"},
            {"secretKey": "DB_PORT", "secretValue": "5432"},
        ]
        client = self._client_with_mock_backend({"list_secrets": secrets_data})

        result = client.export_dotenv()

        assert "DB_HOST=localhost" in result
        assert "DB_PORT=5432" in result

    def test_export_dotenv_empty(self):
        client = self._client_with_mock_backend({"list_secrets": []})

        result = client.export_dotenv()

        assert result == ""


# ---------------------------------------------------------------------------
# ProjectsClient tests
# ---------------------------------------------------------------------------


class TestProjectsClient:
    def _client_with_mock_backend(self, mock_methods: dict):
        backend = MagicMock(spec=InfisicalBackend)
        for method, return_value in mock_methods.items():
            getattr(backend, method).return_value = return_value
        return ProjectsClient(backend)

    def test_list(self):
        workspaces = [{"id": "ws1", "name": "Proj A"}, {"id": "ws2", "name": "Proj B"}]
        client = self._client_with_mock_backend({"list_workspaces": workspaces})

        result = client.list()

        assert result == workspaces
        client.backend.list_workspaces.assert_called_once()

    def test_create(self):
        ws = {"id": "ws-new", "name": "New Proj"}
        client = self._client_with_mock_backend({"create_workspace": ws})

        result = client.create("New Proj", "org-abc")

        assert result == ws
        client.backend.create_workspace.assert_called_once_with(
            workspace_name="New Proj",
            organization_id="org-abc",
        )


# ---------------------------------------------------------------------------
# CLI command tests via CliRunner
# ---------------------------------------------------------------------------


class TestCLICommands:
    """Test Click CLI commands using CliRunner with mocked backend."""

    def _common_args(self) -> list[str]:
        return [
            "--token", TOKEN,
            "--workspace", WORKSPACE_ID,
            "--env", ENV,
            "--url", BASE_URL,
        ]

    # ------------------------------------------------------------------ secrets list

    def test_secrets_list_text(self):
        runner = CliRunner()
        secrets_data = [
            {"secretKey": "FOO", "secretValue": "bar"},
            {"secretKey": "BAZ", "secretValue": "qux"},
        ]

        with patch(
            "cli_anything.infisical.infisical_cli.InfisicalBackend"
        ) as MockBackend:
            instance = MockBackend.return_value
            instance.list_secrets.return_value = secrets_data

            result = runner.invoke(
                main,
                self._common_args() + ["secrets", "list"],
            )

        assert result.exit_code == 0
        assert "FOO" in result.output
        assert "bar" in result.output

    def test_secrets_list_json(self):
        runner = CliRunner()
        secrets_data = [{"secretKey": "FOO", "secretValue": "bar"}]

        with patch(
            "cli_anything.infisical.infisical_cli.InfisicalBackend"
        ) as MockBackend:
            instance = MockBackend.return_value
            instance.list_secrets.return_value = secrets_data

            result = runner.invoke(
                main,
                self._common_args() + ["secrets", "list", "--json"],
            )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert data[0]["secretKey"] == "FOO"

    def test_secrets_list_missing_token(self):
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["--workspace", WORKSPACE_ID, "--env", ENV, "--url", BASE_URL,
             "secrets", "list"],
        )
        assert result.exit_code != 0 or "token" in result.output.lower() or "token" in (result.output + "".join(str(o) for o in [result.exception or ""])).lower()

    def test_secrets_list_missing_workspace(self):
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["--token", TOKEN, "--env", ENV, "--url", BASE_URL,
             "secrets", "list"],
        )
        assert result.exit_code != 0 or "workspace" in result.output.lower()

    # ------------------------------------------------------------------ secrets get

    def test_secrets_get_text(self):
        runner = CliRunner()
        secret = {"secretKey": "MY_KEY", "secretValue": "my_val"}

        with patch(
            "cli_anything.infisical.infisical_cli.InfisicalBackend"
        ) as MockBackend:
            instance = MockBackend.return_value
            instance.get_secret.return_value = secret

            result = runner.invoke(
                main,
                self._common_args() + ["secrets", "get", "MY_KEY"],
            )

        assert result.exit_code == 0
        assert "MY_KEY" in result.output
        assert "my_val" in result.output

    def test_secrets_get_json(self):
        runner = CliRunner()
        secret = {"secretKey": "MY_KEY", "secretValue": "my_val"}

        with patch(
            "cli_anything.infisical.infisical_cli.InfisicalBackend"
        ) as MockBackend:
            instance = MockBackend.return_value
            instance.get_secret.return_value = secret

            result = runner.invoke(
                main,
                self._common_args() + ["secrets", "get", "MY_KEY", "--json"],
            )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["secretValue"] == "my_val"

    # ------------------------------------------------------------------ secrets export

    def test_secrets_export_dotenv(self):
        runner = CliRunner()
        secrets_data = [
            {"secretKey": "HOST", "secretValue": "localhost"},
            {"secretKey": "PORT", "secretValue": "3000"},
        ]

        with patch(
            "cli_anything.infisical.infisical_cli.InfisicalBackend"
        ) as MockBackend:
            instance = MockBackend.return_value
            instance.list_secrets.return_value = secrets_data

            result = runner.invoke(
                main,
                self._common_args() + ["secrets", "export"],
            )

        assert result.exit_code == 0
        assert "HOST=localhost" in result.output
        assert "PORT=3000" in result.output

    def test_secrets_export_json(self):
        runner = CliRunner()
        secrets_data = [
            {"secretKey": "HOST", "secretValue": "localhost"},
        ]

        with patch(
            "cli_anything.infisical.infisical_cli.InfisicalBackend"
        ) as MockBackend:
            instance = MockBackend.return_value
            instance.list_secrets.return_value = secrets_data

            result = runner.invoke(
                main,
                self._common_args() + ["secrets", "export", "--json"],
            )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["HOST"] == "localhost"

    # ------------------------------------------------------------------ secrets create

    def test_secrets_create(self):
        runner = CliRunner()
        created = {"secretKey": "NEW_VAR", "secretValue": "new_value"}

        with patch(
            "cli_anything.infisical.infisical_cli.InfisicalBackend"
        ) as MockBackend:
            instance = MockBackend.return_value
            instance.create_secret.return_value = created

            result = runner.invoke(
                main,
                self._common_args() + ["secrets", "create", "NEW_VAR", "new_value"],
            )

        assert result.exit_code == 0
        assert "NEW_VAR" in result.output or "created" in result.output.lower()

    def test_secrets_create_json(self):
        runner = CliRunner()
        created = {"secretKey": "NEW_VAR", "secretValue": "new_value"}

        with patch(
            "cli_anything.infisical.infisical_cli.InfisicalBackend"
        ) as MockBackend:
            instance = MockBackend.return_value
            instance.create_secret.return_value = created

            result = runner.invoke(
                main,
                self._common_args() + ["secrets", "create", "NEW_VAR", "new_value", "--json"],
            )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["secretKey"] == "NEW_VAR"

    # ------------------------------------------------------------------ secrets edit

    def test_secrets_edit(self):
        runner = CliRunner()
        updated = {"secretKey": "FOO", "secretValue": "new_bar"}

        with patch(
            "cli_anything.infisical.infisical_cli.InfisicalBackend"
        ) as MockBackend:
            instance = MockBackend.return_value
            instance.update_secret.return_value = updated

            result = runner.invoke(
                main,
                self._common_args() + ["secrets", "edit", "FOO", "new_bar"],
            )

        assert result.exit_code == 0
        assert "FOO" in result.output or "updated" in result.output.lower()

    # ------------------------------------------------------------------ projects list

    def test_projects_list_text(self):
        runner = CliRunner()
        workspaces = [
            {"id": "ws1", "name": "Alpha", "organization": "org-1"},
            {"id": "ws2", "name": "Beta", "organization": "org-1"},
        ]

        with patch(
            "cli_anything.infisical.infisical_cli.InfisicalBackend"
        ) as MockBackend:
            instance = MockBackend.return_value
            instance.list_workspaces.return_value = workspaces

            result = runner.invoke(
                main,
                ["--token", TOKEN, "--url", BASE_URL, "projects", "list"],
            )

        assert result.exit_code == 0
        assert "Alpha" in result.output
        assert "Beta" in result.output

    def test_projects_list_json(self):
        runner = CliRunner()
        workspaces = [{"id": "ws1", "name": "Alpha"}]

        with patch(
            "cli_anything.infisical.infisical_cli.InfisicalBackend"
        ) as MockBackend:
            instance = MockBackend.return_value
            instance.list_workspaces.return_value = workspaces

            result = runner.invoke(
                main,
                ["--token", TOKEN, "--url", BASE_URL, "projects", "list", "--json"],
            )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data[0]["name"] == "Alpha"

    # ------------------------------------------------------------------ projects create

    def test_projects_create(self):
        runner = CliRunner()
        ws = {"id": "ws-new", "name": "My New Project"}

        with patch(
            "cli_anything.infisical.infisical_cli.InfisicalBackend"
        ) as MockBackend:
            instance = MockBackend.return_value
            instance.create_workspace.return_value = ws

            result = runner.invoke(
                main,
                ["--token", TOKEN, "--url", BASE_URL,
                 "projects", "create", "My New Project", "--org-id", "org-xyz"],
            )

        assert result.exit_code == 0
        assert "My New Project" in result.output or "created" in result.output.lower()

    def test_projects_create_missing_org(self):
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["--token", TOKEN, "--url", BASE_URL,
             "projects", "create", "Test Project"],
        )
        assert result.exit_code != 0 or "org" in result.output.lower()

    # ------------------------------------------------------------------ API error handling

    def test_api_error_displayed(self):
        runner = CliRunner()
        error_body = {"message": "Secret not found", "error": "NotFoundError"}

        with patch(
            "cli_anything.infisical.infisical_cli.InfisicalBackend"
        ) as MockBackend:
            instance = MockBackend.return_value
            instance.get_secret.side_effect = InfisicalAPIError(404, error_body)

            result = runner.invoke(
                main,
                self._common_args() + ["secrets", "get", "NONEXISTENT"],
            )

        assert result.exit_code != 0
        assert "404" in result.output + (result.output or "")


# ---------------------------------------------------------------------------
# Extended CLI groups — smoke tests (one or two per group)
# ---------------------------------------------------------------------------

def _common():
    return [
        "--token", TOKEN,
        "--workspace", WORKSPACE_ID,
        "--env", ENV,
        "--url", BASE_URL,
    ]


def _patch_backend():
    """Patch InfisicalBackend in the main CLI module (where ctx.backend() instantiates it)."""
    return patch("cli_anything.infisical.infisical_cli.InfisicalBackend")


class TestSecretsExt:
    def test_delete(self):
        with _patch_backend() as MB:
            MB.return_value.delete_secret.return_value = {"secretKey": "FOO"}
            result = CliRunner().invoke(main, _common() + ["secrets-x", "delete", "FOO"])
        assert result.exit_code == 0
        MB.return_value.delete_secret.assert_called_once()

    def test_rename(self):
        with _patch_backend() as MB:
            MB.return_value.update_secret.return_value = {"secretKey": "BAR"}
            result = CliRunner().invoke(main, _common() + ["secrets-x", "rename", "FOO", "BAR"])
        assert result.exit_code == 0
        call = MB.return_value.update_secret.call_args
        assert call.kwargs.get("new_secret_name") == "BAR"

    def test_bulk_delete(self):
        with _patch_backend() as MB:
            MB.return_value.bulk_delete_secrets.return_value = {"secrets": []}
            result = CliRunner().invoke(main, _common() + ["secrets-x", "bulk-delete", "A", "B", "C"])
        assert result.exit_code == 0
        MB.return_value.bulk_delete_secrets.assert_called_once()


class TestFolders:
    def test_list(self):
        with _patch_backend() as MB:
            MB.return_value.list_folders.return_value = [
                {"id": "f1", "name": "prod", "envId": "e1"}
            ]
            result = CliRunner().invoke(main, _common() + ["folders", "list"])
        assert result.exit_code == 0
        assert "prod" in result.output

    def test_create_json(self):
        with _patch_backend() as MB:
            MB.return_value.create_folder.return_value = {"id": "f-new", "name": "secrets"}
            result = CliRunner().invoke(
                main, _common() + ["folders", "create", "secrets", "--json"]
            )
        assert result.exit_code == 0
        assert json.loads(result.output)["id"] == "f-new"


class TestEnvironments:
    def test_list(self):
        with _patch_backend() as MB:
            MB.return_value.list_environments.return_value = [
                {"id": "e1", "name": "Development", "slug": "dev", "position": 1}
            ]
            result = CliRunner().invoke(main, _common() + ["environments", "list"])
        assert result.exit_code == 0
        assert "dev" in result.output

    def test_create(self):
        with _patch_backend() as MB:
            MB.return_value.create_environment.return_value = {"id": "e2", "slug": "staging"}
            result = CliRunner().invoke(
                main, _common() + ["environments", "create", "Staging", "staging"]
            )
        assert result.exit_code == 0


class TestProjectsExt:
    def test_info(self):
        with _patch_backend() as MB:
            MB.return_value.get_workspace.return_value = {"id": WORKSPACE_ID, "name": "App"}
            result = CliRunner().invoke(main, _common() + ["projects-x", "info"])
        assert result.exit_code == 0

    def test_members_list(self):
        with _patch_backend() as MB:
            MB.return_value.list_workspace_memberships.return_value = [
                {"id": "m1", "user": {"email": "a@b.com"}, "roles": [{"role": "admin"}]}
            ]
            result = CliRunner().invoke(main, _common() + ["projects-x", "members", "list"])
        assert result.exit_code == 0


class TestSnapshots:
    def test_list(self):
        with _patch_backend() as MB:
            MB.return_value.list_snapshots.return_value = [
                {"id": "s1", "environment": "dev", "createdAt": "2024-01-01"}
            ]
            result = CliRunner().invoke(main, _common() + ["snapshots", "list"])
        assert result.exit_code == 0
        assert "s1" in result.output

    def test_rollback_requires_yes(self):
        with _patch_backend() as MB:
            result = CliRunner().invoke(main, _common() + ["snapshots", "rollback", "s1"])
        assert result.exit_code != 0 or "--yes" in result.output.lower() or "confirm" in result.output.lower()


class TestTags:
    def test_list(self):
        with _patch_backend() as MB:
            MB.return_value.list_tags.return_value = [{"id": "t1", "slug": "prod", "color": "#000"}]
            result = CliRunner().invoke(main, _common() + ["tags", "list"])
        assert result.exit_code == 0
        assert "prod" in result.output

    def test_create(self):
        with _patch_backend() as MB:
            MB.return_value.create_tag.return_value = {"id": "t2", "slug": "prod"}
            result = CliRunner().invoke(main, _common() + ["tags", "create", "prod", "--color", "#FF0000"])
        assert result.exit_code == 0


class TestSecretImports:
    def test_list(self):
        with _patch_backend() as MB:
            MB.return_value.list_secret_imports.return_value = [
                {"id": "i1", "importEnv": {"slug": "prod"}, "importPath": "/"}
            ]
            result = CliRunner().invoke(main, _common() + ["imports", "list"])
        assert result.exit_code == 0

    def test_create(self):
        with _patch_backend() as MB:
            MB.return_value.create_secret_import.return_value = {"id": "i2"}
            result = CliRunner().invoke(
                main, _common() + ["imports", "create", "--from-env", "prod", "--from-path", "/"]
            )
        assert result.exit_code == 0


class TestIdentities:
    def test_list(self):
        with _patch_backend() as MB:
            MB.return_value.list_identities.return_value = [{"id": "id1", "name": "ci-bot"}]
            result = CliRunner().invoke(
                main, _common() + ["identities", "list", "--org-id", "org-1"]
            )
        assert result.exit_code == 0
        assert "ci-bot" in result.output

    def test_create(self):
        with _patch_backend() as MB:
            MB.return_value.create_identity.return_value = {"id": "id2", "name": "bot"}
            result = CliRunner().invoke(
                main, _common() + ["identities", "create", "bot", "--org-id", "org-1", "--role", "admin"]
            )
        assert result.exit_code == 0


class TestAuth:
    def test_login(self):
        with _patch_backend() as MB:
            MB.return_value.universal_auth_login.return_value = {"accessToken": "jwt-123"}
            result = CliRunner().invoke(
                main, _common() + ["auth", "login", "--client-id", "c1", "--client-secret", "s1"]
            )
        assert result.exit_code == 0
        assert "jwt-123" in result.output

    def test_attach_ua(self):
        with _patch_backend() as MB:
            MB.return_value.attach_universal_auth.return_value = {"id": "ua1"}
            result = CliRunner().invoke(main, _common() + ["auth", "attach-ua", "id1"])
        assert result.exit_code == 0


class TestAudit:
    def test_export(self):
        with _patch_backend() as MB:
            MB.return_value.export_audit_logs.return_value = [
                {"createdAt": "2024-01-01", "actor": "u", "eventType": "secret-created", "ipAddress": "1.2.3.4"}
            ]
            result = CliRunner().invoke(
                main, _common() + ["audit", "export", "--org-id", "org-1"]
            )
        assert result.exit_code == 0


class TestDynamicSecrets:
    def test_list(self):
        with _patch_backend() as MB:
            MB.return_value.list_dynamic_secrets.return_value = [
                {"id": "d1", "name": "pg", "status": "active", "defaultTTL": "1h", "maxTTL": "24h"}
            ]
            result = CliRunner().invoke(main, _common() + ["dynamic-secrets", "list"])
        assert result.exit_code == 0
        assert "pg" in result.output

    def test_leases_create(self):
        with _patch_backend() as MB:
            MB.return_value.create_dynamic_secret_lease.return_value = {
                "lease": {"id": "l1"},
                "data": {"username": "u", "password": "p"},
            }
            result = CliRunner().invoke(
                main, _common() + ["dynamic-secrets", "leases", "create", "pg"]
            )
        assert result.exit_code == 0


class TestGroups:
    def test_list(self):
        with _patch_backend() as MB:
            MB.return_value.list_groups.return_value = [
                {"id": "g1", "name": "devs", "slug": "devs", "role": "member"}
            ]
            result = CliRunner().invoke(
                main, _common() + ["groups", "list", "--org-id", "org-1"]
            )
        assert result.exit_code == 0
        assert "devs" in result.output

    def test_users_list(self):
        with _patch_backend() as MB:
            MB.return_value.list_group_users.return_value = [
                {"username": "alice", "email": "a@b.com", "role": "member", "isPartOfGroup": True}
            ]
            result = CliRunner().invoke(main, _common() + ["groups", "users", "list", "g1"])
        assert result.exit_code == 0


class TestAppConnections:
    def test_list(self):
        with _patch_backend() as MB:
            MB.return_value.list_app_connections.return_value = [
                {"id": "ac1", "name": "aws-prod", "app": "aws", "method": "oauth2", "createdAt": "x"}
            ]
            result = CliRunner().invoke(main, _common() + ["app-connections", "list"])
        assert result.exit_code == 0
        assert "aws-prod" in result.output

    def test_options(self):
        with _patch_backend() as MB:
            MB.return_value.list_app_connection_options.return_value = [
                {"app": "aws"}, {"app": "github"}
            ]
            result = CliRunner().invoke(main, _common() + ["app-connections", "options"])
        assert result.exit_code == 0


# ---------------------------------------------------------------------------
# Backend extension tests (direct backend calls, mocked HTTP)
# ---------------------------------------------------------------------------

class TestBackendExtensions:
    def _backend(self):
        return InfisicalBackend(base_url=BASE_URL, token=TOKEN)

    def test_delete_secret_sends_delete_with_body(self):
        b = self._backend()
        b._session.delete = MagicMock(return_value=_mock_response({"secret": {"secretKey": "X"}}))
        b.delete_secret("X", WORKSPACE_ID, ENV)
        b._session.delete.assert_called_once()
        call = b._session.delete.call_args
        assert "workspaceId" in call.kwargs["json"]

    def test_create_folder_posts_correct_path(self):
        b = self._backend()
        b._session.post = MagicMock(return_value=_mock_response({"folder": {"id": "f1"}}))
        b.create_folder(WORKSPACE_ID, ENV, "subdir")
        url = b._session.post.call_args.args[0]
        assert url.endswith("/api/v1/folders")

    def test_list_environments_returns_envs_from_workspace(self):
        b = self._backend()
        b._session.get = MagicMock(
            return_value=_mock_response({"workspace": {"environments": [{"id": "e1", "slug": "dev"}]}})
        )
        envs = b.list_environments(WORKSPACE_ID)
        assert envs[0]["slug"] == "dev"

    def test_list_snapshots_forwards_params(self):
        b = self._backend()
        b._session.get = MagicMock(return_value=_mock_response({"secretSnapshots": []}))
        b.list_snapshots(WORKSPACE_ID, environment="dev", limit=5, offset=10)
        params = b._session.get.call_args.kwargs["params"]
        assert params["environment"] == "dev"
        assert params["limit"] == 5

    def test_universal_auth_login_does_not_use_session_auth(self):
        """Login swaps creds for a token — should not send the Bearer header."""
        b = self._backend()
        with patch("cli_anything.infisical.utils.infisical_backend.requests.post") as mock_post:
            mock_post.return_value = _mock_response({"accessToken": "new-jwt"})
            result = b.universal_auth_login("cid", "csec")
        assert result["accessToken"] == "new-jwt"

    def test_create_dynamic_secret_lease_posts(self):
        b = self._backend()
        b._session.post = MagicMock(return_value=_mock_response({"lease": {"id": "l1"}}))
        b.create_dynamic_secret_lease("pg", "proj", "dev")
        assert b._session.post.call_args.args[0].endswith("/api/v1/dynamic-secrets/leases")

    def test_list_tags_returns_workspace_tags(self):
        b = self._backend()
        b._session.get = MagicMock(return_value=_mock_response({"workspaceTags": [{"id": "t1"}]}))
        tags = b.list_tags(WORKSPACE_ID)
        assert tags[0]["id"] == "t1"

    def test_export_audit_logs_builds_path(self):
        b = self._backend()
        b._session.get = MagicMock(return_value=_mock_response({"auditLogs": []}))
        b.export_audit_logs("org-1", limit=50)
        url = b._session.get.call_args.args[0]
        # Org is token-scoped on Infisical's side; path has no {id} segment.
        assert url.endswith("/organization/audit-logs")
