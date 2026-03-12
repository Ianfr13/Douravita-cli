"""Projects (workspaces) CRUD operations for Infisical CLI."""

from __future__ import annotations

from cli_anything.infisical.utils.infisical_backend import InfisicalBackend


class ProjectsClient:
    """High-level client for project/workspace operations.

    Args:
        backend: An InfisicalBackend instance.
    """

    def __init__(self, backend: InfisicalBackend):
        self.backend = backend

    def list(self) -> list[dict]:
        """Return all accessible workspaces/projects."""
        return self.backend.list_workspaces()

    def create(self, name: str, organization_id: str) -> dict:
        """Create a new workspace/project.

        Args:
            name: Display name for the workspace.
            organization_id: Organization ID the workspace belongs to.
        """
        return self.backend.create_workspace(
            workspace_name=name,
            organization_id=organization_id,
        )
