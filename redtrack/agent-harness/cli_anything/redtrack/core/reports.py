"""Reporting for RedTrack.

Wraps the RedTrack /report REST API endpoint.
"""

from cli_anything.redtrack.utils.redtrack_backend import api_get


def general_report(api_key: str, base_url: str,
                   date_from: str | None = None,
                   date_to: str | None = None,
                   group_by: str | None = None,
                   filters: str | None = None) -> dict:
    """Get a general performance report.

    Args:
        api_key: RedTrack API key.
        base_url: API base URL.
        date_from: Start date (YYYY-MM-DD).
        date_to: End date (YYYY-MM-DD).
        group_by: Grouping field (e.g., 'campaign', 'offer', 'country').
        filters: JSON string or filter expression.

    Returns:
        Report data dict.
    """
    params: dict = {}
    if date_from:
        params["date_from"] = date_from
    if date_to:
        params["date_to"] = date_to
    if group_by:
        params["group_by"] = group_by
    if filters:
        params["filters"] = filters
    return api_get("/report", params=params, api_key=api_key, base_url=base_url)


def campaigns_report(api_key: str, base_url: str,
                     date_from: str | None = None,
                     date_to: str | None = None) -> dict:
    """Get a campaigns-specific performance report.

    Args:
        api_key: RedTrack API key.
        base_url: API base URL.
        date_from: Start date (YYYY-MM-DD).
        date_to: End date (YYYY-MM-DD).

    Returns:
        Campaigns report data dict.
    """
    params: dict = {"group_by": "campaign"}
    if date_from:
        params["date_from"] = date_from
    if date_to:
        params["date_to"] = date_to
    return api_get("/report", params=params,
                   api_key=api_key, base_url=base_url)


def click_logs(api_key: str, base_url: str,
               date_from: str | None = None,
               date_to: str | None = None,
               campaign_id: str | None = None) -> dict:
    """Get click logs via the /report endpoint grouped by click.

    Args:
        api_key: RedTrack API key.
        base_url: API base URL.
        date_from: Start date (YYYY-MM-DD).
        date_to: End date (YYYY-MM-DD).
        campaign_id: Filter by campaign ID (optional).

    Returns:
        Click log data dict.
    """
    params: dict = {"group_by": "click"}
    if date_from:
        params["date_from"] = date_from
    if date_to:
        params["date_to"] = date_to
    if campaign_id:
        params["campaign_id"] = campaign_id
    return api_get("/report", params=params, api_key=api_key, base_url=base_url)
