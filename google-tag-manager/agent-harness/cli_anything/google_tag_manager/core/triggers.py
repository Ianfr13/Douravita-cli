"""Trigger operations for GTM CLI."""
from googleapiclient.errors import HttpError
from cli_anything.google_tag_manager.utils import gtm_backend as backend

TRIGGER_TABLE_HEADERS = ["Trigger ID", "Name", "Type"]

COMMON_TRIGGER_TYPES = [
    "pageview", "domReady", "windowLoaded", "click", "linkClick",
    "formSubmission", "historyChange", "jsError", "scrollDepth",
    "youtubeVideo", "elementVisibility", "customEvent", "always", "consentInit",
]


def list_triggers(service, account_id: str, container_id: str,
                  workspace_id: str) -> list[dict]:
    """List all triggers in a workspace."""
    if not all([account_id, container_id, workspace_id]):
        raise ValueError("account_id, container_id, and workspace_id are required.")
    try:
        return backend.list_triggers(service, str(account_id), str(container_id),
                                     str(workspace_id))
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))


def get_trigger(service, account_id: str, container_id: str,
                workspace_id: str, trigger_id: str) -> dict:
    """Get a specific trigger."""
    if not all([account_id, container_id, workspace_id, trigger_id]):
        raise ValueError(
            "account_id, container_id, workspace_id, and trigger_id are required."
        )
    try:
        return backend.get_trigger(service, str(account_id), str(container_id),
                                    str(workspace_id), str(trigger_id))
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))


def create_trigger(service, account_id: str, container_id: str,
                   workspace_id: str, name: str, trigger_type: str,
                   filters: list = None,
                   custom_event_filter: list = None) -> dict:
    """Create a new trigger.

    Args:
        trigger_type: e.g. 'pageview', 'click', 'customEvent', etc.
        filters: List of condition dicts for the trigger.
        custom_event_filter: Custom event filter conditions.
    """
    if not all([account_id, container_id, workspace_id]):
        raise ValueError("account_id, container_id, and workspace_id are required.")
    if not name or not name.strip():
        raise ValueError("Trigger name cannot be empty.")
    if not trigger_type or not trigger_type.strip():
        raise ValueError("trigger_type cannot be empty.")

    try:
        return backend.create_trigger(
            service, str(account_id), str(container_id), str(workspace_id),
            name.strip(), trigger_type.strip(),
            filters=filters,
            custom_event_filter=custom_event_filter,
        )
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))


def update_trigger(service, account_id: str, container_id: str,
                   workspace_id: str, trigger_id: str,
                   name: str = None, filters: list = None) -> dict:
    """Update an existing trigger."""
    if not all([account_id, container_id, workspace_id, trigger_id]):
        raise ValueError(
            "account_id, container_id, workspace_id, and trigger_id are required."
        )
    try:
        current = backend.get_trigger(service, str(account_id), str(container_id),
                                       str(workspace_id), str(trigger_id))
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))

    body = dict(current)
    if name is not None:
        body["name"] = name.strip()
    if filters is not None:
        body["filter"] = filters

    try:
        return backend.update_trigger(service, str(account_id), str(container_id),
                                       str(workspace_id), str(trigger_id), body)
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))


def delete_trigger(service, account_id: str, container_id: str,
                   workspace_id: str, trigger_id: str) -> dict:
    """Delete a trigger."""
    if not all([account_id, container_id, workspace_id, trigger_id]):
        raise ValueError(
            "account_id, container_id, workspace_id, and trigger_id are required."
        )
    try:
        backend.delete_trigger(service, str(account_id), str(container_id),
                                str(workspace_id), str(trigger_id))
        return {"deleted": True, "trigger_id": trigger_id}
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))


def revert_trigger(service, account_id: str, container_id: str,
                   workspace_id: str, trigger_id: str) -> dict:
    """Revert changes to a trigger."""
    if not all([account_id, container_id, workspace_id, trigger_id]):
        raise ValueError(
            "account_id, container_id, workspace_id, and trigger_id are required."
        )
    try:
        return backend.revert_trigger(service, str(account_id), str(container_id),
                                       str(workspace_id), str(trigger_id))
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))


def format_trigger_row(trig: dict) -> list:
    """Format a trigger dict into a table row."""
    return [
        trig.get("triggerId", ""),
        trig.get("name", ""),
        trig.get("type", ""),
    ]
