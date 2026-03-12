"""HTTP client wrapping requests for the Infisical REST API."""

from __future__ import annotations

import requests
from typing import Any


class InfisicalAPIError(Exception):
    """Raised when the Infisical API returns a non-2xx response."""

    def __init__(self, status_code: int, body: Any):
        self.status_code = status_code
        self.body = body
        super().__init__(f"Infisical API error {status_code}: {body}")


class InfisicalBackend:
    """Thin wrapper around requests for the Infisical REST API.

    Args:
        base_url: Base URL of the Infisical instance (e.g. https://sec.douravita.com.br).
        token: Bearer token for authentication.
    """

    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _url(self, path: str) -> str:
        return f"{self.base_url}/api{path}"

    def _raise_for_status(self, response: requests.Response) -> None:
        if not response.ok:
            try:
                body = response.json()
            except Exception:
                body = response.text
            raise InfisicalAPIError(response.status_code, body)

    def get(self, path: str, params: dict | None = None) -> Any:
        """Perform a GET request and return parsed JSON."""
        resp = self._session.get(self._url(path), params=params)
        self._raise_for_status(resp)
        return resp.json()

    def post(self, path: str, json: dict | None = None) -> Any:
        """Perform a POST request and return parsed JSON."""
        resp = self._session.post(self._url(path), json=json)
        self._raise_for_status(resp)
        return resp.json()

    def patch(self, path: str, json: dict | None = None) -> Any:
        """Perform a PATCH request and return parsed JSON."""
        resp = self._session.patch(self._url(path), json=json)
        self._raise_for_status(resp)
        return resp.json()

    # ------------------------------------------------------------------
    # Secrets API
    # ------------------------------------------------------------------

    def list_secrets(
        self,
        workspace_id: str,
        environment: str,
        secret_path: str = "/",
    ) -> list[dict]:
        """List all raw secrets for a workspace/environment."""
        data = self.get(
            "/v3/secrets/raw",
            params={
                "workspaceId": workspace_id,
                "environment": environment,
                "secretPath": secret_path,
            },
        )
        return data.get("secrets", data)

    def get_secret(
        self,
        secret_name: str,
        workspace_id: str,
        environment: str,
        secret_path: str = "/",
    ) -> dict:
        """Fetch a single raw secret by name."""
        data = self.get(
            f"/v3/secrets/raw/{secret_name}",
            params={
                "workspaceId": workspace_id,
                "environment": environment,
                "secretPath": secret_path,
            },
        )
        return data.get("secret", data)

    def create_secret(
        self,
        secret_name: str,
        secret_value: str,
        workspace_id: str,
        environment: str,
        secret_path: str = "/",
        secret_type: str = "shared",
    ) -> dict:
        """Create a new secret."""
        data = self.post(
            f"/v3/secrets/raw/{secret_name}",
            json={
                "workspaceId": workspace_id,
                "environment": environment,
                "secretValue": secret_value,
                "secretPath": secret_path,
                "type": secret_type,
            },
        )
        return data.get("secret", data)

    def update_secret(
        self,
        secret_name: str,
        secret_value: str,
        workspace_id: str,
        environment: str,
        secret_path: str = "/",
    ) -> dict:
        """Update an existing secret."""
        data = self.patch(
            f"/v3/secrets/raw/{secret_name}",
            json={
                "workspaceId": workspace_id,
                "environment": environment,
                "secretValue": secret_value,
                "secretPath": secret_path,
            },
        )
        return data.get("secret", data)

    # ------------------------------------------------------------------
    # Workspace / Project API
    # ------------------------------------------------------------------

    def list_workspaces(self) -> list[dict]:
        """List all workspaces accessible by the token."""
        data = self.get("/v1/workspace")
        return data.get("workspaces", data)

    def create_workspace(
        self,
        workspace_name: str,
        organization_id: str,
    ) -> dict:
        """Create a new workspace (project)."""
        data = self.post(
            "/v2/workspace",
            json={
                "workspaceName": workspace_name,
                "organizationId": organization_id,
            },
        )
        return data.get("workspace", data)
