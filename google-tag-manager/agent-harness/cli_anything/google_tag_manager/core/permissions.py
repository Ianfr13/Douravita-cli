"""User permission operations for GTM CLI."""
from googleapiclient.errors import HttpError
from cli_anything.google_tag_manager.utils import gtm_backend as backend

PERMISSION_TABLE_HEADERS = ["Permission ID", "Email", "Account Access", "Containers"]

VALID_ACCOUNT_ACCESS = {"admin", "user", "noAccess"}
VALID_CONTAINER_ACCESS = {"publish", "approve", "edit", "read", "noAccess"}


def list_permissions(service, account_id: str) -> list[dict]:
    """List all user permissions for a GTM account."""
    if not account_id:
        raise ValueError("account_id is required.")
    try:
        return backend.list_permissions(service, str(account_id))
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))


def get_permission(service, account_id: str, user_permission_id: str) -> dict:
    """Get a specific user permission."""
    if not account_id or not user_permission_id:
        raise ValueError("account_id and user_permission_id are required.")
    try:
        return backend.get_permission(service, str(account_id), str(user_permission_id))
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))


def create_permission(service, account_id: str, email: str,
                      account_access: str = "user",
                      container_accesses: list = None) -> dict:
    """Grant permissions to a user.

    Args:
        email: User's Google account email.
        account_access: 'admin', 'user', or 'noAccess'.
        container_accesses: List of dicts with 'containerId' and 'permission' keys.
            e.g. [{"containerId": "123", "permission": "edit"}]
    """
    if not account_id:
        raise ValueError("account_id is required.")
    if not email or "@" not in email:
        raise ValueError(f"Invalid email address: '{email}'.")
    if account_access not in VALID_ACCOUNT_ACCESS:
        raise ValueError(
            f"account_access must be one of {VALID_ACCOUNT_ACCESS}, got '{account_access}'."
        )

    # Validate container accesses
    if container_accesses:
        for ca in container_accesses:
            if "containerId" not in ca:
                raise ValueError(f"Each container access must have a 'containerId' key: {ca}")
            if ca.get("permission") not in VALID_CONTAINER_ACCESS:
                raise ValueError(
                    f"container permission must be one of {VALID_CONTAINER_ACCESS}, "
                    f"got '{ca.get('permission')}'."
                )

    account_access_body = {"permission": account_access}

    try:
        return backend.create_permission(
            service, str(account_id), email,
            account_access=account_access_body,
            container_accesses=container_accesses,
        )
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))


def update_permission(service, account_id: str, user_permission_id: str,
                      account_access: str = None,
                      container_accesses: list = None) -> dict:
    """Update user permissions."""
    if not account_id or not user_permission_id:
        raise ValueError("account_id and user_permission_id are required.")

    try:
        current = backend.get_permission(service, str(account_id),
                                          str(user_permission_id))
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))

    body = dict(current)
    if account_access is not None:
        if account_access not in VALID_ACCOUNT_ACCESS:
            raise ValueError(
                f"account_access must be one of {VALID_ACCOUNT_ACCESS}."
            )
        body["accountAccess"] = {"permission": account_access}
    if container_accesses is not None:
        body["containerAccess"] = container_accesses

    try:
        return backend.update_permission(service, str(account_id),
                                          str(user_permission_id), body)
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))


def delete_permission(service, account_id: str, user_permission_id: str) -> dict:
    """Revoke (delete) a user's GTM permissions."""
    if not account_id or not user_permission_id:
        raise ValueError("account_id and user_permission_id are required.")
    try:
        backend.delete_permission(service, str(account_id), str(user_permission_id))
        return {"revoked": True, "user_permission_id": user_permission_id}
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))


def format_permission_row(perm: dict) -> list:
    """Format a user permission dict into a table row."""
    uid = perm.get("path", "").split("/")[-1]
    email = perm.get("emailAddress", "")
    acct_access = perm.get("accountAccess", {}).get("permission", "")
    containers = len(perm.get("containerAccess", []))
    return [uid, email, acct_access, f"{containers} containers"]
