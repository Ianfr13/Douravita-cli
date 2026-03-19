"""Custom and Lookalike Audience management."""

from typing import Dict, List, Optional
from cli_anything.meta_ads.utils.meta_ads_backend import (
    api_get, api_post, api_delete, api_paginate, AUDIENCE_FIELDS
)

CUSTOM_AUDIENCE_SUBTYPES = [
    "CUSTOM", "WEBSITE", "APP", "OFFLINE_CONVERSION",
    "CLAIM", "PARTNER", "MANAGED", "VIDEO", "LOOKALIKE",
    "ENGAGEMENT", "DATA_SET", "BAG_OF_ACCOUNTS", "STUDY_RULE_AUDIENCE",
    "FOX",
]


def list_audiences(access_token: str, ad_account_id: str,
                   limit: int = 50) -> List[Dict]:
    return api_paginate(f"{ad_account_id}/customaudiences", access_token,
                        {"fields": AUDIENCE_FIELDS, "limit": limit})


def get_audience(access_token: str, audience_id: str) -> Dict:
    return api_get(audience_id, access_token, {"fields": AUDIENCE_FIELDS})


def create_custom_audience(access_token: str, ad_account_id: str,
                           name: str, subtype: str = "CUSTOM",
                           description: str = None,
                           customer_file_source: str = "USER_PROVIDED_ONLY") -> Dict:
    """Create a custom audience (empty — add users via the API separately).

    Args:
        subtype: Audience subtype — CUSTOM, WEBSITE, APP, etc.
        customer_file_source: USER_PROVIDED_ONLY, PARTNER_PROVIDED_ONLY, etc.
    """
    payload = {
        "name": name,
        "subtype": subtype.upper(),
        "customer_file_source": customer_file_source,
    }
    if description:
        payload["description"] = description
    return api_post(f"{ad_account_id}/customaudiences", access_token, payload)


def create_lookalike_audience(access_token: str, ad_account_id: str,
                              name: str, origin_audience_id: str,
                              country: str = "US",
                              ratio: float = 0.01,
                              description: str = None) -> Dict:
    """Create a lookalike audience from a source audience.

    Args:
        origin_audience_id: Source custom audience ID.
        country: Two-letter country code (e.g., "US", "BR").
        ratio: Lookalike size ratio between 0.01 and 0.20 (1%–20%).
    """
    lookalike_spec = {
        "ratio": ratio,
        "country": country.upper(),
        "origin": [{"id": origin_audience_id, "type": "custom_audience"}],
    }
    payload = {
        "name": name,
        "subtype": "LOOKALIKE",
        "lookalike_spec": lookalike_spec,
    }
    if description:
        payload["description"] = description
    return api_post(f"{ad_account_id}/customaudiences", access_token, payload)


def delete_audience(access_token: str, audience_id: str) -> Dict:
    return api_delete(audience_id, access_token)


def get_audience_users_count(access_token: str, audience_id: str) -> Dict:
    """Fetch approximate user count and delivery estimate for an audience."""
    fields = "id,name,approximate_count,delivery_estimate"
    return api_get(audience_id, access_token, {"fields": fields})
