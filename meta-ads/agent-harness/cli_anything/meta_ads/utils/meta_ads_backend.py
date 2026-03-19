"""Meta Ads Graph API backend.

Handles all HTTP communication with the Meta Graph API (v21.0).
All functions raise MetaAdsAPIError on API-level errors.
"""

import json
from typing import Any, Dict, List, Optional

import requests

GRAPH_API_VERSION = "v21.0"
GRAPH_BASE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

# Default fields fetched for each object type
CAMPAIGN_FIELDS = (
    "id,name,status,effective_status,objective,buying_type,"
    "daily_budget,lifetime_budget,budget_remaining,"
    "start_time,stop_time,created_time,updated_time"
)
ADSET_FIELDS = (
    "id,name,status,effective_status,campaign_id,"
    "daily_budget,lifetime_budget,budget_remaining,"
    "bid_amount,billing_event,optimization_goal,"
    "targeting,start_time,end_time,created_time,updated_time"
)
AD_FIELDS = (
    "id,name,status,effective_status,adset_id,campaign_id,"
    "creative{id,name},created_time,updated_time"
)
CREATIVE_FIELDS = (
    "id,name,status,body,title,image_url,thumbnail_url,"
    "object_type,created_time"
)
AUDIENCE_FIELDS = (
    "id,name,subtype,approximate_count,description,"
    "data_source,lookalike_spec,created_time,updated_time"
)
ACCOUNT_FIELDS = (
    "id,name,account_status,currency,timezone_name,"
    "amount_spent,balance,spend_cap,age,business"
)

DEFAULT_INSIGHTS_FIELDS = (
    "impressions,clicks,reach,spend,ctr,cpc,cpm,cpp,"
    "actions,action_values,cost_per_action_type,frequency"
)


class MetaAdsAPIError(Exception):
    """Raised when the Meta Graph API returns an error response."""

    def __init__(self, message: str, code: int = None, subcode: int = None,
                 error_type: str = None):
        super().__init__(message)
        self.code = code
        self.subcode = subcode
        self.error_type = error_type

    def __str__(self):
        parts = [super().__str__()]
        if self.code:
            parts.append(f"(code={self.code})")
        return " ".join(parts)


def _raise_if_error(data: dict) -> None:
    """Raise MetaAdsAPIError if response contains an error."""
    if "error" in data:
        err = data["error"]
        raise MetaAdsAPIError(
            err.get("message", "Unknown Meta API error"),
            code=err.get("code"),
            subcode=err.get("error_subcode"),
            error_type=err.get("type"),
        )


def api_get(endpoint: str, access_token: str, params: Dict = None) -> Dict:
    """Make a GET request to the Graph API.

    Args:
        endpoint: API endpoint path, e.g. "act_123/campaigns" or "123456789".
        access_token: Valid Meta access token.
        params: Additional query parameters.

    Returns:
        Parsed JSON response dict.

    Raises:
        MetaAdsAPIError: On API errors.
        requests.RequestException: On network errors.
    """
    url = f"{GRAPH_BASE_URL}/{endpoint.lstrip('/')}"
    p = {"access_token": access_token}
    if params:
        p.update({k: v for k, v in params.items() if v is not None})
    resp = requests.get(url, params=p, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    _raise_if_error(data)
    return data


def api_post(endpoint: str, access_token: str, payload: Dict = None) -> Dict:
    """Make a POST request to the Graph API.

    Args:
        endpoint: API endpoint path.
        access_token: Valid Meta access token.
        payload: Form data to POST.

    Returns:
        Parsed JSON response dict.

    Raises:
        MetaAdsAPIError: On API errors.
    """
    url = f"{GRAPH_BASE_URL}/{endpoint.lstrip('/')}"
    data = {"access_token": access_token}
    if payload:
        # Serialize dicts/lists to JSON strings (required by Graph API)
        for k, v in payload.items():
            if isinstance(v, (dict, list)):
                data[k] = json.dumps(v)
            elif v is not None:
                data[k] = v
    resp = requests.post(url, data=data, timeout=30)
    resp.raise_for_status()
    result = resp.json()
    _raise_if_error(result)
    return result


def api_delete(endpoint: str, access_token: str) -> Dict:
    """Make a DELETE request to the Graph API.

    Args:
        endpoint: API endpoint path.
        access_token: Valid Meta access token.

    Returns:
        Parsed JSON response dict (usually {"success": true}).

    Raises:
        MetaAdsAPIError: On API errors.
    """
    url = f"{GRAPH_BASE_URL}/{endpoint.lstrip('/')}"
    resp = requests.delete(url, params={"access_token": access_token}, timeout=30)
    resp.raise_for_status()
    result = resp.json()
    _raise_if_error(result)
    return result


def api_paginate(endpoint: str, access_token: str,
                 params: Dict = None, limit: int = 100) -> List[Dict]:
    """Fetch all pages from a cursor-paginated Graph API response.

    Args:
        endpoint: API endpoint path.
        access_token: Valid Meta access token.
        params: Additional query parameters.
        limit: Page size per request.

    Returns:
        Flattened list of all result objects.
    """
    p = dict(params or {})
    p.setdefault("limit", limit)
    data = api_get(endpoint, access_token, p)
    results = list(data.get("data", []))

    while True:
        paging = data.get("paging", {})
        cursors = paging.get("cursors", {})
        next_cursor = cursors.get("after") or paging.get("next")
        if not next_cursor or not paging.get("next"):
            break
        p["after"] = cursors.get("after", "")
        if not p["after"]:
            break
        data = api_get(endpoint, access_token, p)
        results.extend(data.get("data", []))

    return results


def validate_access_token(access_token: str) -> Dict:
    """Check token validity and return basic info.

    Args:
        access_token: Meta access token to validate.

    Returns:
        Dict with token info (user_id, app_id, scopes, etc.).

    Raises:
        MetaAdsAPIError: If token is invalid.
    """
    data = api_get("me", access_token, {"fields": "id,name"})
    return data


def normalize_account_id(account_id: str) -> str:
    """Ensure account ID has act_ prefix."""
    if not account_id.startswith("act_"):
        return f"act_{account_id}"
    return account_id
