"""Session management for cli-anything-redtrack.

Tracks API key (masked for display), base URL, and other session context.
"""

from cli_anything.redtrack.utils.redtrack_backend import DEFAULT_BASE_URL


def get_session_info(api_key: str | None, base_url: str = DEFAULT_BASE_URL) -> dict:
    """Return session status information.

    Args:
        api_key: Current API key (will be masked in output).
        base_url: Current API base URL.

    Returns:
        Dict with masked api_key, base_url, and other session details.
    """
    masked = _mask_key(api_key)
    return {
        "api_key": masked,
        "base_url": base_url,
        "authenticated": bool(api_key),
    }


def _mask_key(api_key: str | None) -> str:
    """Mask an API key for safe display.

    Shows the first 4 and last 4 characters, masking the rest with asterisks.

    Args:
        api_key: The API key to mask.

    Returns:
        Masked key string, or '(not set)' if key is empty/None.
    """
    if not api_key:
        return "(not set)"
    if len(api_key) <= 8:
        return "*" * len(api_key)
    return f"{api_key[:4]}{'*' * (len(api_key) - 8)}{api_key[-4:]}"
