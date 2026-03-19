"""Account-level operations for GTM CLI."""
from typing import Any
from googleapiclient.errors import HttpError
from cli_anything.google_tag_manager.utils import gtm_backend as backend


def list_accounts(service) -> list[dict]:
    """List all GTM accounts accessible to the authenticated user.

    Returns:
        List of account dicts with keys: accountId, name, shareData, path.
    """
    try:
        accounts = backend.list_accounts(service)
        return accounts
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))


def get_account(service, account_id: str) -> dict:
    """Get details for a specific GTM account.

    Args:
        account_id: The GTM account ID (numeric string).

    Returns:
        Account resource dict.
    """
    if not account_id or not str(account_id).strip():
        raise ValueError("account_id must be a non-empty string.")
    try:
        return backend.get_account(service, str(account_id))
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))


def update_account(service, account_id: str, name: str = None,
                   share_data: bool = None) -> dict:
    """Update a GTM account.

    Args:
        account_id: The GTM account ID.
        name: New display name for the account.
        share_data: Whether to share anonymized data with Google.

    Returns:
        Updated account resource dict.
    """
    if not account_id:
        raise ValueError("account_id is required.")

    # First fetch current values
    try:
        current = backend.get_account(service, str(account_id))
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))

    body = dict(current)
    if name is not None:
        body["name"] = name
    if share_data is not None:
        body["shareData"] = share_data

    try:
        return backend.update_account(service, str(account_id), body)
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))


def format_account_row(acct: dict) -> list:
    """Format an account dict into a table row."""
    return [
        acct.get("accountId", ""),
        acct.get("name", ""),
        str(acct.get("shareData", False)),
    ]


ACCOUNT_TABLE_HEADERS = ["Account ID", "Name", "Share Data"]
