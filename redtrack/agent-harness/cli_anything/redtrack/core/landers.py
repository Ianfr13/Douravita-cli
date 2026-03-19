"""Lander management for RedTrack.

Wraps the RedTrack /landers REST API endpoints.
"""

from cli_anything.redtrack.utils.redtrack_backend import (
    api_get, api_post, api_patch, api_delete
)


def list_landers(api_key: str, base_url: str) -> dict:
    """List all landers (landing pages).

    Args:
        api_key: RedTrack API key.
        base_url: API base URL.

    Returns:
        API response with landers list.
    """
    return api_get("/landers", api_key=api_key, base_url=base_url)


def get_lander(api_key: str, base_url: str, lander_id: str) -> dict:
    """Get a single lander by ID.

    Args:
        api_key: RedTrack API key.
        base_url: API base URL.
        lander_id: Lander identifier.

    Returns:
        Lander data dict.
    """
    return api_get(f"/landers/{lander_id}", api_key=api_key, base_url=base_url)


def create_lander(api_key: str, base_url: str, name: str,
                  url: str | None = None,
                  tracking_type: str | None = None) -> dict:
    """Create a new lander.

    Args:
        api_key: RedTrack API key.
        base_url: API base URL.
        name: Lander name.
        url: Landing page URL.
        tracking_type: Tracking type (e.g., 'redirect', 'direct').

    Returns:
        Created lander data dict.
    """
    data: dict = {"name": name}
    if url:
        data["url"] = url
    if tracking_type:
        data["tracking_type"] = tracking_type
    return api_post("/landers", data=data, api_key=api_key, base_url=base_url)


def update_lander(api_key: str, base_url: str, lander_id: str,
                  name: str | None = None, url: str | None = None,
                  tracking_type: str | None = None,
                  status: str | None = None) -> dict:
    """Update an existing lander.

    Args:
        api_key: RedTrack API key.
        base_url: API base URL.
        lander_id: Lander identifier.
        name: New name (optional).
        url: New URL (optional).
        tracking_type: New tracking type (optional).
        status: New status (optional).

    Returns:
        Updated lander data dict.
    """
    data: dict = {}
    if name is not None:
        data["name"] = name
    if url is not None:
        data["url"] = url
    if tracking_type is not None:
        data["tracking_type"] = tracking_type
    if status is not None:
        data["status"] = status
    return api_patch(f"/landers/{lander_id}", data=data,
                     api_key=api_key, base_url=base_url)


def delete_lander(api_key: str, base_url: str, lander_id: str) -> dict:
    """Delete a lander.

    Args:
        api_key: RedTrack API key.
        base_url: API base URL.
        lander_id: Lander identifier.

    Returns:
        Status dict.
    """
    return api_delete(f"/landers/{lander_id}", api_key=api_key, base_url=base_url)
