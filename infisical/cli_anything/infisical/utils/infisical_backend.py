"""HTTP client wrapping requests for the Infisical REST API.

Covers the surface exposed by the cli-anything-infisical CLI:

- Secrets (raw v3): CRUD, bulk, tag attach/detach, move, versions, rollback
- Folders, Environments, Projects (workspace)
- Secret snapshots and rollback
- Tags (project-scoped), Secret imports
- Identities + Universal Auth (client secrets) + Service-token identities
- Audit logs
- Project memberships (users) + Groups
- Dynamic secrets + leases
- App-connections listing (generic)

All methods raise ``InfisicalAPIError`` on non-2xx responses.
"""

from __future__ import annotations

import json
import requests
from typing import Any, Iterable

__all__ = ["InfisicalAPIError", "InfisicalBackend"]


class InfisicalAPIError(Exception):
    """Raised when the Infisical API returns a non-2xx response."""

    def __init__(self, status_code: int, body: Any):
        self.status_code = status_code
        self.body = body
        super().__init__(f"Infisical API error {status_code}: {body}")


def _clean(params: dict | None) -> dict:
    """Drop None values from a query-param dict."""
    if not params:
        return {}
    return {k: v for k, v in params.items() if v is not None}


class InfisicalBackend:
    """Thin wrapper around requests for the Infisical REST API.

    Args:
        base_url: Base URL of the Infisical instance (e.g. https://sec.douravita.com.br).
        token: Bearer token for authentication.
        timeout: Request timeout in seconds (default 30).
    """

    def __init__(self, base_url: str, token: str, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
        )

    # ------------------------------------------------------------------
    # Low-level HTTP
    # ------------------------------------------------------------------

    def _url(self, path: str) -> str:
        if not path.startswith("/"):
            path = "/" + path
        return f"{self.base_url}/api{path}"

    def _raise_for_status(self, response: requests.Response) -> None:
        if not response.ok:
            try:
                body = response.json()
            except Exception:
                body = response.text
            raise InfisicalAPIError(response.status_code, body)

    def get(self, path: str, params: dict | None = None) -> Any:
        resp = self._session.get(
            self._url(path), params=_clean(params), timeout=self.timeout
        )
        self._raise_for_status(resp)
        return resp.json()

    def post(self, path: str, json: dict | None = None) -> Any:
        resp = self._session.post(
            self._url(path), json=json, timeout=self.timeout
        )
        self._raise_for_status(resp)
        if not resp.content:
            return {}
        return resp.json()

    def patch(self, path: str, json: dict | None = None) -> Any:
        resp = self._session.patch(
            self._url(path), json=json, timeout=self.timeout
        )
        self._raise_for_status(resp)
        if not resp.content:
            return {}
        return resp.json()

    def delete(self, path: str, json: dict | None = None) -> Any:
        resp = self._session.delete(
            self._url(path), json=json, timeout=self.timeout
        )
        self._raise_for_status(resp)
        if not resp.content:
            return {}
        try:
            return resp.json()
        except Exception:
            return {}

    # ==================================================================
    # Secrets (raw v3)
    # ==================================================================

    def list_secrets(
        self,
        workspace_id: str,
        environment: str,
        secret_path: str = "/",
        recursive: bool = False,
        include_imports: bool = True,
        expand_references: bool = True,
        metadata_filter: str | None = None,
        tag_slugs: str | None = None,
    ) -> list[dict]:
        """List raw secrets for a workspace/environment."""
        data = self.get(
            "/v3/secrets/raw",
            params={
                "workspaceId": workspace_id,
                "environment": environment,
                "secretPath": secret_path,
                "recursive": "true" if recursive else None,
                "include_imports": "true" if include_imports else "false",
                "expandSecretReferences": "true" if expand_references else "false",
                "metadataFilter": metadata_filter,
                "tagSlugs": tag_slugs,
            },
        )
        return data.get("secrets", data)

    def get_secret(
        self,
        secret_name: str,
        workspace_id: str,
        environment: str,
        secret_path: str = "/",
        secret_type: str = "shared",
        include_imports: bool = True,
    ) -> dict:
        data = self.get(
            f"/v3/secrets/raw/{secret_name}",
            params={
                "workspaceId": workspace_id,
                "environment": environment,
                "secretPath": secret_path,
                "type": secret_type,
                "include_imports": "true" if include_imports else "false",
            },
        )
        return data.get("secret", data)

    def get_secret_by_id(self, secret_id: str) -> dict:
        data = self.get(f"/v3/secrets/raw/id/{secret_id}")
        return data.get("secret", data)

    def create_secret(
        self,
        secret_name: str,
        secret_value: str,
        workspace_id: str,
        environment: str,
        secret_path: str = "/",
        secret_type: str = "shared",
        secret_comment: str | None = None,
        tag_ids: list[str] | None = None,
        skip_multiline_encoding: bool | None = None,
    ) -> dict:
        body: dict = {
            "workspaceId": workspace_id,
            "environment": environment,
            "secretValue": secret_value,
            "secretPath": secret_path,
            "type": secret_type,
        }
        if secret_comment is not None:
            body["secretComment"] = secret_comment
        if tag_ids:
            body["tagIds"] = tag_ids
        if skip_multiline_encoding is not None:
            body["skipMultilineEncoding"] = skip_multiline_encoding
        data = self.post(f"/v3/secrets/raw/{secret_name}", json=body)
        return data.get("secret", data)

    def update_secret(
        self,
        secret_name: str,
        workspace_id: str,
        environment: str,
        secret_value: str | None = None,
        secret_path: str = "/",
        new_secret_name: str | None = None,
        secret_comment: str | None = None,
        tag_ids: list[str] | None = None,
    ) -> dict:
        body: dict = {
            "workspaceId": workspace_id,
            "environment": environment,
            "secretPath": secret_path,
        }
        if secret_value is not None:
            body["secretValue"] = secret_value
        if new_secret_name is not None:
            body["newSecretName"] = new_secret_name
        if secret_comment is not None:
            body["secretComment"] = secret_comment
        if tag_ids is not None:
            body["tagIds"] = tag_ids
        data = self.patch(f"/v3/secrets/raw/{secret_name}", json=body)
        return data.get("secret", data)

    def delete_secret(
        self,
        secret_name: str,
        workspace_id: str,
        environment: str,
        secret_path: str = "/",
        secret_type: str = "shared",
    ) -> dict:
        data = self.delete(
            f"/v3/secrets/raw/{secret_name}",
            json={
                "workspaceId": workspace_id,
                "environment": environment,
                "secretPath": secret_path,
                "type": secret_type,
            },
        )
        return data.get("secret", data)

    def move_secrets(
        self,
        project_id: str,
        source_environment: str,
        source_secret_path: str,
        destination_environment: str,
        destination_secret_path: str,
        secret_ids: list[str],
        should_overwrite: bool = False,
    ) -> dict:
        return self.post(
            "/v3/secrets/move",
            json={
                "projectId": project_id,
                "sourceEnvironment": source_environment,
                "sourceSecretPath": source_secret_path,
                "destinationEnvironment": destination_environment,
                "destinationSecretPath": destination_secret_path,
                "secretIds": secret_ids,
                "shouldOverwrite": should_overwrite,
            },
        )

    def bulk_create_secrets(
        self,
        workspace_id: str,
        environment: str,
        secrets: list[dict],
        secret_path: str = "/",
    ) -> dict:
        return self.post(
            "/v3/secrets/batch/raw",
            json={
                "projectId": workspace_id,
                "environment": environment,
                "secretPath": secret_path,
                "secrets": secrets,
            },
        )

    def bulk_update_secrets(
        self,
        workspace_id: str,
        environment: str,
        secrets: list[dict],
        secret_path: str = "/",
    ) -> dict:
        return self.patch(
            "/v3/secrets/batch/raw",
            json={
                "projectId": workspace_id,
                "environment": environment,
                "secretPath": secret_path,
                "secrets": secrets,
            },
        )

    def bulk_delete_secrets(
        self,
        workspace_id: str,
        environment: str,
        secrets: list[dict],
        secret_path: str = "/",
    ) -> dict:
        return self.delete(
            "/v3/secrets/batch/raw",
            json={
                "projectId": workspace_id,
                "environment": environment,
                "secretPath": secret_path,
                "secrets": secrets,
            },
        )

    def attach_tags_to_secret(
        self,
        secret_name: str,
        project_slug: str,
        environment: str,
        secret_path: str,
        tag_slugs: list[str],
    ) -> dict:
        return self.post(
            f"/v3/secrets/tags/{secret_name}",
            json={
                "projectSlug": project_slug,
                "environment": environment,
                "secretPath": secret_path,
                "tagSlugs": tag_slugs,
            },
        )

    def detach_tags_from_secret(
        self,
        secret_name: str,
        project_slug: str,
        environment: str,
        secret_path: str,
        tag_slugs: list[str],
    ) -> dict:
        return self.delete(
            f"/v3/secrets/tags/{secret_name}",
            json={
                "projectSlug": project_slug,
                "environment": environment,
                "secretPath": secret_path,
                "tagSlugs": tag_slugs,
            },
        )

    # ------------------------------------------------------------------
    # Secret versions & rollback
    # ------------------------------------------------------------------

    def list_secret_versions(
        self, secret_id: str, offset: int = 0, limit: int = 20
    ) -> list[dict]:
        data = self.get(
            f"/v1/secret/{secret_id}/secret-versions",
            params={"offset": offset, "limit": limit},
        )
        return data.get("secretVersions", data)

    def rollback_secret_version(self, secret_version_id: str) -> dict:
        return self.post(f"/v1/secret/version/{secret_version_id}/restore")

    # ==================================================================
    # Folders
    # ==================================================================

    def list_folders(
        self,
        workspace_id: str,
        environment: str,
        path: str = "/",
        recursive: bool = False,
    ) -> list[dict]:
        data = self.get(
            "/v1/folders",
            params={
                "workspaceId": workspace_id,
                "environment": environment,
                "path": path,
                "recursive": "true" if recursive else None,
            },
        )
        return data.get("folders", data)

    def get_folder(self, folder_id: str) -> dict:
        data = self.get(f"/v1/folders/{folder_id}")
        return data.get("folder", data)

    def create_folder(
        self,
        workspace_id: str,
        environment: str,
        name: str,
        path: str = "/",
        description: str | None = None,
    ) -> dict:
        body: dict = {
            "workspaceId": workspace_id,
            "environment": environment,
            "name": name,
            "path": path,
        }
        if description is not None:
            body["description"] = description
        data = self.post("/v1/folders", json=body)
        return data.get("folder", data)

    def update_folder(
        self,
        folder_id: str,
        workspace_id: str,
        environment: str,
        name: str | None = None,
        path: str = "/",
        description: str | None = None,
    ) -> dict:
        body: dict = {
            "workspaceId": workspace_id,
            "environment": environment,
            "path": path,
        }
        if name is not None:
            body["name"] = name
        if description is not None:
            body["description"] = description
        data = self.patch(f"/v1/folders/{folder_id}", json=body)
        return data.get("folder", data)

    def delete_folder(
        self,
        folder_id_or_name: str,
        workspace_id: str,
        environment: str,
        path: str = "/",
    ) -> dict:
        return self.delete(
            f"/v1/folders/{folder_id_or_name}",
            json={
                "workspaceId": workspace_id,
                "environment": environment,
                "path": path,
            },
        )

    # ==================================================================
    # Environments (workspace scoped)
    # ==================================================================

    def list_environments(self, workspace_id: str) -> list[dict]:
        data = self.get(f"/v1/workspace/{workspace_id}")
        ws = data.get("workspace", data)
        return ws.get("environments", [])

    def get_environment(self, workspace_id: str, env_id: str) -> dict:
        data = self.get(f"/v1/workspace/{workspace_id}/environments/{env_id}")
        return data.get("environment", data)

    def create_environment(
        self, workspace_id: str, name: str, slug: str, position: int | None = None
    ) -> dict:
        body: dict = {"name": name, "slug": slug}
        if position is not None:
            body["position"] = position
        data = self.post(f"/v1/workspace/{workspace_id}/environments", json=body)
        return data.get("environment", data)

    def update_environment(
        self,
        workspace_id: str,
        env_id: str,
        name: str | None = None,
        slug: str | None = None,
        position: int | None = None,
    ) -> dict:
        body: dict = {}
        if name is not None:
            body["name"] = name
        if slug is not None:
            body["slug"] = slug
        if position is not None:
            body["position"] = position
        data = self.patch(
            f"/v1/workspace/{workspace_id}/environments/{env_id}", json=body
        )
        return data.get("environment", data)

    def delete_environment(self, workspace_id: str, env_id: str) -> dict:
        return self.delete(f"/v1/workspace/{workspace_id}/environments/{env_id}")

    # ==================================================================
    # Projects (workspaces)
    # ==================================================================

    def list_workspaces(self) -> list[dict]:
        data = self.get("/v1/workspace")
        return data.get("workspaces", data)

    def get_workspace(self, workspace_id: str) -> dict:
        data = self.get(f"/v1/workspace/{workspace_id}")
        return data.get("workspace", data)

    def create_workspace(
        self, workspace_name: str, organization_id: str
    ) -> dict:
        data = self.post(
            "/v2/workspace",
            json={
                "workspaceName": workspace_name,
                "organizationId": organization_id,
            },
        )
        return data.get("workspace", data)

    def update_workspace(
        self,
        workspace_id: str,
        name: str | None = None,
        description: str | None = None,
        auto_capitalization: bool | None = None,
    ) -> dict:
        body: dict = {}
        if name is not None:
            body["name"] = name
        if description is not None:
            body["description"] = description
        if auto_capitalization is not None:
            body["autoCapitalization"] = auto_capitalization
        data = self.patch(f"/v1/workspace/{workspace_id}", json=body)
        return data.get("workspace", data)

    def delete_workspace(self, workspace_id: str) -> dict:
        return self.delete(f"/v1/workspace/{workspace_id}")

    def list_workspace_memberships(self, workspace_id: str) -> list[dict]:
        data = self.get(f"/v1/workspace/{workspace_id}/memberships")
        return data.get("memberships", data)

    def update_membership_role(
        self, workspace_id: str, membership_id: str, role: str
    ) -> dict:
        data = self.patch(
            f"/v1/workspace/{workspace_id}/memberships/{membership_id}",
            json={"roles": [{"role": role}]},
        )
        return data.get("membership", data)

    def delete_workspace_membership(
        self, project_id: str, emails: list[str] | None = None,
        usernames: list[str] | None = None,
    ) -> dict:
        body: dict = {}
        if emails:
            body["emails"] = emails
        if usernames:
            body["usernames"] = usernames
        return self.delete(f"/v2/workspace/{project_id}/memberships", json=body)

    # ==================================================================
    # Secret snapshots
    # ==================================================================

    def list_snapshots(
        self,
        workspace_id: str,
        environment: str | None = None,
        folder_id: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict]:
        data = self.get(
            f"/v1/workspace/{workspace_id}/secret-snapshots",
            params={
                "environment": environment,
                "folderId": folder_id,
                "limit": limit,
                "offset": offset,
            },
        )
        return data.get("secretSnapshots", data)

    def rollback_snapshot(self, snapshot_id: str) -> dict:
        return self.post(f"/v1/secret-snapshot/{snapshot_id}/rollback")

    # ==================================================================
    # Tags (project scoped)
    # ==================================================================

    def list_tags(self, project_id: str) -> list[dict]:
        data = self.get(f"/v1/workspace/{project_id}/tags")
        return data.get("workspaceTags", data)

    def get_tag(self, project_id: str, tag_id: str) -> dict:
        data = self.get(f"/v1/workspace/{project_id}/tags/{tag_id}")
        return data.get("workspaceTag", data)

    def get_tag_by_slug(self, project_id: str, tag_slug: str) -> dict:
        data = self.get(f"/v1/workspace/{project_id}/tags/slug/{tag_slug}")
        return data.get("workspaceTag", data)

    def create_tag(
        self, project_id: str, slug: str, color: str | None = None
    ) -> dict:
        body: dict = {"slug": slug}
        if color is not None:
            body["color"] = color
        data = self.post(f"/v1/workspace/{project_id}/tags", json=body)
        return data.get("workspaceTag", data)

    def update_tag(
        self,
        project_id: str,
        tag_id: str,
        slug: str | None = None,
        color: str | None = None,
    ) -> dict:
        body: dict = {}
        if slug is not None:
            body["slug"] = slug
        if color is not None:
            body["color"] = color
        data = self.patch(f"/v1/workspace/{project_id}/tags/{tag_id}", json=body)
        return data.get("workspaceTag", data)

    def delete_tag(self, project_id: str, tag_id: str) -> dict:
        return self.delete(f"/v1/workspace/{project_id}/tags/{tag_id}")

    # ==================================================================
    # Secret imports
    # ==================================================================

    def list_secret_imports(
        self, workspace_id: str, environment: str, path: str = "/"
    ) -> list[dict]:
        data = self.get(
            "/v1/secret-imports",
            params={
                "workspaceId": workspace_id,
                "environment": environment,
                "path": path,
            },
        )
        return data.get("secretImports", data)

    def create_secret_import(
        self,
        workspace_id: str,
        environment: str,
        import_environment: str,
        import_path: str,
        path: str = "/",
        is_replication: bool = False,
    ) -> dict:
        data = self.post(
            "/v1/secret-imports",
            json={
                "workspaceId": workspace_id,
                "environment": environment,
                "path": path,
                "import": {
                    "environment": import_environment,
                    "path": import_path,
                },
                "isReplication": is_replication,
            },
        )
        return data.get("secretImport", data)

    def update_secret_import(
        self,
        secret_import_id: str,
        workspace_id: str,
        environment: str,
        import_environment: str | None = None,
        import_path: str | None = None,
        path: str = "/",
        position: int | None = None,
    ) -> dict:
        body: dict = {
            "workspaceId": workspace_id,
            "environment": environment,
            "path": path,
            "import": {},
        }
        if import_environment is not None:
            body["import"]["environment"] = import_environment
        if import_path is not None:
            body["import"]["path"] = import_path
        if position is not None:
            body["import"]["position"] = position
        data = self.patch(
            f"/v1/secret-imports/{secret_import_id}", json=body
        )
        return data.get("secretImport", data)

    def delete_secret_import(
        self,
        secret_import_id: str,
        workspace_id: str,
        environment: str,
        path: str = "/",
    ) -> dict:
        return self.delete(
            f"/v1/secret-imports/{secret_import_id}",
            json={
                "workspaceId": workspace_id,
                "environment": environment,
                "path": path,
            },
        )

    # ==================================================================
    # Identities
    # ==================================================================

    def list_identities(
        self,
        organization_id: str,
        offset: int = 0,
        limit: int = 100,
        search: str | None = None,
    ) -> list[dict]:
        data = self.get(
            "/v2/identities/search",
            params={
                "orgId": organization_id,
                "offset": offset,
                "limit": limit,
                "search": search,
            },
        )
        return data.get("identities", data)

    def get_identity(self, identity_id: str) -> dict:
        data = self.get(f"/v1/identities/{identity_id}")
        return data.get("identity", data)

    def create_identity(
        self,
        name: str,
        organization_id: str,
        role: str = "no-access",
    ) -> dict:
        data = self.post(
            "/v1/identities",
            json={
                "name": name,
                "organizationId": organization_id,
                "role": role,
            },
        )
        return data.get("identity", data)

    def update_identity(
        self,
        identity_id: str,
        name: str | None = None,
        role: str | None = None,
    ) -> dict:
        body: dict = {}
        if name is not None:
            body["name"] = name
        if role is not None:
            body["role"] = role
        data = self.patch(f"/v1/identities/{identity_id}", json=body)
        return data.get("identity", data)

    def delete_identity(self, identity_id: str) -> dict:
        return self.delete(f"/v1/identities/{identity_id}")

    # ------------------------------------------------------------------
    # Universal Auth (login + client-secrets for identities)
    # ------------------------------------------------------------------

    def universal_auth_login(self, client_id: str, client_secret: str) -> dict:
        """Exchange a client_id+client_secret for an access token."""
        # Universal auth login is unauthenticated (swaps creds for a token).
        resp = requests.post(
            self._url("/v1/auth/universal-auth/login"),
            json={"clientId": client_id, "clientSecret": client_secret},
            timeout=self.timeout,
        )
        self._raise_for_status(resp)
        return resp.json()

    def attach_universal_auth(
        self,
        identity_id: str,
        client_secret_trusted_ips: list[dict] | None = None,
        access_token_trusted_ips: list[dict] | None = None,
        access_token_ttl: int | None = None,
        access_token_max_ttl: int | None = None,
        access_token_num_uses_limit: int | None = None,
    ) -> dict:
        body: dict = {}
        if client_secret_trusted_ips is not None:
            body["clientSecretTrustedIps"] = client_secret_trusted_ips
        if access_token_trusted_ips is not None:
            body["accessTokenTrustedIps"] = access_token_trusted_ips
        if access_token_ttl is not None:
            body["accessTokenTTL"] = access_token_ttl
        if access_token_max_ttl is not None:
            body["accessTokenMaxTTL"] = access_token_max_ttl
        if access_token_num_uses_limit is not None:
            body["accessTokenNumUsesLimit"] = access_token_num_uses_limit
        return self.post(
            f"/v1/auth/universal-auth/identities/{identity_id}", json=body
        )

    def get_universal_auth(self, identity_id: str) -> dict:
        return self.get(f"/v1/auth/universal-auth/identities/{identity_id}")

    def revoke_universal_auth(self, identity_id: str) -> dict:
        return self.delete(
            f"/v1/auth/universal-auth/identities/{identity_id}"
        )

    def create_client_secret(
        self,
        identity_id: str,
        description: str = "",
        ttl: int = 0,
        num_uses_limit: int = 0,
    ) -> dict:
        return self.post(
            f"/v1/auth/universal-auth/identities/{identity_id}/client-secrets",
            json={
                "description": description,
                "ttl": ttl,
                "numUsesLimit": num_uses_limit,
            },
        )

    def list_client_secrets(self, identity_id: str) -> list[dict]:
        data = self.get(
            f"/v1/auth/universal-auth/identities/{identity_id}/client-secrets"
        )
        return data.get("clientSecretData", data)

    def revoke_client_secret(
        self, identity_id: str, client_secret_id: str
    ) -> dict:
        return self.post(
            f"/v1/auth/universal-auth/identities/{identity_id}"
            f"/client-secrets/{client_secret_id}/revoke"
        )

    # ==================================================================
    # Audit logs
    # ==================================================================

    def export_audit_logs(
        self,
        organization_id: str,
        project_id: str | None = None,
        event_type: str | None = None,
        actor: str | None = None,
        user_agent_type: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[dict]:
        data = self.get(
            f"/v1/organization/{organization_id}/audit-logs",
            params={
                "projectId": project_id,
                "eventType": event_type,
                "actor": actor,
                "userAgentType": user_agent_type,
                "startDate": start_date,
                "endDate": end_date,
                "offset": offset,
                "limit": limit,
            },
        )
        return data.get("auditLogs", data)

    # ==================================================================
    # Groups
    # ==================================================================

    def list_groups(
        self, organization_id: str, offset: int = 0, limit: int = 100
    ) -> list[dict]:
        data = self.get(
            "/v1/groups",
            params={
                "organizationId": organization_id,
                "offset": offset,
                "limit": limit,
            },
        )
        return data.get("groups", data)

    def get_group(self, group_id: str) -> dict:
        data = self.get(f"/v1/groups/{group_id}")
        return data.get("group", data)

    def create_group(
        self, name: str, slug: str, organization_id: str, role: str = "no-access"
    ) -> dict:
        data = self.post(
            "/v1/groups",
            json={
                "name": name,
                "slug": slug,
                "organizationId": organization_id,
                "role": role,
            },
        )
        return data.get("group", data)

    def update_group(
        self,
        group_id: str,
        name: str | None = None,
        slug: str | None = None,
        role: str | None = None,
    ) -> dict:
        body: dict = {}
        if name is not None:
            body["name"] = name
        if slug is not None:
            body["slug"] = slug
        if role is not None:
            body["role"] = role
        data = self.patch(f"/v1/groups/{group_id}", json=body)
        return data.get("group", data)

    def delete_group(self, group_id: str) -> dict:
        return self.delete(f"/v1/groups/{group_id}")

    def list_group_users(
        self, group_id: str, offset: int = 0, limit: int = 100,
        username: str | None = None, filter: str | None = None,
    ) -> list[dict]:
        data = self.get(
            f"/v1/groups/{group_id}/users",
            params={
                "offset": offset,
                "limit": limit,
                "username": username,
                "filter": filter,
            },
        )
        return data.get("users", data)

    def add_user_to_group(self, group_id: str, username: str) -> dict:
        return self.post(f"/v1/groups/{group_id}/users/{username}")

    def remove_user_from_group(self, group_id: str, username: str) -> dict:
        return self.delete(f"/v1/groups/{group_id}/users/{username}")

    # ==================================================================
    # Dynamic secrets
    # ==================================================================

    def list_dynamic_secrets(
        self, project_slug: str, environment_slug: str, path: str = "/"
    ) -> list[dict]:
        data = self.get(
            "/v1/dynamic-secrets",
            params={
                "projectSlug": project_slug,
                "environmentSlug": environment_slug,
                "path": path,
            },
        )
        return data.get("dynamicSecrets", data)

    def get_dynamic_secret(
        self, name: str, project_slug: str, environment_slug: str, path: str = "/"
    ) -> dict:
        data = self.get(
            f"/v1/dynamic-secrets/{name}",
            params={
                "projectSlug": project_slug,
                "environmentSlug": environment_slug,
                "path": path,
            },
        )
        return data.get("dynamicSecret", data)

    def create_dynamic_secret(
        self,
        name: str,
        project_slug: str,
        environment_slug: str,
        provider: dict,
        default_ttl: str,
        path: str = "/",
        max_ttl: str | None = None,
    ) -> dict:
        body: dict = {
            "name": name,
            "projectSlug": project_slug,
            "environmentSlug": environment_slug,
            "path": path,
            "provider": provider,
            "defaultTTL": default_ttl,
        }
        if max_ttl is not None:
            body["maxTTL"] = max_ttl
        data = self.post("/v1/dynamic-secrets", json=body)
        return data.get("dynamicSecret", data)

    def update_dynamic_secret(
        self,
        name: str,
        project_slug: str,
        environment_slug: str,
        path: str = "/",
        new_name: str | None = None,
        default_ttl: str | None = None,
        max_ttl: str | None = None,
    ) -> dict:
        body: dict = {
            "projectSlug": project_slug,
            "environmentSlug": environment_slug,
            "path": path,
            "data": {},
        }
        if new_name is not None:
            body["data"]["newName"] = new_name
        if default_ttl is not None:
            body["data"]["defaultTTL"] = default_ttl
        if max_ttl is not None:
            body["data"]["maxTTL"] = max_ttl
        data = self.patch(f"/v1/dynamic-secrets/{name}", json=body)
        return data.get("dynamicSecret", data)

    def delete_dynamic_secret(
        self,
        name: str,
        project_slug: str,
        environment_slug: str,
        path: str = "/",
        force: bool = False,
    ) -> dict:
        return self.delete(
            f"/v1/dynamic-secrets/{name}",
            json={
                "projectSlug": project_slug,
                "environmentSlug": environment_slug,
                "path": path,
                "isForced": force,
            },
        )

    def list_dynamic_secret_leases(
        self,
        name: str,
        project_slug: str,
        environment_slug: str,
        path: str = "/",
    ) -> list[dict]:
        data = self.get(
            f"/v1/dynamic-secrets/{name}/leases",
            params={
                "projectSlug": project_slug,
                "environmentSlug": environment_slug,
                "path": path,
            },
        )
        return data.get("leases", data)

    def create_dynamic_secret_lease(
        self,
        dynamic_secret_name: str,
        project_slug: str,
        environment_slug: str,
        path: str = "/",
        ttl: str | None = None,
    ) -> dict:
        body: dict = {
            "dynamicSecretName": dynamic_secret_name,
            "projectSlug": project_slug,
            "environmentSlug": environment_slug,
            "path": path,
        }
        if ttl is not None:
            body["ttl"] = ttl
        return self.post("/v1/dynamic-secrets/leases", json=body)

    def get_dynamic_secret_lease(self, lease_id: str) -> dict:
        data = self.get(f"/v1/dynamic-secrets/leases/{lease_id}")
        return data.get("lease", data)

    def renew_dynamic_secret_lease(
        self,
        lease_id: str,
        project_slug: str,
        environment_slug: str,
        path: str = "/",
        ttl: str | None = None,
    ) -> dict:
        body: dict = {
            "projectSlug": project_slug,
            "environmentSlug": environment_slug,
            "path": path,
        }
        if ttl is not None:
            body["ttl"] = ttl
        return self.post(
            f"/v1/dynamic-secrets/leases/{lease_id}/renew", json=body
        )

    def delete_dynamic_secret_lease(
        self,
        lease_id: str,
        project_slug: str,
        environment_slug: str,
        path: str = "/",
        force: bool = False,
    ) -> dict:
        return self.delete(
            f"/v1/dynamic-secrets/leases/{lease_id}",
            json={
                "projectSlug": project_slug,
                "environmentSlug": environment_slug,
                "path": path,
                "isForced": force,
            },
        )

    # ==================================================================
    # App connections (generic listing — per-provider ops are out of scope)
    # ==================================================================

    def list_app_connections(
        self, app: str | None = None, connection_name: str | None = None
    ) -> list[dict]:
        data = self.get(
            "/v1/app-connections",
            params={"app": app, "connectionName": connection_name},
        )
        return data.get("appConnections", data)

    def list_app_connection_options(self) -> list[dict]:
        data = self.get("/v1/app-connections/options")
        return data.get("appConnectionOptions", data)
