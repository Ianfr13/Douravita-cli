"""Ad CRUD and status management."""

from typing import Dict, List, Optional
from cli_anything.meta_ads.utils.meta_ads_backend import (
    api_get, api_post, api_delete, api_paginate, AD_FIELDS
)


def list_ads(access_token: str, ad_account_id: str,
             adset_id: str = None, campaign_id: str = None,
             status_filter: str = None, limit: int = 50) -> List[Dict]:
    params = {"fields": AD_FIELDS, "limit": limit}
    if adset_id:
        params["adset_id"] = adset_id
    if campaign_id:
        params["campaign_id"] = campaign_id
    if status_filter:
        params["effective_status"] = [status_filter.upper()]
    return api_paginate(f"{ad_account_id}/ads", access_token, params)


def get_ad(access_token: str, ad_id: str) -> Dict:
    return api_get(ad_id, access_token, {"fields": AD_FIELDS})


def create_ad(access_token: str, ad_account_id: str,
              name: str, adset_id: str, creative_id: str,
              status: str = "PAUSED",
              tracking_specs: list = None) -> Dict:
    """Create an ad.

    Args:
        name: Ad name.
        adset_id: Parent ad set ID.
        creative_id: ID of the ad creative to use.
        status: Initial status (default: PAUSED).
        tracking_specs: Optional list of tracking spec dicts.
    """
    payload = {
        "name": name,
        "adset_id": adset_id,
        "creative": {"creative_id": creative_id},
        "status": status.upper(),
    }
    if tracking_specs:
        payload["tracking_specs"] = tracking_specs
    return api_post(f"{ad_account_id}/ads", access_token, payload)


def update_ad(access_token: str, ad_id: str,
              name: str = None, status: str = None,
              creative_id: str = None) -> Dict:
    payload = {}
    if name:
        payload["name"] = name
    if status:
        payload["status"] = status.upper()
    if creative_id:
        payload["creative"] = {"creative_id": creative_id}
    if not payload:
        raise ValueError("No fields to update provided.")
    return api_post(ad_id, access_token, payload)


def set_ad_status(access_token: str, ad_id: str, status: str) -> Dict:
    return api_post(ad_id, access_token, {"status": status.upper()})


def delete_ad(access_token: str, ad_id: str) -> Dict:
    return api_delete(ad_id, access_token)
