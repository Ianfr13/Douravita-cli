"""Campaign CRUD and status management."""

from typing import Dict, List, Optional
from cli_anything.meta_ads.utils.meta_ads_backend import (
    api_get, api_post, api_delete, api_paginate, CAMPAIGN_FIELDS
)

VALID_OBJECTIVES = [
    "APP_INSTALLS", "BRAND_AWARENESS", "CONVERSIONS", "EVENT_RESPONSES",
    "LEAD_GENERATION", "LINK_CLICKS", "LOCAL_AWARENESS", "MESSAGES",
    "OUTCOME_APP_PROMOTION", "OUTCOME_AWARENESS", "OUTCOME_ENGAGEMENT",
    "OUTCOME_LEADS", "OUTCOME_SALES", "OUTCOME_TRAFFIC",
    "PAGE_LIKES", "POST_ENGAGEMENT", "REACH", "STORE_VISITS",
    "VIDEO_VIEWS",
]

VALID_STATUSES = ["ACTIVE", "PAUSED", "DELETED", "ARCHIVED"]


def list_campaigns(access_token: str, ad_account_id: str,
                   status_filter: str = None, limit: int = 50) -> List[Dict]:
    """List campaigns for an ad account."""
    params = {"fields": CAMPAIGN_FIELDS, "limit": limit}
    if status_filter:
        params["effective_status"] = [status_filter.upper()]
    return api_paginate(f"{ad_account_id}/campaigns", access_token, params)


def get_campaign(access_token: str, campaign_id: str) -> Dict:
    """Fetch a single campaign by ID."""
    return api_get(campaign_id, access_token, {"fields": CAMPAIGN_FIELDS})


def create_campaign(access_token: str, ad_account_id: str, name: str,
                    objective: str, status: str = "PAUSED",
                    daily_budget: int = None, lifetime_budget: int = None,
                    start_time: str = None, stop_time: str = None,
                    special_ad_categories: list = None) -> Dict:
    """Create a new campaign.

    Args:
        access_token: Meta access token.
        ad_account_id: Ad account ID (with act_ prefix).
        name: Campaign name.
        objective: Campaign objective (e.g., OUTCOME_TRAFFIC).
        status: Initial status — ACTIVE or PAUSED (default: PAUSED).
        daily_budget: Daily budget in account currency cents (e.g., 1000 = $10.00).
        lifetime_budget: Lifetime budget in cents (mutually exclusive with daily_budget).
        start_time: ISO 8601 start time (e.g., "2024-01-01T00:00:00+0000").
        stop_time: ISO 8601 stop time.
        special_ad_categories: List of special ad categories (default: []).

    Returns:
        Dict with "id" of created campaign.
    """
    payload = {
        "name": name,
        "objective": objective.upper(),
        "status": status.upper(),
        "special_ad_categories": special_ad_categories or [],
    }
    if daily_budget is not None:
        payload["daily_budget"] = str(daily_budget)
    if lifetime_budget is not None:
        payload["lifetime_budget"] = str(lifetime_budget)
    if start_time:
        payload["start_time"] = start_time
    if stop_time:
        payload["stop_time"] = stop_time
    return api_post(f"{ad_account_id}/campaigns", access_token, payload)


def update_campaign(access_token: str, campaign_id: str,
                    name: str = None, status: str = None,
                    daily_budget: int = None, lifetime_budget: int = None,
                    start_time: str = None, stop_time: str = None) -> Dict:
    """Update campaign fields. Only provided fields are changed."""
    payload = {}
    if name is not None:
        payload["name"] = name
    if status is not None:
        payload["status"] = status.upper()
    if daily_budget is not None:
        payload["daily_budget"] = str(daily_budget)
    if lifetime_budget is not None:
        payload["lifetime_budget"] = str(lifetime_budget)
    if start_time is not None:
        payload["start_time"] = start_time
    if stop_time is not None:
        payload["stop_time"] = stop_time
    if not payload:
        raise ValueError("No fields to update provided.")
    return api_post(campaign_id, access_token, payload)


def set_campaign_status(access_token: str, campaign_id: str, status: str) -> Dict:
    """Set campaign status to ACTIVE, PAUSED, DELETED, or ARCHIVED."""
    return api_post(campaign_id, access_token, {"status": status.upper()})


def delete_campaign(access_token: str, campaign_id: str) -> Dict:
    """Delete a campaign (sets status to DELETED)."""
    return api_delete(campaign_id, access_token)
