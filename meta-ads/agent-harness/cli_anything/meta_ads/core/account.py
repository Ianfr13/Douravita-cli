"""Ad Account operations."""

from typing import Dict, List, Optional
from cli_anything.meta_ads.utils.meta_ads_backend import (
    api_get, api_paginate, ACCOUNT_FIELDS
)


def get_account_info(access_token: str, ad_account_id: str) -> Dict:
    """Fetch detailed info for a single ad account."""
    return api_get(ad_account_id, access_token, {"fields": ACCOUNT_FIELDS})


def list_ad_accounts(access_token: str) -> List[Dict]:
    """List all ad accounts accessible by the current token."""
    fields = "id,name,account_status,currency,timezone_name,amount_spent,business"
    return api_paginate("me/adaccounts", access_token, {"fields": fields})


def get_spending_summary(access_token: str, ad_account_id: str) -> Dict:
    """Return spend, balance and cap for the account."""
    fields = "id,name,amount_spent,balance,spend_cap,currency"
    data = api_get(ad_account_id, access_token, {"fields": fields})
    return {
        "id": data.get("id"),
        "name": data.get("name"),
        "currency": data.get("currency"),
        "amount_spent": data.get("amount_spent"),
        "balance": data.get("balance"),
        "spend_cap": data.get("spend_cap"),
    }


def list_pages(access_token: str) -> List[Dict]:
    """List Facebook Pages accessible to the current user."""
    fields = "id,name,category,fan_count,link"
    return api_paginate("me/accounts", access_token, {"fields": fields})
