"""Cost information for RedTrack.

NOTE: The /costs REST endpoint does not exist in the RedTrack API (confirmed 404).
Cost data in RedTrack is embedded within campaign/report data.
To access cost metrics, use the reports module with appropriate group_by fields.

The update_cost function is kept for compatibility but currently has no
direct API endpoint — cost updates happen through traffic source integrations
or manual entry in the RedTrack dashboard.
"""

from cli_anything.redtrack.utils.redtrack_backend import api_get


def get_cost_from_report(api_key: str, base_url: str,
                         date_from: str | None = None,
                         date_to: str | None = None,
                         campaign_id: str | None = None) -> dict:
    """Get cost data via the /report endpoint (grouped by campaign).

    Since RedTrack does not have a dedicated /costs endpoint, cost metrics
    (cost, cpc, roi, etc.) are available through the standard report endpoint.

    Args:
        api_key: RedTrack API key.
        base_url: API base URL.
        date_from: Start date filter (YYYY-MM-DD).
        date_to: End date filter (YYYY-MM-DD).
        campaign_id: Filter by campaign ID (optional).

    Returns:
        Report data dict containing cost metrics per campaign.
    """
    params: dict = {"group_by": "campaign"}
    if date_from:
        params["date_from"] = date_from
    if date_to:
        params["date_to"] = date_to
    if campaign_id:
        params["campaign_id"] = campaign_id
    return api_get("/report", params=params, api_key=api_key, base_url=base_url)
