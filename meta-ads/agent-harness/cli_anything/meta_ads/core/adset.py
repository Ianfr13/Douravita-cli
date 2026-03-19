"""Ad Set CRUD and status management."""

from typing import Dict, List, Optional
from cli_anything.meta_ads.utils.meta_ads_backend import (
    api_get, api_post, api_delete, api_paginate, ADSET_FIELDS
)

BILLING_EVENTS = ["APP_INSTALLS", "CLICKS", "IMPRESSIONS", "LINK_CLICKS",
                  "NONE", "OFFER_CLAIMS", "PAGE_LIKES", "POST_ENGAGEMENT",
                  "THRUPLAY", "PURCHASE", "LISTING_INTERACTION"]

OPTIMIZATION_GOALS = ["APP_INSTALLS", "BRAND_AWARENESS", "CLICKS",
                       "ENGAGED_USERS", "EVENT_RESPONSES", "IMPRESSIONS",
                       "LEAD_GENERATION", "LINK_CLICKS", "NONE",
                       "OFFSITE_CONVERSIONS", "PAGE_ENGAGEMENT", "PAGE_LIKES",
                       "POST_ENGAGEMENT", "QUALITY_CALL", "QUALITY_LEAD",
                       "REACH", "REPLIES", "SOCIAL_IMPRESSIONS",
                       "THRUPLAY", "VIDEO_VIEWS", "VISIT_INSTAGRAM_PROFILE"]


def list_adsets(access_token: str, ad_account_id: str,
                campaign_id: str = None, status_filter: str = None,
                limit: int = 50) -> List[Dict]:
    params = {"fields": ADSET_FIELDS, "limit": limit}
    if campaign_id:
        params["campaign_id"] = campaign_id
    if status_filter:
        params["effective_status"] = [status_filter.upper()]
    return api_paginate(f"{ad_account_id}/adsets", access_token, params)


def get_adset(access_token: str, adset_id: str) -> Dict:
    return api_get(adset_id, access_token, {"fields": ADSET_FIELDS})


def create_adset(access_token: str, ad_account_id: str,
                 name: str, campaign_id: str,
                 daily_budget: int = None, lifetime_budget: int = None,
                 bid_amount: int = None,
                 billing_event: str = "IMPRESSIONS",
                 optimization_goal: str = "REACH",
                 targeting: dict = None,
                 status: str = "PAUSED",
                 start_time: str = None, end_time: str = None) -> Dict:
    """Create an ad set.

    Args:
        daily_budget / lifetime_budget: In account currency cents.
        bid_amount: Bid in cents (optional, for manual bidding).
        billing_event: What you're charged for (IMPRESSIONS, CLICKS, etc.).
        optimization_goal: What to optimize for (REACH, LINK_CLICKS, etc.).
        targeting: Targeting spec dict (geo_locations, age_min, age_max, etc.).
        start_time / end_time: ISO 8601 datetime strings.
    """
    payload = {
        "name": name,
        "campaign_id": campaign_id,
        "billing_event": billing_event.upper(),
        "optimization_goal": optimization_goal.upper(),
        "status": status.upper(),
        "targeting": targeting or {"geo_locations": {"countries": ["US"]}},
    }
    if daily_budget is not None:
        payload["daily_budget"] = str(daily_budget)
    if lifetime_budget is not None:
        payload["lifetime_budget"] = str(lifetime_budget)
    if bid_amount is not None:
        payload["bid_amount"] = str(bid_amount)
    if start_time:
        payload["start_time"] = start_time
    if end_time:
        payload["end_time"] = end_time
    return api_post(f"{ad_account_id}/adsets", access_token, payload)


def update_adset(access_token: str, adset_id: str,
                 name: str = None, status: str = None,
                 daily_budget: int = None, lifetime_budget: int = None,
                 bid_amount: int = None, targeting: dict = None,
                 start_time: str = None, end_time: str = None) -> Dict:
    payload = {}
    if name:
        payload["name"] = name
    if status:
        payload["status"] = status.upper()
    if daily_budget is not None:
        payload["daily_budget"] = str(daily_budget)
    if lifetime_budget is not None:
        payload["lifetime_budget"] = str(lifetime_budget)
    if bid_amount is not None:
        payload["bid_amount"] = str(bid_amount)
    if targeting:
        payload["targeting"] = targeting
    if start_time:
        payload["start_time"] = start_time
    if end_time:
        payload["end_time"] = end_time
    if not payload:
        raise ValueError("No fields to update provided.")
    return api_post(adset_id, access_token, payload)


def set_adset_status(access_token: str, adset_id: str, status: str) -> Dict:
    return api_post(adset_id, access_token, {"status": status.upper()})


def delete_adset(access_token: str, adset_id: str) -> Dict:
    return api_delete(adset_id, access_token)
