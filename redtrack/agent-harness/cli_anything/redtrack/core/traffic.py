"""Traffic channel management for RedTrack.

Wraps the RedTrack /sources REST API endpoints.
"""

from cli_anything.redtrack.utils.redtrack_backend import (
    api_get, api_post, api_patch, api_delete
)


def list_traffic_channels(api_key: str, base_url: str) -> dict:
    """List all traffic channels.

    Args:
        api_key: RedTrack API key.
        base_url: API base URL.

    Returns:
        API response with traffic channels list.
    """
    return api_get("/sources", api_key=api_key, base_url=base_url)


def get_traffic_channel(api_key: str, base_url: str, channel_id: str) -> dict:
    """Get a single traffic channel by ID.

    Args:
        api_key: RedTrack API key.
        base_url: API base URL.
        channel_id: Traffic channel identifier.

    Returns:
        Traffic channel data dict.
    """
    return api_get(f"/sources/{channel_id}",
                   api_key=api_key, base_url=base_url)


def create_traffic_channel(api_key: str, base_url: str, name: str,
                            template: str | None = None) -> dict:
    """Create a new traffic channel.

    Args:
        api_key: RedTrack API key.
        base_url: API base URL.
        name: Traffic channel name.
        template: Optional template name for pre-configured channel settings.

    Returns:
        Created traffic channel data dict.
    """
    data: dict = {"name": name}
    if template:
        data["template"] = template
    return api_post("/sources", data=data, api_key=api_key, base_url=base_url)


def update_traffic_channel(api_key: str, base_url: str, channel_id: str,
                            name: str | None = None,
                            status: str | None = None) -> dict:
    """Update an existing traffic channel.

    Args:
        api_key: RedTrack API key.
        base_url: API base URL.
        channel_id: Traffic channel identifier.
        name: New name (optional).
        status: New status (optional).

    Returns:
        Updated traffic channel data dict.
    """
    data: dict = {}
    if name is not None:
        data["name"] = name
    if status is not None:
        data["status"] = status
    return api_patch(f"/sources/{channel_id}", data=data,
                     api_key=api_key, base_url=base_url)


def delete_traffic_channel(api_key: str, base_url: str, channel_id: str) -> dict:
    """Delete a traffic channel.

    Args:
        api_key: RedTrack API key.
        base_url: API base URL.
        channel_id: Traffic channel identifier.

    Returns:
        Status dict.
    """
    return api_delete(f"/sources/{channel_id}",
                      api_key=api_key, base_url=base_url)
