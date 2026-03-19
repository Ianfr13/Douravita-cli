"""Tag operations for GTM CLI."""
from googleapiclient.errors import HttpError
from cli_anything.google_tag_manager.utils import gtm_backend as backend

TAG_TABLE_HEADERS = ["Tag ID", "Name", "Type", "Firing Triggers", "Status"]

# Common GTM tag types for reference
COMMON_TAG_TYPES = {
    "ua": "Universal Analytics (ua)",
    "ga4": "Google Analytics 4 (googtag)",
    "awct": "Google Ads Conversion Tracking (awct)",
    "html": "Custom HTML (html)",
    "img": "Custom Image (img)",
    "floodlight_counter": "Floodlight Counter (flc)",
    "floodlight_sales": "Floodlight Sales (fls)",
}


def list_tags(service, account_id: str, container_id: str,
              workspace_id: str) -> list[dict]:
    """List all tags in a workspace."""
    if not all([account_id, container_id, workspace_id]):
        raise ValueError("account_id, container_id, and workspace_id are required.")
    try:
        return backend.list_tags(service, str(account_id), str(container_id),
                                 str(workspace_id))
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))


def get_tag(service, account_id: str, container_id: str,
            workspace_id: str, tag_id: str) -> dict:
    """Get a specific tag."""
    if not all([account_id, container_id, workspace_id, tag_id]):
        raise ValueError("account_id, container_id, workspace_id, and tag_id are required.")
    try:
        return backend.get_tag(service, str(account_id), str(container_id),
                               str(workspace_id), str(tag_id))
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))


def create_tag(service, account_id: str, container_id: str,
               workspace_id: str, name: str, tag_type: str,
               parameters: list = None, firing_trigger_ids: list = None,
               blocking_trigger_ids: list = None,
               tag_firing_option: str = "oncePerEvent") -> dict:
    """Create a new tag in a workspace.

    Args:
        name: Display name for the tag.
        tag_type: GTM tag type (e.g., 'ua', 'html', 'googtag').
        parameters: List of parameter dicts, e.g. [{"type": "template", "key": "trackingId", "value": "UA-..."}].
        firing_trigger_ids: List of trigger IDs that fire this tag.
        blocking_trigger_ids: List of trigger IDs that block this tag.
        tag_firing_option: 'oncePerEvent', 'oncePerLoad', or 'unlimited'.
    """
    if not all([account_id, container_id, workspace_id]):
        raise ValueError("account_id, container_id, and workspace_id are required.")
    if not name or not name.strip():
        raise ValueError("Tag name cannot be empty.")
    if not tag_type or not tag_type.strip():
        raise ValueError("tag_type cannot be empty.")

    valid_firing_options = {"oncePerEvent", "oncePerLoad", "unlimited"}
    if tag_firing_option not in valid_firing_options:
        raise ValueError(
            f"tag_firing_option must be one of {valid_firing_options}, "
            f"got '{tag_firing_option}'."
        )

    try:
        return backend.create_tag(
            service, str(account_id), str(container_id), str(workspace_id),
            name.strip(), tag_type.strip(),
            parameters=parameters,
            firing_trigger_ids=firing_trigger_ids,
            blocking_trigger_ids=blocking_trigger_ids,
            tag_firing_option=tag_firing_option,
        )
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))


def update_tag(service, account_id: str, container_id: str,
               workspace_id: str, tag_id: str,
               name: str = None, parameters: list = None,
               firing_trigger_ids: list = None) -> dict:
    """Update an existing tag."""
    if not all([account_id, container_id, workspace_id, tag_id]):
        raise ValueError("account_id, container_id, workspace_id, and tag_id are required.")

    try:
        current = backend.get_tag(service, str(account_id), str(container_id),
                                   str(workspace_id), str(tag_id))
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))

    body = dict(current)
    if name is not None:
        body["name"] = name.strip()
    if parameters is not None:
        body["parameter"] = parameters
    if firing_trigger_ids is not None:
        body["firingTriggerId"] = firing_trigger_ids

    try:
        return backend.update_tag(service, str(account_id), str(container_id),
                                   str(workspace_id), str(tag_id), body)
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))


def delete_tag(service, account_id: str, container_id: str,
               workspace_id: str, tag_id: str) -> dict:
    """Delete a tag."""
    if not all([account_id, container_id, workspace_id, tag_id]):
        raise ValueError("account_id, container_id, workspace_id, and tag_id are required.")
    try:
        backend.delete_tag(service, str(account_id), str(container_id),
                           str(workspace_id), str(tag_id))
        return {"deleted": True, "tag_id": tag_id}
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))


def revert_tag(service, account_id: str, container_id: str,
               workspace_id: str, tag_id: str) -> dict:
    """Revert changes to a tag."""
    if not all([account_id, container_id, workspace_id, tag_id]):
        raise ValueError("account_id, container_id, workspace_id, and tag_id are required.")
    try:
        return backend.revert_tag(service, str(account_id), str(container_id),
                                   str(workspace_id), str(tag_id))
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))


def format_tag_row(tag: dict) -> list:
    """Format a tag dict into a table row."""
    triggers = ", ".join(tag.get("firingTriggerId", []))
    return [
        tag.get("tagId", ""),
        tag.get("name", ""),
        tag.get("type", ""),
        triggers[:30] if len(triggers) > 30 else triggers,
        tag.get("tagFiringOption", ""),
    ]
