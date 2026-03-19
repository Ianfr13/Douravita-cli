"""Variable operations for GTM CLI."""
from googleapiclient.errors import HttpError
from cli_anything.google_tag_manager.utils import gtm_backend as backend

VARIABLE_TABLE_HEADERS = ["Variable ID", "Name", "Type"]

COMMON_VARIABLE_TYPES = [
    "v",        # Constant
    "k",        # First-Party Cookie
    "d",        # Data Layer Variable
    "j",        # Custom JavaScript
    "u",        # URL
    "jsm",      # JavaScript Variable
    "remm",     # Regular Expression Table
    "smm",      # Lookup Table
    "gas",      # Google Analytics Settings
    "gtes",     # Google Tag: Event Settings
    "aev",      # Auto-Event Variable
    "e",        # Element
    "vis",      # Visibility
]


def list_variables(service, account_id: str, container_id: str,
                   workspace_id: str) -> list[dict]:
    """List all variables in a workspace."""
    if not all([account_id, container_id, workspace_id]):
        raise ValueError("account_id, container_id, and workspace_id are required.")
    try:
        return backend.list_variables(service, str(account_id), str(container_id),
                                      str(workspace_id))
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))


def get_variable(service, account_id: str, container_id: str,
                 workspace_id: str, variable_id: str) -> dict:
    """Get a specific variable."""
    if not all([account_id, container_id, workspace_id, variable_id]):
        raise ValueError(
            "account_id, container_id, workspace_id, and variable_id are required."
        )
    try:
        return backend.get_variable(service, str(account_id), str(container_id),
                                     str(workspace_id), str(variable_id))
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))


def create_variable(service, account_id: str, container_id: str,
                    workspace_id: str, name: str, variable_type: str,
                    parameters: list = None) -> dict:
    """Create a new variable.

    Args:
        variable_type: GTM variable type (e.g., 'v' for constant, 'd' for data layer).
        parameters: List of parameter dicts.
    """
    if not all([account_id, container_id, workspace_id]):
        raise ValueError("account_id, container_id, and workspace_id are required.")
    if not name or not name.strip():
        raise ValueError("Variable name cannot be empty.")
    if not variable_type or not variable_type.strip():
        raise ValueError("variable_type cannot be empty.")

    try:
        return backend.create_variable(
            service, str(account_id), str(container_id), str(workspace_id),
            name.strip(), variable_type.strip(),
            parameters=parameters,
        )
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))


def update_variable(service, account_id: str, container_id: str,
                    workspace_id: str, variable_id: str,
                    name: str = None, parameters: list = None) -> dict:
    """Update an existing variable."""
    if not all([account_id, container_id, workspace_id, variable_id]):
        raise ValueError(
            "account_id, container_id, workspace_id, and variable_id are required."
        )
    try:
        current = backend.get_variable(service, str(account_id), str(container_id),
                                        str(workspace_id), str(variable_id))
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))

    body = dict(current)
    if name is not None:
        body["name"] = name.strip()
    if parameters is not None:
        body["parameter"] = parameters

    try:
        return backend.update_variable(service, str(account_id), str(container_id),
                                        str(workspace_id), str(variable_id), body)
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))


def delete_variable(service, account_id: str, container_id: str,
                    workspace_id: str, variable_id: str) -> dict:
    """Delete a variable."""
    if not all([account_id, container_id, workspace_id, variable_id]):
        raise ValueError(
            "account_id, container_id, workspace_id, and variable_id are required."
        )
    try:
        backend.delete_variable(service, str(account_id), str(container_id),
                                 str(workspace_id), str(variable_id))
        return {"deleted": True, "variable_id": variable_id}
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))


def revert_variable(service, account_id: str, container_id: str,
                    workspace_id: str, variable_id: str) -> dict:
    """Revert changes to a variable."""
    if not all([account_id, container_id, workspace_id, variable_id]):
        raise ValueError(
            "account_id, container_id, workspace_id, and variable_id are required."
        )
    try:
        return backend.revert_variable(service, str(account_id), str(container_id),
                                        str(workspace_id), str(variable_id))
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))


def format_variable_row(var: dict) -> list:
    """Format a variable dict into a table row."""
    return [
        var.get("variableId", ""),
        var.get("name", ""),
        var.get("type", ""),
    ]
