"""Offer and offer source management for RedTrack.

Wraps the RedTrack /offers and /offer_sources REST API endpoints.
"""

from cli_anything.redtrack.utils.redtrack_backend import (
    api_get, api_post, api_patch, api_delete
)


# ── Offers ────────────────────────────────────────────────────────────────


def list_offers(api_key: str, base_url: str) -> dict:
    """List all offers.

    Args:
        api_key: RedTrack API key.
        base_url: API base URL.

    Returns:
        API response with offers list.
    """
    return api_get("/offers", api_key=api_key, base_url=base_url)


def get_offer(api_key: str, base_url: str, offer_id: str) -> dict:
    """Get a single offer by ID.

    Args:
        api_key: RedTrack API key.
        base_url: API base URL.
        offer_id: Offer identifier.

    Returns:
        Offer data dict.
    """
    return api_get(f"/offers/{offer_id}", api_key=api_key, base_url=base_url)


def create_offer(api_key: str, base_url: str, name: str,
                 offer_source_id: str | None = None, url: str | None = None,
                 payout: float | None = None) -> dict:
    """Create a new offer.

    Args:
        api_key: RedTrack API key.
        base_url: API base URL.
        name: Offer name.
        offer_source_id: ID of the affiliate network/offer source.
        url: Offer destination URL.
        payout: Default payout value.

    Returns:
        Created offer data dict.
    """
    data: dict = {"name": name}
    if offer_source_id:
        data["offer_source_id"] = offer_source_id
    if url:
        data["url"] = url
    if payout is not None:
        data["payout"] = payout
    return api_post("/offers", data=data, api_key=api_key, base_url=base_url)


def update_offer(api_key: str, base_url: str, offer_id: str,
                 name: str | None = None, url: str | None = None,
                 payout: float | None = None,
                 status: str | None = None) -> dict:
    """Update an existing offer.

    Args:
        api_key: RedTrack API key.
        base_url: API base URL.
        offer_id: Offer identifier.
        name: New offer name (optional).
        url: New offer URL (optional).
        payout: New payout value (optional).
        status: New status (optional).

    Returns:
        Updated offer data dict.
    """
    data: dict = {}
    if name is not None:
        data["name"] = name
    if url is not None:
        data["url"] = url
    if payout is not None:
        data["payout"] = payout
    if status is not None:
        data["status"] = status
    return api_patch(f"/offers/{offer_id}", data=data,
                     api_key=api_key, base_url=base_url)


def delete_offer(api_key: str, base_url: str, offer_id: str) -> dict:
    """Delete an offer.

    Args:
        api_key: RedTrack API key.
        base_url: API base URL.
        offer_id: Offer identifier.

    Returns:
        Status dict.
    """
    return api_delete(f"/offers/{offer_id}", api_key=api_key, base_url=base_url)


# ── Offer Sources (Affiliate Networks) ────────────────────────────────────


def list_offer_sources(api_key: str, base_url: str) -> dict:
    """List all offer sources (affiliate networks).

    Args:
        api_key: RedTrack API key.
        base_url: API base URL.

    Returns:
        API response with offer sources list.
    """
    return api_get("/offer_sources", api_key=api_key, base_url=base_url)


def get_offer_source(api_key: str, base_url: str, source_id: str) -> dict:
    """Get a single offer source by ID.

    Args:
        api_key: RedTrack API key.
        base_url: API base URL.
        source_id: Offer source identifier.

    Returns:
        Offer source data dict.
    """
    return api_get(f"/offer_sources/{source_id}", api_key=api_key, base_url=base_url)


def create_offer_source(api_key: str, base_url: str, name: str,
                        postback_url: str | None = None,
                        click_id_param: str | None = None,
                        payout_param: str | None = None) -> dict:
    """Create a new offer source (affiliate network).

    Args:
        api_key: RedTrack API key.
        base_url: API base URL.
        name: Offer source name.
        postback_url: Postback URL template for conversion tracking.
        click_id_param: Name of click ID parameter in postback.
        payout_param: Name of payout parameter in postback.

    Returns:
        Created offer source data dict.
    """
    data: dict = {"name": name}
    if postback_url:
        data["postback_url"] = postback_url
    if click_id_param:
        data["click_id_param"] = click_id_param
    if payout_param:
        data["payout_param"] = payout_param
    return api_post("/offer_sources", data=data, api_key=api_key, base_url=base_url)


def update_offer_source(api_key: str, base_url: str, source_id: str,
                        name: str | None = None,
                        postback_url: str | None = None,
                        click_id_param: str | None = None,
                        payout_param: str | None = None) -> dict:
    """Update an existing offer source.

    Args:
        api_key: RedTrack API key.
        base_url: API base URL.
        source_id: Offer source identifier.
        name: New name (optional).
        postback_url: New postback URL (optional).
        click_id_param: New click ID param name (optional).
        payout_param: New payout param name (optional).

    Returns:
        Updated offer source data dict.
    """
    data: dict = {}
    if name is not None:
        data["name"] = name
    if postback_url is not None:
        data["postback_url"] = postback_url
    if click_id_param is not None:
        data["click_id_param"] = click_id_param
    if payout_param is not None:
        data["payout_param"] = payout_param
    return api_patch(f"/offer_sources/{source_id}", data=data,
                     api_key=api_key, base_url=base_url)


def delete_offer_source(api_key: str, base_url: str, source_id: str) -> dict:
    """Delete an offer source.

    Args:
        api_key: RedTrack API key.
        base_url: API base URL.
        source_id: Offer source identifier.

    Returns:
        Status dict.
    """
    return api_delete(f"/offer_sources/{source_id}", api_key=api_key, base_url=base_url)
