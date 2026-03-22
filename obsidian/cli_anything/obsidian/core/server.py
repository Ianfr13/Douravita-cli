"""Obsidian server status — health check for the Local REST API plugin."""

from cli_anything.obsidian.utils.obsidian_backend import api_get


def status(base_url: str) -> dict:
    """Check if Obsidian REST API is running.

    No authentication required for GET /.

    Args:
        base_url: Obsidian server base URL.

    Returns:
        Dict with 'ok', 'service', 'authenticated', 'versions' keys.
    """
    return api_get(base_url, "/", api_key=None, accept="application/json")
