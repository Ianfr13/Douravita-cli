"""Version header operations for GTM CLI."""
from googleapiclient.errors import HttpError
from cli_anything.google_tag_manager.utils import gtm_backend as backend

VERSION_TABLE_HEADERS = ["Version", "Name", "Deleted", "Published", "Fingerprint"]


def list_version_headers(service, account_id: str, container_id: str,
                         include_deleted: bool = False) -> list[dict]:
    """List all version headers for a container."""
    if not account_id or not container_id:
        raise ValueError("account_id and container_id are required.")
    try:
        return backend.list_version_headers(
            service, str(account_id), str(container_id),
            include_deleted=include_deleted
        )
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))


def latest_version_header(service, account_id: str, container_id: str) -> dict:
    """Get the latest published version header."""
    if not account_id or not container_id:
        raise ValueError("account_id and container_id are required.")
    try:
        return backend.latest_version_header(service, str(account_id), str(container_id))
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))


def format_version_row(vh: dict) -> list:
    """Format a version header dict into a table row."""
    return [
        vh.get("containerVersionId", ""),
        vh.get("name", ""),
        str(vh.get("deleted", False)),
        str(vh.get("numMacros", "")) + " vars",
        (vh.get("fingerprint", "") or "")[:12],
    ]
