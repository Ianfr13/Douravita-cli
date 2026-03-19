"""Campaign management for RedTrack.

Wraps the RedTrack /campaigns REST API endpoints.
"""

from cli_anything.redtrack.utils.redtrack_backend import (
    api_get, api_post, api_patch, api_put, api_delete
)


def list_campaigns(api_key: str, base_url: str, date_from: str | None = None,
                   date_to: str | None = None, page: int = 1,
                   per: int = 100) -> dict:
    """List campaigns with optional date range and pagination.

    Args:
        api_key: RedTrack API key.
        base_url: API base URL.
        date_from: Start date filter (YYYY-MM-DD).
        date_to: End date filter (YYYY-MM-DD).
        page: Page number (1-based).
        per: Number of results per page.

    Returns:
        API response with campaigns list.
    """
    params: dict = {"page": page, "per": per}
    if date_from:
        params["date_from"] = date_from
    if date_to:
        params["date_to"] = date_to
    return api_get("/campaigns", params=params, api_key=api_key, base_url=base_url)


def get_campaign(api_key: str, base_url: str, campaign_id: str) -> dict:
    """Get a single campaign by ID.

    Args:
        api_key: RedTrack API key.
        base_url: API base URL.
        campaign_id: Campaign identifier.

    Returns:
        Campaign data dict.
    """
    return api_get(f"/campaigns/{campaign_id}", api_key=api_key, base_url=base_url)


def create_campaign(api_key: str, base_url: str, name: str,
                    traffic_channel_id: str, domain: str | None = None,
                    cost_type: str | None = None,
                    cost_value: float | None = None) -> dict:
    """Create a new campaign.

    Args:
        api_key: RedTrack API key.
        base_url: API base URL.
        name: Campaign name.
        traffic_channel_id: ID of the traffic channel.
        domain: Custom tracking domain (optional).
        cost_type: Cost model type (e.g., 'cpc', 'cpm', 'cpa').
        cost_value: Cost value per unit.

    Returns:
        Created campaign data dict.
    """
    data: dict = {"name": name, "traffic_channel_id": traffic_channel_id}
    if domain:
        data["domain"] = domain
    if cost_type:
        data["cost_type"] = cost_type
    if cost_value is not None:
        data["cost_value"] = cost_value
    return api_post("/campaigns", data=data, api_key=api_key, base_url=base_url)


def update_campaign(api_key: str, base_url: str, campaign_id: str,
                    name: str | None = None, status: str | None = None,
                    cost_type: str | None = None,
                    cost_value: float | None = None) -> dict:
    """Update an existing campaign.

    Args:
        api_key: RedTrack API key.
        base_url: API base URL.
        campaign_id: Campaign identifier.
        name: New campaign name (optional).
        status: New status e.g. 'active', 'paused' (optional).
        cost_type: New cost type (optional).
        cost_value: New cost value (optional).

    Returns:
        Updated campaign data dict.
    """
    data: dict = {}
    if name is not None:
        data["name"] = name
    if status is not None:
        data["status"] = status
    if cost_type is not None:
        data["cost_type"] = cost_type
    if cost_value is not None:
        data["cost_value"] = cost_value
    return api_put(f"/campaigns/{campaign_id}", data=data,
                   api_key=api_key, base_url=base_url)


def update_campaign_statuses(api_key: str, base_url: str,
                              ids: list[str], status: str) -> dict:
    """Bulk update campaign statuses.

    Uses the dedicated PATCH /campaigns/status endpoint which accepts
    a list of campaign IDs and the new status.

    Args:
        api_key: RedTrack API key.
        base_url: API base URL.
        ids: List of campaign IDs to update.
        status: New status ('active', 'paused', 'archived').

    Returns:
        API response dict.
    """
    data = {"ids": ids, "status": status}
    return api_patch("/campaigns/status", data=data, api_key=api_key, base_url=base_url)


def list_campaigns_v2(api_key: str, base_url: str, date_from: str | None = None,
                      date_to: str | None = None, page: int = 1,
                      per: int = 100) -> dict:
    """List campaigns via the lighter v2 endpoint (no total_stat).

    Args:
        api_key: RedTrack API key.
        base_url: API base URL.
        date_from: Start date filter (YYYY-MM-DD).
        date_to: End date filter (YYYY-MM-DD).
        page: Page number (1-based).
        per: Number of results per page.

    Returns:
        API response with campaigns list.
    """
    params: dict = {"page": page, "per": per}
    if date_from:
        params["date_from"] = date_from
    if date_to:
        params["date_to"] = date_to
    return api_get("/campaigns/v2", params=params, api_key=api_key, base_url=base_url)


def get_campaign_links(api_key: str, base_url: str, campaign_id: str) -> dict:
    """Get tracking links for a campaign.

    Fetches campaign data and extracts tracking link information.

    Args:
        api_key: RedTrack API key.
        base_url: API base URL.
        campaign_id: Campaign identifier.

    Returns:
        Dict containing tracking link info extracted from campaign data.
    """
    campaign = get_campaign(api_key, base_url, campaign_id)
    # Extract link-related fields from the campaign response
    links = {}
    for key in ("url", "tracking_url", "links", "click_url", "postback_url",
                "domain", "campaign_url"):
        if key in campaign:
            links[key] = campaign[key]
    if not links:
        links["campaign"] = campaign
    return links
