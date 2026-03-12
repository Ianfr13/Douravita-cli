"""Secrets CRUD operations for Infisical CLI."""

from __future__ import annotations

from typing import Any

from cli_anything.infisical.utils.infisical_backend import InfisicalBackend


class SecretsClient:
    """High-level client for secrets operations.

    Args:
        backend: An InfisicalBackend instance.
        workspace_id: Target workspace/project ID.
        environment: Target environment (e.g. dev, staging, prod).
        secret_path: Secret path prefix (default: /).
    """

    def __init__(
        self,
        backend: InfisicalBackend,
        workspace_id: str,
        environment: str,
        secret_path: str = "/",
    ):
        self.backend = backend
        self.workspace_id = workspace_id
        self.environment = environment
        self.secret_path = secret_path

    def list(self) -> list[dict]:
        """Return all secrets for the configured workspace/environment."""
        return self.backend.list_secrets(
            workspace_id=self.workspace_id,
            environment=self.environment,
            secret_path=self.secret_path,
        )

    def get(self, name: str) -> dict:
        """Return a single secret by name."""
        return self.backend.get_secret(
            secret_name=name,
            workspace_id=self.workspace_id,
            environment=self.environment,
            secret_path=self.secret_path,
        )

    def create(self, name: str, value: str) -> dict:
        """Create a new secret."""
        return self.backend.create_secret(
            secret_name=name,
            secret_value=value,
            workspace_id=self.workspace_id,
            environment=self.environment,
            secret_path=self.secret_path,
        )

    def update(self, name: str, value: str) -> dict:
        """Update an existing secret."""
        return self.backend.update_secret(
            secret_name=name,
            secret_value=value,
            workspace_id=self.workspace_id,
            environment=self.environment,
            secret_path=self.secret_path,
        )

    def export_dotenv(self) -> str:
        """Return all secrets as KEY=VALUE lines."""
        secrets = self.list()
        lines = []
        for s in secrets:
            key = s.get("secretKey") or s.get("key") or s.get("name", "")
            val = s.get("secretValue") or s.get("value", "")
            lines.append(f"{key}={val}")
        return "\n".join(lines)
