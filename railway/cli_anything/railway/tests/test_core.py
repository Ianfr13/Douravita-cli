"""Unit tests for cli-anything-railway core commands.

All tests mock RailwayBackend so no network calls are made.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from cli_anything.railway.railway_cli import main
from cli_anything.railway.utils.railway_backend import RailwayAPIError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_backend(**overrides):
    """Return a MagicMock backend pre-configured with sensible defaults."""
    backend = MagicMock()

    # --- Projects ---
    backend.projects_list.return_value = [
        {"id": "proj-1", "name": "MyApp", "description": "Test", "createdAt": "2024-01-01T00:00:00", "updatedAt": "2024-01-02T00:00:00"}
    ]
    backend.project_info.return_value = {
        "id": "proj-1",
        "name": "MyApp",
        "description": "Test",
        "createdAt": "2024-01-01T00:00:00",
        "updatedAt": "2024-01-02T00:00:00",
        "environments": {"edges": [{"node": {"id": "env-1", "name": "production"}}]},
        "services": {"edges": [{"node": {"id": "svc-1", "name": "web", "createdAt": "2024-01-01T00:00:00"}}]},
    }
    backend.project_create.return_value = {"id": "proj-new", "name": "NewProject"}

    # --- Services ---
    backend.services_list.return_value = [
        {"id": "svc-1", "name": "web", "createdAt": "2024-01-01T00:00:00"}
    ]
    backend.service_info.return_value = {
        "id": "svc-1", "name": "web",
        "createdAt": "2024-01-01T00:00:00", "updatedAt": "2024-01-02T00:00:00"
    }
    backend.service_create_cron.return_value = {"id": "svc-cron-1", "name": "my-cron"}

    # --- Deployments ---
    backend.deployments_list.return_value = [
        {"id": "dep-1", "status": "SUCCESS", "createdAt": "2024-01-01T00:00:00", "staticUrl": "https://example.up.railway.app"}
    ]
    backend.deployment_trigger.return_value = True
    backend.deployment_status.return_value = {
        "id": "dep-1", "status": "SUCCESS",
        "createdAt": "2024-01-01T00:00:00", "staticUrl": "https://example.up.railway.app"
    }
    backend.deployment_rollback.return_value = True

    # --- Variables ---
    backend.variables_list.return_value = {"MY_VAR": "hello", "PORT": "3000"}
    backend.variable_upsert.return_value = True
    backend.variable_delete.return_value = True

    # --- Environments ---
    backend.environments_list.return_value = [
        {"id": "env-1", "name": "production"}
    ]
    backend.environment_create.return_value = {"id": "env-2", "name": "staging"}

    # --- Logs ---
    backend.deployment_logs.return_value = [
        {"message": "Server started", "severity": "INFO", "timestamp": "2024-01-01T00:00:01"}
    ]
    backend.build_logs.return_value = [
        {"message": "Build complete", "severity": "INFO", "timestamp": "2024-01-01T00:00:00"}
    ]

    # --- Domains ---
    backend.domains_list.return_value = [
        {"id": "dom-1", "domain": "example.com", "type": "custom", "createdAt": "2024-01-01T00:00:00"},
        {"id": "dom-2", "domain": "app.up.railway.app", "type": "railway", "createdAt": "2024-01-01T00:00:00"},
    ]
    backend.custom_domain_create.return_value = {"id": "dom-3", "domain": "new.example.com"}
    backend.custom_domain_delete.return_value = True
    backend.service_domain_create.return_value = {"id": "dom-4", "domain": "generated.up.railway.app"}

    # --- Volumes ---
    backend.volumes_list.return_value = [
        {"id": "vol-1", "name": "data", "createdAt": "2024-01-01T00:00:00"}
    ]
    backend.volume_create.return_value = {"id": "vol-2", "name": "uploads"}
    backend.volume_delete.return_value = True

    # --- Metrics ---
    backend.service_metrics.return_value = {
        "cpuPercentage": 12.5,
        "memoryUsageBytes": 134217728,
        "networkRxBytes": 1048576,
        "networkTxBytes": 524288,
    }

    # --- Templates ---
    backend.templates_list.return_value = [
        {"id": "t-1", "code": "django", "name": "Django", "description": "Django web framework"},
        {"id": "t-2", "code": "postgres", "name": "PostgreSQL", "description": "Managed Postgres"},
    ]
    backend.template_deploy.return_value = {"projectId": "proj-1"}

    # --- Service config ---
    backend.service_instance_get.return_value = {
        "startCommand": "node server.js",
        "buildCommand": "npm run build",
        "dockerfilePath": "Dockerfile",
        "healthcheckPath": "/health",
        "restartPolicyType": "ON_FAILURE",
        "rootDirectory": "/app",
    }
    backend.service_instance_update.return_value = True

    # --- TCP proxies ---
    backend.tcp_proxies_list.return_value = [
        {"id": "tcp-1", "applicationPort": 3000, "proxyPort": 12345, "domain": "proxy.railway.app"}
    ]
    backend.tcp_proxy_create.return_value = {"id": "tcp-2", "proxyPort": 22222, "domain": "new-proxy.railway.app"}
    backend.tcp_proxy_delete.return_value = True

    # --- Webhooks ---
    backend.webhooks_list.return_value = [
        {"id": "wh-1", "url": "https://hooks.example.com/railway"}
    ]
    backend.webhook_create.return_value = {"id": "wh-2", "url": "https://hooks.example.com/new"}
    backend.webhook_delete.return_value = True

    # --- Team ---
    backend.team_list.return_value = [
        {"id": "usr-1", "email": "alice@example.com", "role": "ADMIN", "teamId": "team-1", "teamName": "Acme"}
    ]
    backend.team_invite.return_value = True
    backend.team_member_remove.return_value = True

    # --- Networking ---
    backend.networking_list.return_value = [
        {"serviceId": "svc-1", "serviceName": "web", "id": "nd-1", "internalDomain": "web.railway.internal"}
    ]

    # --- Git ---
    backend.git_connect.return_value = True
    backend.git_disconnect.return_value = True

    for k, v in overrides.items():
        setattr(backend, k, v)

    return backend


def _invoke(args: list[str], backend=None):
    """Run the CLI with a mocked backend."""
    runner = CliRunner()
    _backend = backend or _make_backend()

    with patch(
        "cli_anything.railway.railway_cli.RailwayBackend", return_value=_backend
    ):
        result = runner.invoke(
            main,
            ["--token", "fake-token"] + args,
            catch_exceptions=False,
        )
    return result


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------

class TestProjectsList:
    def test_tabular_output(self):
        result = _invoke(["projects", "list"])
        assert result.exit_code == 0
        assert "MyApp" in result.output

    def test_json_output(self):
        result = _invoke(["projects", "list", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data[0]["id"] == "proj-1"

    def test_api_error(self):
        backend = _make_backend()
        backend.projects_list.side_effect = RailwayAPIError("boom")
        result = _invoke(["projects", "list"], backend=backend)
        assert result.exit_code != 0

    def test_empty_list(self):
        backend = _make_backend()
        backend.projects_list.return_value = []
        result = _invoke(["projects", "list"], backend=backend)
        assert result.exit_code == 0
        assert "No projects" in result.output


class TestProjectsCreate:
    def test_creates_project(self):
        result = _invoke(["projects", "create", "NewProject"])
        assert result.exit_code == 0
        assert "NewProject" in result.output

    def test_json_output(self):
        result = _invoke(["projects", "create", "NewProject", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["id"] == "proj-new"

    def test_api_error(self):
        backend = _make_backend()
        backend.project_create.side_effect = RailwayAPIError("cannot create")
        result = _invoke(["projects", "create", "Bad", "--json"], backend=backend)
        assert result.exit_code != 0


class TestProjectsInfo:
    def test_shows_details(self):
        result = _invoke(["projects", "info", "proj-1"])
        assert result.exit_code == 0
        assert "MyApp" in result.output

    def test_json_output(self):
        result = _invoke(["projects", "info", "proj-1", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["id"] == "proj-1"

    def test_not_found(self):
        backend = _make_backend()
        backend.project_info.return_value = {}
        result = _invoke(["projects", "info", "bad-id"], backend=backend)
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# Services
# ---------------------------------------------------------------------------

class TestServicesList:
    def test_tabular_output(self):
        result = _invoke(["services", "list", "--project", "proj-1"])
        assert result.exit_code == 0
        assert "web" in result.output

    def test_json_output(self):
        result = _invoke(["services", "list", "--project", "proj-1", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data[0]["id"] == "svc-1"

    def test_missing_project_flag(self):
        runner = CliRunner()
        with patch("cli_anything.railway.railway_cli.RailwayBackend", return_value=_make_backend()):
            result = runner.invoke(main, ["--token", "x", "services", "list"], catch_exceptions=False)
        assert result.exit_code != 0

    def test_empty_list(self):
        backend = _make_backend()
        backend.services_list.return_value = []
        result = _invoke(["services", "list", "--project", "proj-1"], backend=backend)
        assert result.exit_code == 0


class TestServicesInfo:
    def test_shows_details(self):
        result = _invoke(["services", "info", "svc-1"])
        assert result.exit_code == 0
        assert "web" in result.output

    def test_json_output(self):
        result = _invoke(["services", "info", "svc-1", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["id"] == "svc-1"

    def test_not_found(self):
        backend = _make_backend()
        backend.service_info.return_value = {}
        result = _invoke(["services", "info", "bad-id"], backend=backend)
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# Deployments
# ---------------------------------------------------------------------------

class TestDeploymentsList:
    def test_tabular_output(self):
        result = _invoke(["deployments", "list", "--service", "svc-1"])
        assert result.exit_code == 0
        assert "SUCCESS" in result.output

    def test_json_output(self):
        result = _invoke(["deployments", "list", "--service", "svc-1", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data[0]["id"] == "dep-1"

    def test_empty(self):
        backend = _make_backend()
        backend.deployments_list.return_value = []
        result = _invoke(["deployments", "list", "--service", "svc-1"], backend=backend)
        assert result.exit_code == 0


class TestDeploymentsTrigger:
    def test_success(self):
        result = _invoke(["deployments", "trigger", "svc-1", "--env", "env-1"])
        assert result.exit_code == 0
        assert "triggered" in result.output.lower()

    def test_json_output(self):
        result = _invoke(["deployments", "trigger", "svc-1", "--env", "env-1", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["triggered"] is True

    def test_api_error(self):
        backend = _make_backend()
        backend.deployment_trigger.side_effect = RailwayAPIError("fail")
        result = _invoke(["deployments", "trigger", "svc-1", "--env", "env-1"], backend=backend)
        assert result.exit_code != 0


class TestDeploymentsStatus:
    def test_shows_details(self):
        result = _invoke(["deployments", "status", "dep-1"])
        assert result.exit_code == 0
        assert "SUCCESS" in result.output

    def test_json_output(self):
        result = _invoke(["deployments", "status", "dep-1", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["id"] == "dep-1"

    def test_not_found(self):
        backend = _make_backend()
        backend.deployment_status.return_value = {}
        result = _invoke(["deployments", "status", "bad-id"], backend=backend)
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# Variables
# ---------------------------------------------------------------------------

class TestVariablesList:
    def test_tabular_output(self):
        result = _invoke(["variables", "list", "--project", "proj-1", "--env", "env-1"])
        assert result.exit_code == 0
        assert "MY_VAR" in result.output

    def test_json_output(self):
        result = _invoke(["variables", "list", "--project", "proj-1", "--env", "env-1", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["MY_VAR"] == "hello"

    def test_empty(self):
        backend = _make_backend()
        backend.variables_list.return_value = {}
        result = _invoke(["variables", "list", "--project", "proj-1", "--env", "env-1"], backend=backend)
        assert result.exit_code == 0

    def test_api_error(self):
        backend = _make_backend()
        backend.variables_list.side_effect = RailwayAPIError("boom")
        result = _invoke(["variables", "list", "--project", "proj-1", "--env", "env-1"], backend=backend)
        assert result.exit_code != 0


class TestVariablesSet:
    def test_sets_variable(self):
        result = _invoke(["variables", "set", "MY_KEY", "MY_VAL", "--project", "proj-1", "--env", "env-1"])
        assert result.exit_code == 0
        assert "MY_KEY" in result.output

    def test_json_output(self):
        result = _invoke(["variables", "set", "MY_KEY", "MY_VAL", "--project", "proj-1", "--env", "env-1", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["key"] == "MY_KEY"
        assert data["set"] is True

    def test_api_error(self):
        backend = _make_backend()
        backend.variable_upsert.side_effect = RailwayAPIError("nope")
        result = _invoke(["variables", "set", "K", "V", "--project", "p", "--env", "e"], backend=backend)
        assert result.exit_code != 0


class TestVariablesDelete:
    def test_deletes_variable(self):
        result = _invoke(["variables", "delete", "MY_KEY", "--project", "proj-1", "--env", "env-1"])
        assert result.exit_code == 0
        assert "MY_KEY" in result.output

    def test_json_output(self):
        result = _invoke(["variables", "delete", "MY_KEY", "--project", "proj-1", "--env", "env-1", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["deleted"] is True

    def test_api_error(self):
        backend = _make_backend()
        backend.variable_delete.side_effect = RailwayAPIError("cannot delete")
        result = _invoke(["variables", "delete", "K", "--project", "p", "--env", "e"], backend=backend)
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# Environments
# ---------------------------------------------------------------------------

class TestEnvironmentsList:
    def test_tabular_output(self):
        result = _invoke(["environments", "list", "--project", "proj-1"])
        assert result.exit_code == 0
        assert "production" in result.output

    def test_json_output(self):
        result = _invoke(["environments", "list", "--project", "proj-1", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data[0]["id"] == "env-1"

    def test_empty(self):
        backend = _make_backend()
        backend.environments_list.return_value = []
        result = _invoke(["environments", "list", "--project", "proj-1"], backend=backend)
        assert result.exit_code == 0

    def test_api_error(self):
        backend = _make_backend()
        backend.environments_list.side_effect = RailwayAPIError("fail")
        result = _invoke(["environments", "list", "--project", "proj-1"], backend=backend)
        assert result.exit_code != 0


class TestEnvironmentsCreate:
    def test_creates_environment(self):
        result = _invoke(["environments", "create", "staging", "--project", "proj-1"])
        assert result.exit_code == 0
        assert "staging" in result.output

    def test_json_output(self):
        result = _invoke(["environments", "create", "staging", "--project", "proj-1", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["id"] == "env-2"

    def test_api_error(self):
        backend = _make_backend()
        backend.environment_create.side_effect = RailwayAPIError("nope")
        result = _invoke(["environments", "create", "bad", "--project", "proj-1"], backend=backend)
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# Backend unit tests
# ---------------------------------------------------------------------------

class TestRailwayBackend:
    def test_no_token_raises(self):
        from cli_anything.railway.utils.railway_backend import RailwayBackend, RailwayAPIError
        with pytest.raises(RailwayAPIError, match="No Railway token"):
            RailwayBackend("")

    def test_auth_header_set(self):
        from cli_anything.railway.utils.railway_backend import RailwayBackend
        backend = RailwayBackend("my-token")
        assert backend._session.headers["Authorization"] == "Bearer my-token"

    def test_http_error_raises(self):
        import requests
        from cli_anything.railway.utils.railway_backend import RailwayBackend, RailwayAPIError
        backend = RailwayBackend("tok")
        mock_resp = MagicMock()
        mock_resp.ok = False
        mock_resp.status_code = 500
        mock_resp.text = "Internal Server Error"
        with patch.object(backend._session, "post", return_value=mock_resp):
            with pytest.raises(RailwayAPIError):
                backend.query("query { projects { edges { node { id } } } }")

    def test_graphql_errors_raises(self):
        from cli_anything.railway.utils.railway_backend import RailwayBackend, RailwayAPIError
        backend = RailwayBackend("tok")
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"errors": [{"message": "Not authorized"}]}
        with patch.object(backend._session, "post", return_value=mock_resp):
            with pytest.raises(RailwayAPIError, match="Not authorized"):
                backend.query("query { projects { edges { node { id } } } }")

    def test_projects_list_parses_edges(self):
        from cli_anything.railway.utils.railway_backend import RailwayBackend
        backend = RailwayBackend("tok")
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "data": {
                "projects": {
                    "edges": [
                        {"node": {"id": "p1", "name": "Alpha", "description": "", "createdAt": "", "updatedAt": ""}}
                    ]
                }
            }
        }
        with patch.object(backend._session, "post", return_value=mock_resp):
            projects = backend.projects_list()
        assert len(projects) == 1
        assert projects[0]["id"] == "p1"

    def test_401_raises_auth_error(self):
        from cli_anything.railway.utils.railway_backend import RailwayBackend, RailwayAPIError
        backend = RailwayBackend("bad-token")
        mock_resp = MagicMock()
        mock_resp.ok = False
        mock_resp.status_code = 401
        mock_resp.text = "Unauthorized"
        with patch.object(backend._session, "post", return_value=mock_resp):
            with pytest.raises(RailwayAPIError, match="Authentication failed"):
                backend.projects_list()


# ---------------------------------------------------------------------------
# Logs
# ---------------------------------------------------------------------------

class TestLogsDeployment:
    def test_tabular_output(self):
        result = _invoke(["logs", "deployment", "dep-1"])
        assert result.exit_code == 0
        assert "Server started" in result.output

    def test_build_logs_flag(self):
        result = _invoke(["logs", "deployment", "dep-1", "--build"])
        assert result.exit_code == 0
        assert "Build complete" in result.output

    def test_json_output(self):
        result = _invoke(["logs", "deployment", "dep-1", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data[0]["message"] == "Server started"

    def test_empty(self):
        backend = _make_backend()
        backend.deployment_logs.return_value = []
        result = _invoke(["logs", "deployment", "dep-1"], backend=backend)
        assert result.exit_code == 0
        assert "No log" in result.output

    def test_api_error(self):
        backend = _make_backend()
        backend.deployment_logs.side_effect = RailwayAPIError("boom")
        result = _invoke(["logs", "deployment", "dep-1"], backend=backend)
        assert result.exit_code != 0


class TestLogsService:
    def test_tabular_output(self):
        result = _invoke(["logs", "service", "svc-1", "--env", "env-1"])
        assert result.exit_code == 0
        assert "Server started" in result.output

    def test_json_output(self):
        result = _invoke(["logs", "service", "svc-1", "--env", "env-1", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)

    def test_no_deployments(self):
        backend = _make_backend()
        backend.deployments_list.return_value = []
        result = _invoke(["logs", "service", "svc-1", "--env", "env-1"], backend=backend)
        assert result.exit_code == 0
        assert "No deployments" in result.output

    def test_api_error_on_deployments(self):
        backend = _make_backend()
        backend.deployments_list.side_effect = RailwayAPIError("boom")
        result = _invoke(["logs", "service", "svc-1", "--env", "env-1"], backend=backend)
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# Domains
# ---------------------------------------------------------------------------

class TestDomainsList:
    def test_tabular_output(self):
        result = _invoke(["domains", "list", "--service", "svc-1", "--env", "env-1"])
        assert result.exit_code == 0
        assert "example.com" in result.output

    def test_json_output(self):
        result = _invoke(["domains", "list", "--service", "svc-1", "--env", "env-1", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data[0]["id"] == "dom-1"

    def test_empty(self):
        backend = _make_backend()
        backend.domains_list.return_value = []
        result = _invoke(["domains", "list", "--service", "svc-1", "--env", "env-1"], backend=backend)
        assert result.exit_code == 0

    def test_api_error(self):
        backend = _make_backend()
        backend.domains_list.side_effect = RailwayAPIError("fail")
        result = _invoke(["domains", "list", "--service", "svc-1", "--env", "env-1"], backend=backend)
        assert result.exit_code != 0


class TestDomainsCreate:
    def test_creates_domain(self):
        result = _invoke(["domains", "create", "new.example.com", "--service", "svc-1", "--env", "env-1"])
        assert result.exit_code == 0
        assert "new.example.com" in result.output

    def test_json_output(self):
        result = _invoke(["domains", "create", "new.example.com", "--service", "svc-1", "--env", "env-1", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["id"] == "dom-3"

    def test_api_error(self):
        backend = _make_backend()
        backend.custom_domain_create.side_effect = RailwayAPIError("nope")
        result = _invoke(["domains", "create", "x.com", "--service", "svc-1", "--env", "env-1"], backend=backend)
        assert result.exit_code != 0


class TestDomainsDelete:
    def test_deletes(self):
        result = _invoke(["domains", "delete", "dom-1"])
        assert result.exit_code == 0

    def test_json_output(self):
        result = _invoke(["domains", "delete", "dom-1", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["deleted"] is True

    def test_api_error(self):
        backend = _make_backend()
        backend.custom_domain_delete.side_effect = RailwayAPIError("fail")
        result = _invoke(["domains", "delete", "dom-1"], backend=backend)
        assert result.exit_code != 0


class TestDomainsGenerate:
    def test_generates(self):
        result = _invoke(["domains", "generate", "--service", "svc-1", "--env", "env-1"])
        assert result.exit_code == 0
        assert "generated.up.railway.app" in result.output

    def test_json_output(self):
        result = _invoke(["domains", "generate", "--service", "svc-1", "--env", "env-1", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["id"] == "dom-4"

    def test_api_error(self):
        backend = _make_backend()
        backend.service_domain_create.side_effect = RailwayAPIError("fail")
        result = _invoke(["domains", "generate", "--service", "svc-1", "--env", "env-1"], backend=backend)
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# Volumes
# ---------------------------------------------------------------------------

class TestVolumesList:
    def test_tabular_output(self):
        result = _invoke(["volumes", "list", "--project", "proj-1"])
        assert result.exit_code == 0
        assert "data" in result.output

    def test_json_output(self):
        result = _invoke(["volumes", "list", "--project", "proj-1", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data[0]["id"] == "vol-1"

    def test_empty(self):
        backend = _make_backend()
        backend.volumes_list.return_value = []
        result = _invoke(["volumes", "list", "--project", "proj-1"], backend=backend)
        assert result.exit_code == 0

    def test_api_error(self):
        backend = _make_backend()
        backend.volumes_list.side_effect = RailwayAPIError("fail")
        result = _invoke(["volumes", "list", "--project", "proj-1"], backend=backend)
        assert result.exit_code != 0


class TestVolumesCreate:
    def test_creates_volume(self):
        result = _invoke(["volumes", "create", "uploads", "--project", "proj-1"])
        assert result.exit_code == 0
        assert "uploads" in result.output

    def test_json_output(self):
        result = _invoke(["volumes", "create", "uploads", "--project", "proj-1", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["id"] == "vol-2"

    def test_api_error(self):
        backend = _make_backend()
        backend.volume_create.side_effect = RailwayAPIError("fail")
        result = _invoke(["volumes", "create", "x", "--project", "proj-1"], backend=backend)
        assert result.exit_code != 0


class TestVolumesDelete:
    def test_deletes(self):
        result = _invoke(["volumes", "delete", "vol-1"])
        assert result.exit_code == 0

    def test_json_output(self):
        result = _invoke(["volumes", "delete", "vol-1", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["deleted"] is True

    def test_api_error(self):
        backend = _make_backend()
        backend.volume_delete.side_effect = RailwayAPIError("fail")
        result = _invoke(["volumes", "delete", "vol-1"], backend=backend)
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

class TestMetricsService:
    def test_tabular_output(self):
        result = _invoke(["metrics", "service", "svc-1", "--env", "env-1"])
        assert result.exit_code == 0
        assert "12.50%" in result.output

    def test_json_output(self):
        result = _invoke(["metrics", "service", "svc-1", "--env", "env-1", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["cpuPercentage"] == 12.5

    def test_empty(self):
        backend = _make_backend()
        backend.service_metrics.return_value = {}
        result = _invoke(["metrics", "service", "svc-1", "--env", "env-1"], backend=backend)
        assert result.exit_code == 0

    def test_api_error(self):
        backend = _make_backend()
        backend.service_metrics.side_effect = RailwayAPIError("fail")
        result = _invoke(["metrics", "service", "svc-1", "--env", "env-1"], backend=backend)
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

class TestTemplatesList:
    def test_tabular_output(self):
        result = _invoke(["templates", "list"])
        assert result.exit_code == 0
        assert "django" in result.output.lower()

    def test_json_output(self):
        result = _invoke(["templates", "list", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data[0]["code"] == "django"

    def test_empty(self):
        backend = _make_backend()
        backend.templates_list.return_value = []
        result = _invoke(["templates", "list"], backend=backend)
        assert result.exit_code == 0

    def test_api_error(self):
        backend = _make_backend()
        backend.templates_list.side_effect = RailwayAPIError("fail")
        result = _invoke(["templates", "list"], backend=backend)
        assert result.exit_code != 0


class TestTemplatesDeploy:
    def test_deploys(self):
        result = _invoke(["templates", "deploy", "django", "--project", "proj-1"])
        assert result.exit_code == 0
        assert "django" in result.output.lower()

    def test_json_output(self):
        result = _invoke(["templates", "deploy", "django", "--project", "proj-1", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["projectId"] == "proj-1"

    def test_api_error(self):
        backend = _make_backend()
        backend.template_deploy.side_effect = RailwayAPIError("fail")
        result = _invoke(["templates", "deploy", "bad", "--project", "proj-1"], backend=backend)
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# Deployments rollback
# ---------------------------------------------------------------------------

class TestDeploymentsRollback:
    def test_success(self):
        result = _invoke(["deployments", "rollback", "dep-1"])
        assert result.exit_code == 0
        assert "dep-1" in result.output

    def test_json_output(self):
        result = _invoke(["deployments", "rollback", "dep-1", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["rolledBack"] is True

    def test_api_error(self):
        backend = _make_backend()
        backend.deployment_rollback.side_effect = RailwayAPIError("fail")
        result = _invoke(["deployments", "rollback", "dep-1"], backend=backend)
        assert result.exit_code != 0

    def test_false_result(self):
        backend = _make_backend()
        backend.deployment_rollback.return_value = False
        result = _invoke(["deployments", "rollback", "dep-1"], backend=backend)
        assert result.exit_code == 0
        assert "false" in result.output.lower() or "warning" in result.output.lower() or "Rollback" in result.output


# ---------------------------------------------------------------------------
# Service config
# ---------------------------------------------------------------------------

class TestServiceConfigGet:
    def test_shows_config(self):
        result = _invoke(["service-config", "get", "svc-1", "--env", "env-1"])
        assert result.exit_code == 0
        assert "node server.js" in result.output

    def test_json_output(self):
        result = _invoke(["service-config", "get", "svc-1", "--env", "env-1", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["startCommand"] == "node server.js"

    def test_empty(self):
        backend = _make_backend()
        backend.service_instance_get.return_value = {}
        result = _invoke(["service-config", "get", "svc-1", "--env", "env-1"], backend=backend)
        assert result.exit_code == 0

    def test_api_error(self):
        backend = _make_backend()
        backend.service_instance_get.side_effect = RailwayAPIError("fail")
        result = _invoke(["service-config", "get", "svc-1", "--env", "env-1"], backend=backend)
        assert result.exit_code != 0


class TestServiceConfigSetters:
    def _check_update(self, subcmd, extra_args=None):
        args = ["service-config", subcmd, "svc-1"] + (extra_args or []) + ["--env", "env-1"]
        result = _invoke(args)
        assert result.exit_code == 0
        assert "updated" in result.output.lower() or "configuration" in result.output.lower()

    def test_set_start_command(self):
        self._check_update("set-start-command", ["python app.py"])

    def test_set_build_command(self):
        self._check_update("set-build-command", ["pip install -r requirements.txt"])

    def test_set_dockerfile(self):
        self._check_update("set-dockerfile", ["Dockerfile.prod"])

    def test_set_health_check(self):
        self._check_update("set-health-check", ["/healthz"])

    def test_set_restart_policy(self):
        self._check_update("set-restart-policy", ["ALWAYS"])

    def test_set_root_dir(self):
        self._check_update("set-root-dir", ["/src"])

    def test_invalid_restart_policy(self):
        result = _invoke(["service-config", "set-restart-policy", "svc-1", "INVALID", "--env", "env-1"])
        assert result.exit_code != 0

    def test_json_output(self):
        result = _invoke(["service-config", "set-start-command", "svc-1", "node app.js", "--env", "env-1", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["updated"] is True

    def test_api_error(self):
        backend = _make_backend()
        backend.service_instance_update.side_effect = RailwayAPIError("fail")
        result = _invoke(["service-config", "set-start-command", "svc-1", "cmd", "--env", "env-1"], backend=backend)
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# TCP Proxies
# ---------------------------------------------------------------------------

class TestTcpProxiesList:
    def test_tabular_output(self):
        result = _invoke(["tcp-proxies", "list", "--service", "svc-1", "--env", "env-1"])
        assert result.exit_code == 0
        assert "3000" in result.output

    def test_json_output(self):
        result = _invoke(["tcp-proxies", "list", "--service", "svc-1", "--env", "env-1", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data[0]["id"] == "tcp-1"

    def test_empty(self):
        backend = _make_backend()
        backend.tcp_proxies_list.return_value = []
        result = _invoke(["tcp-proxies", "list", "--service", "svc-1", "--env", "env-1"], backend=backend)
        assert result.exit_code == 0

    def test_api_error(self):
        backend = _make_backend()
        backend.tcp_proxies_list.side_effect = RailwayAPIError("fail")
        result = _invoke(["tcp-proxies", "list", "--service", "svc-1", "--env", "env-1"], backend=backend)
        assert result.exit_code != 0


class TestTcpProxiesCreate:
    def test_creates(self):
        result = _invoke(["tcp-proxies", "create", "--service", "svc-1", "--env", "env-1", "--port", "3000"])
        assert result.exit_code == 0
        assert "new-proxy.railway.app" in result.output

    def test_json_output(self):
        result = _invoke(["tcp-proxies", "create", "--service", "svc-1", "--env", "env-1", "--port", "3000", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["id"] == "tcp-2"

    def test_api_error(self):
        backend = _make_backend()
        backend.tcp_proxy_create.side_effect = RailwayAPIError("fail")
        result = _invoke(["tcp-proxies", "create", "--service", "svc-1", "--env", "env-1", "--port", "3000"], backend=backend)
        assert result.exit_code != 0


class TestTcpProxiesDelete:
    def test_deletes(self):
        result = _invoke(["tcp-proxies", "delete", "tcp-1"])
        assert result.exit_code == 0

    def test_json_output(self):
        result = _invoke(["tcp-proxies", "delete", "tcp-1", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["deleted"] is True

    def test_api_error(self):
        backend = _make_backend()
        backend.tcp_proxy_delete.side_effect = RailwayAPIError("fail")
        result = _invoke(["tcp-proxies", "delete", "tcp-1"], backend=backend)
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# Webhooks
# ---------------------------------------------------------------------------

class TestWebhooksList:
    def test_tabular_output(self):
        result = _invoke(["webhooks", "list", "--project", "proj-1"])
        assert result.exit_code == 0
        assert "hooks.example.com" in result.output

    def test_json_output(self):
        result = _invoke(["webhooks", "list", "--project", "proj-1", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data[0]["id"] == "wh-1"

    def test_empty(self):
        backend = _make_backend()
        backend.webhooks_list.return_value = []
        result = _invoke(["webhooks", "list", "--project", "proj-1"], backend=backend)
        assert result.exit_code == 0

    def test_api_error(self):
        backend = _make_backend()
        backend.webhooks_list.side_effect = RailwayAPIError("fail")
        result = _invoke(["webhooks", "list", "--project", "proj-1"], backend=backend)
        assert result.exit_code != 0


class TestWebhooksCreate:
    def test_creates(self):
        result = _invoke(["webhooks", "create", "https://example.com/hook", "--project", "proj-1"])
        assert result.exit_code == 0
        assert "hooks.example.com" in result.output

    def test_json_output(self):
        result = _invoke(["webhooks", "create", "https://example.com/hook", "--project", "proj-1", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["id"] == "wh-2"

    def test_api_error(self):
        backend = _make_backend()
        backend.webhook_create.side_effect = RailwayAPIError("fail")
        result = _invoke(["webhooks", "create", "https://x.com", "--project", "proj-1"], backend=backend)
        assert result.exit_code != 0


class TestWebhooksDelete:
    def test_deletes(self):
        result = _invoke(["webhooks", "delete", "wh-1"])
        assert result.exit_code == 0

    def test_json_output(self):
        result = _invoke(["webhooks", "delete", "wh-1", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["deleted"] is True

    def test_api_error(self):
        backend = _make_backend()
        backend.webhook_delete.side_effect = RailwayAPIError("fail")
        result = _invoke(["webhooks", "delete", "wh-1"], backend=backend)
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# Team
# ---------------------------------------------------------------------------

class TestTeamList:
    def test_tabular_output(self):
        result = _invoke(["team", "list"])
        assert result.exit_code == 0
        assert "alice@example.com" in result.output

    def test_json_output(self):
        result = _invoke(["team", "list", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data[0]["id"] == "usr-1"

    def test_empty(self):
        backend = _make_backend()
        backend.team_list.return_value = []
        result = _invoke(["team", "list"], backend=backend)
        assert result.exit_code == 0

    def test_api_error(self):
        backend = _make_backend()
        backend.team_list.side_effect = RailwayAPIError("fail")
        result = _invoke(["team", "list"], backend=backend)
        assert result.exit_code != 0


class TestTeamInvite:
    def test_invites(self):
        result = _invoke(["team", "invite", "bob@example.com", "--team", "team-1"])
        assert result.exit_code == 0
        assert "bob@example.com" in result.output

    def test_json_output(self):
        result = _invoke(["team", "invite", "bob@example.com", "--team", "team-1", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["invited"] is True

    def test_role_admin(self):
        result = _invoke(["team", "invite", "bob@example.com", "--team", "team-1", "--role", "ADMIN"])
        assert result.exit_code == 0

    def test_invalid_role(self):
        result = _invoke(["team", "invite", "bob@example.com", "--team", "team-1", "--role", "SUPERUSER"])
        assert result.exit_code != 0

    def test_api_error(self):
        backend = _make_backend()
        backend.team_invite.side_effect = RailwayAPIError("fail")
        result = _invoke(["team", "invite", "bob@example.com", "--team", "team-1"], backend=backend)
        assert result.exit_code != 0


class TestTeamRemove:
    def test_removes(self):
        result = _invoke(["team", "remove", "usr-1", "--team", "team-1"])
        assert result.exit_code == 0
        assert "usr-1" in result.output

    def test_json_output(self):
        result = _invoke(["team", "remove", "usr-1", "--team", "team-1", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["removed"] is True

    def test_api_error(self):
        backend = _make_backend()
        backend.team_member_remove.side_effect = RailwayAPIError("fail")
        result = _invoke(["team", "remove", "usr-1", "--team", "team-1"], backend=backend)
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# Services create-cron
# ---------------------------------------------------------------------------

class TestServicesCreateCron:
    def test_creates_cron(self):
        result = _invoke(["services", "create-cron", "my-cron", "0 * * * *", "--project", "proj-1"])
        assert result.exit_code == 0
        assert "my-cron" in result.output

    def test_json_output(self):
        result = _invoke(["services", "create-cron", "my-cron", "0 * * * *", "--project", "proj-1", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["id"] == "svc-cron-1"

    def test_api_error(self):
        backend = _make_backend()
        backend.service_create_cron.side_effect = RailwayAPIError("fail")
        result = _invoke(["services", "create-cron", "bad", "* * * * *", "--project", "proj-1"], backend=backend)
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# Networking
# ---------------------------------------------------------------------------

class TestNetworkingList:
    def test_tabular_output(self):
        result = _invoke(["networking", "list", "--project", "proj-1"])
        assert result.exit_code == 0
        assert "web.railway.internal" in result.output

    def test_json_output(self):
        result = _invoke(["networking", "list", "--project", "proj-1", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data[0]["internalDomain"] == "web.railway.internal"

    def test_empty(self):
        backend = _make_backend()
        backend.networking_list.return_value = []
        result = _invoke(["networking", "list", "--project", "proj-1"], backend=backend)
        assert result.exit_code == 0

    def test_api_error(self):
        backend = _make_backend()
        backend.networking_list.side_effect = RailwayAPIError("fail")
        result = _invoke(["networking", "list", "--project", "proj-1"], backend=backend)
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# Git
# ---------------------------------------------------------------------------

class TestGitConnect:
    def test_connects(self):
        result = _invoke(["git", "connect", "svc-1", "acme/myapp", "main"])
        assert result.exit_code == 0
        assert "acme/myapp" in result.output

    def test_json_output(self):
        result = _invoke(["git", "connect", "svc-1", "acme/myapp", "main", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["connected"] is True

    def test_api_error(self):
        backend = _make_backend()
        backend.git_connect.side_effect = RailwayAPIError("fail")
        result = _invoke(["git", "connect", "svc-1", "acme/myapp", "main"], backend=backend)
        assert result.exit_code != 0


class TestGitDisconnect:
    def test_disconnects(self):
        result = _invoke(["git", "disconnect", "svc-1"])
        assert result.exit_code == 0
        assert "svc-1" in result.output

    def test_json_output(self):
        result = _invoke(["git", "disconnect", "svc-1", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["disconnected"] is True

    def test_api_error(self):
        backend = _make_backend()
        backend.git_disconnect.side_effect = RailwayAPIError("fail")
        result = _invoke(["git", "disconnect", "svc-1"], backend=backend)
        assert result.exit_code != 0
