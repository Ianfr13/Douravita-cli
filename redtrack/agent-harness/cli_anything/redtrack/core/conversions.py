"""Conversion tracking for RedTrack.

Wraps the RedTrack /conversions REST API endpoints.
"""

from cli_anything.redtrack.utils.redtrack_backend import api_get, api_post

# Standard RedTrack conversion statuses
CONVERSION_STATUSES = ["approved", "pending", "declined", "fired"]

# Standard RedTrack conversion types
CONVERSION_TYPES = [
    "conversion",
    "lead",
    "sale",
    "install",
    "registration",
    "deposit",
    "custom",
]


def list_conversions(api_key: str, base_url: str,
                     date_from: str | None = None,
                     date_to: str | None = None,
                     campaign_id: str | None = None,
                     status: str | None = None) -> dict:
    """List conversions with optional filters.

    Args:
        api_key: RedTrack API key.
        base_url: API base URL.
        date_from: Start date filter (YYYY-MM-DD).
        date_to: End date filter (YYYY-MM-DD).
        campaign_id: Filter by campaign ID (optional).
        status: Filter by status e.g. 'approved', 'pending' (optional).

    Returns:
        API response with conversions list.
    """
    params: dict = {}
    if date_from:
        params["date_from"] = date_from
    if date_to:
        params["date_to"] = date_to
    if campaign_id:
        params["campaign_id"] = campaign_id
    if status:
        params["status"] = status
    return api_get("/conversions", params=params, api_key=api_key, base_url=base_url)


def upload_conversion(api_key: str, base_url: str, click_id: str,
                      status: str = "approved",
                      payout: float | None = None,
                      conversion_type: str | None = None) -> dict:
    """Manually upload/record a conversion.

    Args:
        api_key: RedTrack API key.
        base_url: API base URL.
        click_id: RedTrack click ID to associate the conversion with.
        status: Conversion status (approved, pending, declined).
        payout: Payout amount for this conversion.
        conversion_type: Type of conversion event.

    Returns:
        API response dict.
    """
    data: dict = {"click_id": click_id, "status": status}
    if payout is not None:
        data["payout"] = payout
    if conversion_type:
        data["type"] = conversion_type
    return api_post("/conversions", data=data, api_key=api_key, base_url=base_url)


def get_conversion_types() -> list[str]:
    """Return the list of known RedTrack conversion type names.

    Returns:
        List of conversion type name strings.
    """
    return CONVERSION_TYPES
