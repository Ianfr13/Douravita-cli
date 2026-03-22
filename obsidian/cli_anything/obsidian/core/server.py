"""Obsidian server status — health check for the Local REST API plugin."""

from cli_anything.obsidian.utils.obsidian_backend import api_get


def status(base_url: str, api_key: str | None = None) -> dict:
    """Check if Obsidian REST API is running.

    GET / is public (no auth required), but sending a valid Bearer token
    lets the server confirm authentication in its response.

    Args:
        base_url: Obsidian server base URL.
        api_key: Optional Bearer token. When provided, the response
                 includes ``authenticated: true`` if the key is valid.

    Returns:
        Dict with 'status', 'service', 'authenticated', 'versions' keys.
    """
    return api_get(base_url, "/", api_key=api_key, accept="application/json")
