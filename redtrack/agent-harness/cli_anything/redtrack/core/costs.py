"""Cost tracking for RedTrack.

Wraps the RedTrack /costs REST API endpoints.
"""

from cli_anything.redtrack.utils.redtrack_backend import api_get, api_post


def list_costs(api_key: str, base_url: str,
               date_from: str | None = None,
               date_to: str | None = None) -> dict:
    """List cost records.

    Args:
        api_key: RedTrack API key.
        base_url: API base URL.
        date_from: Start date filter (YYYY-MM-DD).
        date_to: End date filter (YYYY-MM-DD).

    Returns:
        API response with costs data.
    """
    params: dict = {}
    if date_from:
        params["date_from"] = date_from
    if date_to:
        params["date_to"] = date_to
    return api_get("/costs", params=params, api_key=api_key, base_url=base_url)


def update_cost(api_key: str, base_url: str, campaign_id: str,
                cost: float, date: str | None = None) -> dict:
    """Manually update cost for a campaign.

    Args:
        api_key: RedTrack API key.
        base_url: API base URL.
        campaign_id: Campaign identifier.
        cost: Cost amount to record.
        date: Date for the cost entry (YYYY-MM-DD), defaults to today.

    Returns:
        API response dict.
    """
    data: dict = {"campaign_id": campaign_id, "cost": cost}
    if date:
        data["date"] = date
    return api_post("/costs", data=data, api_key=api_key, base_url=base_url)


def get_auto_cost_status(api_key: str, base_url: str) -> dict:
    """Get auto-update cost status information.

    Retrieves information about automatic cost synchronization settings.

    Args:
        api_key: RedTrack API key.
        base_url: API base URL.

    Returns:
        Cost auto-update status dict.
    """
    return api_get("/costs/auto", api_key=api_key, base_url=base_url)
