"""Container operations for GTM CLI."""
from googleapiclient.errors import HttpError
from cli_anything.google_tag_manager.utils import gtm_backend as backend

VALID_USAGE_CONTEXTS = {"web", "androidSdk5", "iosSdk5", "amp", "server"}

CONTAINER_TABLE_HEADERS = ["Container ID", "Name", "Public ID", "Usage Context"]


def list_containers(service, account_id: str) -> list[dict]:
    """List all containers in a GTM account."""
    if not account_id:
        raise ValueError("account_id is required.")
    try:
        return backend.list_containers(service, str(account_id))
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))


def get_container(service, account_id: str, container_id: str) -> dict:
    """Get a specific container."""
    if not account_id or not container_id:
        raise ValueError("account_id and container_id are required.")
    try:
        return backend.get_container(service, str(account_id), str(container_id))
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))


def create_container(service, account_id: str, name: str, usage_context: list,
                     domain_name: list = None, notes: str = "") -> dict:
    """Create a new container.

    Args:
        usage_context: List of contexts, e.g. ['web']. Valid: web, androidSdk5, iosSdk5, amp, server.
    """
    if not account_id:
        raise ValueError("account_id is required.")
    if not name or not name.strip():
        raise ValueError("Container name cannot be empty.")
    if not usage_context:
        raise ValueError("usage_context must contain at least one context.")

    invalid = set(usage_context) - VALID_USAGE_CONTEXTS
    if invalid:
        raise ValueError(
            f"Invalid usage_context values: {invalid}. "
            f"Valid values: {VALID_USAGE_CONTEXTS}"
        )

    try:
        return backend.create_container(
            service, str(account_id), name.strip(), usage_context,
            domain_name=domain_name, notes=notes
        )
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))


def update_container(service, account_id: str, container_id: str,
                     name: str = None, domain_name: list = None,
                     notes: str = None) -> dict:
    """Update a container's properties."""
    if not account_id or not container_id:
        raise ValueError("account_id and container_id are required.")

    try:
        current = backend.get_container(service, str(account_id), str(container_id))
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))

    body = dict(current)
    if name is not None:
        body["name"] = name.strip()
    if domain_name is not None:
        body["domainName"] = domain_name
    if notes is not None:
        body["notes"] = notes

    try:
        return backend.update_container(service, str(account_id), str(container_id), body)
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))


def delete_container(service, account_id: str, container_id: str) -> dict:
    """Delete a container."""
    if not account_id or not container_id:
        raise ValueError("account_id and container_id are required.")
    try:
        backend.delete_container(service, str(account_id), str(container_id))
        return {"deleted": True, "container_id": container_id}
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))


def get_snippet(service, account_id: str, container_id: str) -> dict:
    """Get the tagging snippet for a container."""
    if not account_id or not container_id:
        raise ValueError("account_id and container_id are required.")
    try:
        return backend.get_snippet(service, str(account_id), str(container_id))
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))


def format_container_row(c: dict) -> list:
    """Format a container dict into a table row."""
    ctx = ", ".join(c.get("usageContext", []))
    return [
        c.get("containerId", ""),
        c.get("name", ""),
        c.get("publicId", ""),
        ctx,
    ]
