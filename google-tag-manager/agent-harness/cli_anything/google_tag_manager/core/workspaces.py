"""Workspace operations for GTM CLI."""
from googleapiclient.errors import HttpError
from cli_anything.google_tag_manager.utils import gtm_backend as backend

WORKSPACE_TABLE_HEADERS = ["Workspace ID", "Name", "Description", "Fingerprint"]


def list_workspaces(service, account_id: str, container_id: str) -> list[dict]:
    """List all workspaces in a container."""
    if not account_id or not container_id:
        raise ValueError("account_id and container_id are required.")
    try:
        return backend.list_workspaces(service, str(account_id), str(container_id))
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))


def get_workspace(service, account_id: str, container_id: str,
                  workspace_id: str) -> dict:
    """Get a specific workspace."""
    if not all([account_id, container_id, workspace_id]):
        raise ValueError("account_id, container_id, and workspace_id are required.")
    try:
        return backend.get_workspace(service, str(account_id), str(container_id),
                                     str(workspace_id))
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))


def create_workspace(service, account_id: str, container_id: str,
                     name: str, description: str = "") -> dict:
    """Create a new workspace."""
    if not account_id or not container_id:
        raise ValueError("account_id and container_id are required.")
    if not name or not name.strip():
        raise ValueError("Workspace name cannot be empty.")
    try:
        return backend.create_workspace(service, str(account_id), str(container_id),
                                        name.strip(), description)
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))


def update_workspace(service, account_id: str, container_id: str,
                     workspace_id: str, name: str = None,
                     description: str = None) -> dict:
    """Update a workspace."""
    if not all([account_id, container_id, workspace_id]):
        raise ValueError("account_id, container_id, and workspace_id are required.")
    try:
        current = backend.get_workspace(service, str(account_id), str(container_id),
                                        str(workspace_id))
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))

    body = dict(current)
    if name is not None:
        body["name"] = name.strip()
    if description is not None:
        body["description"] = description

    try:
        return backend.update_workspace(service, str(account_id), str(container_id),
                                        str(workspace_id), body)
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))


def delete_workspace(service, account_id: str, container_id: str,
                     workspace_id: str) -> dict:
    """Delete a workspace."""
    if not all([account_id, container_id, workspace_id]):
        raise ValueError("account_id, container_id, and workspace_id are required.")
    try:
        backend.delete_workspace(service, str(account_id), str(container_id),
                                 str(workspace_id))
        return {"deleted": True, "workspace_id": workspace_id}
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))


def workspace_status(service, account_id: str, container_id: str,
                     workspace_id: str) -> dict:
    """Get status (changes, conflicts) for a workspace."""
    if not all([account_id, container_id, workspace_id]):
        raise ValueError("account_id, container_id, and workspace_id are required.")
    try:
        return backend.workspace_status(service, str(account_id), str(container_id),
                                        str(workspace_id))
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))


def sync_workspace(service, account_id: str, container_id: str,
                   workspace_id: str) -> dict:
    """Sync workspace with the latest container version."""
    if not all([account_id, container_id, workspace_id]):
        raise ValueError("account_id, container_id, and workspace_id are required.")
    try:
        return backend.sync_workspace(service, str(account_id), str(container_id),
                                      str(workspace_id))
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))


def create_version(service, account_id: str, container_id: str,
                   workspace_id: str, name: str = "",
                   notes: str = "") -> dict:
    """Create a new container version from a workspace."""
    if not all([account_id, container_id, workspace_id]):
        raise ValueError("account_id, container_id, and workspace_id are required.")
    try:
        return backend.create_version(service, str(account_id), str(container_id),
                                      str(workspace_id), name=name, notes=notes)
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))


def quick_preview(service, account_id: str, container_id: str,
                  workspace_id: str) -> dict:
    """Create a quick preview of a workspace."""
    if not all([account_id, container_id, workspace_id]):
        raise ValueError("account_id, container_id, and workspace_id are required.")
    try:
        return backend.quick_preview(service, str(account_id), str(container_id),
                                     str(workspace_id))
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))


def format_workspace_row(ws: dict) -> list:
    """Format a workspace dict into a table row."""
    return [
        ws.get("workspaceId", ""),
        ws.get("name", ""),
        ws.get("description", ""),
        ws.get("fingerprint", "")[:12] if ws.get("fingerprint") else "",
    ]
