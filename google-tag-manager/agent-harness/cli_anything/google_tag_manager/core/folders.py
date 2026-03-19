"""Folder operations for GTM CLI."""
from googleapiclient.errors import HttpError
from cli_anything.google_tag_manager.utils import gtm_backend as backend

FOLDER_TABLE_HEADERS = ["Folder ID", "Name", "Fingerprint"]


def list_folders(service, account_id: str, container_id: str,
                 workspace_id: str) -> list[dict]:
    """List all folders in a workspace."""
    if not all([account_id, container_id, workspace_id]):
        raise ValueError("account_id, container_id, and workspace_id are required.")
    try:
        return backend.list_folders(service, str(account_id), str(container_id),
                                    str(workspace_id))
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))


def get_folder(service, account_id: str, container_id: str,
               workspace_id: str, folder_id: str) -> dict:
    """Get a specific folder."""
    if not all([account_id, container_id, workspace_id, folder_id]):
        raise ValueError(
            "account_id, container_id, workspace_id, and folder_id are required."
        )
    try:
        return backend.get_folder(service, str(account_id), str(container_id),
                                   str(workspace_id), str(folder_id))
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))


def create_folder(service, account_id: str, container_id: str,
                  workspace_id: str, name: str) -> dict:
    """Create a new folder."""
    if not all([account_id, container_id, workspace_id]):
        raise ValueError("account_id, container_id, and workspace_id are required.")
    if not name or not name.strip():
        raise ValueError("Folder name cannot be empty.")
    try:
        return backend.create_folder(service, str(account_id), str(container_id),
                                      str(workspace_id), name.strip())
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))


def update_folder(service, account_id: str, container_id: str,
                  workspace_id: str, folder_id: str, name: str) -> dict:
    """Rename a folder."""
    if not all([account_id, container_id, workspace_id, folder_id]):
        raise ValueError(
            "account_id, container_id, workspace_id, and folder_id are required."
        )
    if not name or not name.strip():
        raise ValueError("Folder name cannot be empty.")

    try:
        current = backend.get_folder(service, str(account_id), str(container_id),
                                      str(workspace_id), str(folder_id))
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))

    body = dict(current)
    body["name"] = name.strip()

    try:
        return backend.update_folder(service, str(account_id), str(container_id),
                                      str(workspace_id), str(folder_id), body)
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))


def delete_folder(service, account_id: str, container_id: str,
                  workspace_id: str, folder_id: str) -> dict:
    """Delete a folder."""
    if not all([account_id, container_id, workspace_id, folder_id]):
        raise ValueError(
            "account_id, container_id, workspace_id, and folder_id are required."
        )
    try:
        backend.delete_folder(service, str(account_id), str(container_id),
                               str(workspace_id), str(folder_id))
        return {"deleted": True, "folder_id": folder_id}
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))


def folder_entities(service, account_id: str, container_id: str,
                    workspace_id: str, folder_id: str) -> dict:
    """List entities in a folder."""
    if not all([account_id, container_id, workspace_id, folder_id]):
        raise ValueError(
            "account_id, container_id, workspace_id, and folder_id are required."
        )
    try:
        return backend.folder_entities(service, str(account_id), str(container_id),
                                        str(workspace_id), str(folder_id))
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))


def move_to_folder(service, account_id: str, container_id: str,
                   workspace_id: str, folder_id: str,
                   tag_ids: list = None, trigger_ids: list = None,
                   variable_ids: list = None) -> dict:
    """Move entities to a folder."""
    if not all([account_id, container_id, workspace_id, folder_id]):
        raise ValueError(
            "account_id, container_id, workspace_id, and folder_id are required."
        )
    if not any([tag_ids, trigger_ids, variable_ids]):
        raise ValueError("At least one of tag_ids, trigger_ids, or variable_ids must be provided.")
    try:
        backend.move_to_folder(service, str(account_id), str(container_id),
                                str(workspace_id), str(folder_id),
                                tag_id=tag_ids, trigger_id=trigger_ids,
                                variable_id=variable_ids)
        return {"moved": True, "folder_id": folder_id}
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))


def revert_folder(service, account_id: str, container_id: str,
                  workspace_id: str, folder_id: str) -> dict:
    """Revert changes to a folder."""
    if not all([account_id, container_id, workspace_id, folder_id]):
        raise ValueError(
            "account_id, container_id, workspace_id, and folder_id are required."
        )
    try:
        return backend.revert_folder(service, str(account_id), str(container_id),
                                      str(workspace_id), str(folder_id))
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))


def format_folder_row(folder: dict) -> list:
    """Format a folder dict into a table row."""
    fp = folder.get("fingerprint", "")
    return [
        folder.get("folderId", ""),
        folder.get("name", ""),
        fp[:12] if fp else "",
    ]
