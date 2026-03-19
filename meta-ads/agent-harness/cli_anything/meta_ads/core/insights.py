"""Performance insights and reporting."""

from typing import Dict, List, Optional
from cli_anything.meta_ads.utils.meta_ads_backend import (
    api_get, api_paginate, DEFAULT_INSIGHTS_FIELDS
)

DATE_PRESETS = [
    "today", "yesterday", "this_week_sun_today", "this_week_mon_today",
    "last_week_sun_sat", "last_week_mon_sun", "last_7d", "last_14d",
    "last_28d", "last_30d", "last_90d", "this_month", "last_month",
    "this_quarter", "last_quarter", "this_year", "last_year", "lifetime",
]

BREAKDOWN_OPTIONS = [
    "age", "gender", "country", "region", "dma", "impression_device",
    "placement", "platform_position", "publisher_platform",
    "device_platform", "product_id", "hourly_stats_aggregated_by_advertiser_time_zone",
]

LEVELS = ["account", "campaign", "adset", "ad"]


def get_insights(access_token: str, object_id: str,
                 fields: str = None, date_preset: str = "last_30d",
                 since: str = None, until: str = None,
                 breakdowns: List[str] = None,
                 level: str = None,
                 limit: int = 100) -> List[Dict]:
    """Fetch insights for any object (account, campaign, adset, or ad).

    Args:
        object_id: Account ID (act_XXX), campaign ID, ad set ID, or ad ID.
        fields: Comma-separated metric fields (default: standard set).
        date_preset: Predefined date range (e.g., "last_30d", "last_7d").
        since / until: ISO date strings for custom range (e.g., "2024-01-01").
        breakdowns: List of breakdown dimensions (e.g., ["age", "gender"]).
        level: Aggregation level: account | campaign | adset | ad.
        limit: Results per page.
    """
    params = {
        "fields": fields or DEFAULT_INSIGHTS_FIELDS,
        "limit": limit,
    }
    if since and until:
        params["time_range"] = {"since": since, "until": until}
    else:
        params["date_preset"] = date_preset
    if breakdowns:
        params["breakdowns"] = ",".join(breakdowns)
    if level:
        params["level"] = level.lower()
    return api_paginate(f"{object_id}/insights", access_token, params)


def get_account_insights(access_token: str, ad_account_id: str,
                         date_preset: str = "last_30d",
                         since: str = None, until: str = None,
                         fields: str = None,
                         breakdowns: List[str] = None) -> List[Dict]:
    return get_insights(access_token, ad_account_id, fields=fields,
                        date_preset=date_preset, since=since, until=until,
                        breakdowns=breakdowns, level="account")


def get_campaign_insights(access_token: str, campaign_id: str,
                           date_preset: str = "last_30d",
                           since: str = None, until: str = None,
                           fields: str = None,
                           breakdowns: List[str] = None) -> List[Dict]:
    return get_insights(access_token, campaign_id, fields=fields,
                        date_preset=date_preset, since=since, until=until,
                        breakdowns=breakdowns, level="campaign")


def get_adset_insights(access_token: str, adset_id: str,
                        date_preset: str = "last_30d",
                        since: str = None, until: str = None,
                        fields: str = None,
                        breakdowns: List[str] = None) -> List[Dict]:
    return get_insights(access_token, adset_id, fields=fields,
                        date_preset=date_preset, since=since, until=until,
                        breakdowns=breakdowns, level="adset")


def get_ad_insights(access_token: str, ad_id: str,
                     date_preset: str = "last_30d",
                     since: str = None, until: str = None,
                     fields: str = None,
                     breakdowns: List[str] = None) -> List[Dict]:
    return get_insights(access_token, ad_id, fields=fields,
                        date_preset=date_preset, since=since, until=until,
                        breakdowns=breakdowns, level="ad")
