"""Custom domain management for RedTrack.

Wraps the RedTrack /domains REST API endpoints.
"""

from cli_anything.redtrack.utils.redtrack_backend import (
    api_get, api_post, api_put, api_delete
)


def list_domains(api_key: str, base_url: str,
                 domain_type: str | None = None,
                 page: int = 1, per: int = 100) -> dict:
    """List custom tracking domains.

    Args:
        api_key: RedTrack API key.
        base_url: API base URL.
        domain_type: Filter by domain type (optional).
        page: Page number (1-based).
        per: Results per page.

    Returns:
        API response with domains list.
    """
    params: dict = {"page": page, "per": per}
    if domain_type:
        params["type"] = domain_type
    return api_get("/domains", params=params, api_key=api_key, base_url=base_url)


def add_domain(api_key: str, base_url: str, domain: str,
               domain_type: str | None = None) -> dict:
    """Add a custom tracking domain.

    Args:
        api_key: RedTrack API key.
        base_url: API base URL.
        domain: Domain name to add.
        domain_type: Type of domain (optional).

    Returns:
        Created domain data dict.
    """
    data: dict = {"domain": domain}
    if domain_type:
        data["type"] = domain_type
    return api_post("/domains", data=data, api_key=api_key, base_url=base_url)


def update_domain(api_key: str, base_url: str, domain_id: str,
                  domain: str | None = None,
                  domain_type: str | None = None) -> dict:
    """Update a custom tracking domain.

    Args:
        api_key: RedTrack API key.
        base_url: API base URL.
        domain_id: Domain identifier.
        domain: New domain name (optional).
        domain_type: New domain type (optional).

    Returns:
        Updated domain data dict.
    """
    data: dict = {}
    if domain is not None:
        data["domain"] = domain
    if domain_type is not None:
        data["type"] = domain_type
    return api_put(f"/domains/{domain_id}", data=data, api_key=api_key, base_url=base_url)


def delete_domain(api_key: str, base_url: str, domain_id: str) -> dict:
    """Delete a custom tracking domain.

    Args:
        api_key: RedTrack API key.
        base_url: API base URL.
        domain_id: Domain identifier.

    Returns:
        Status dict.
    """
    result = api_delete(f"/domains/{domain_id}", api_key=api_key, base_url=base_url)
    if result is None:
        return {"status": "ok"}
    return result


def regenerate_ssl(api_key: str, base_url: str, domain_id: str) -> dict:
    """Regenerate the free SSL certificate for a domain.

    Args:
        api_key: RedTrack API key.
        base_url: API base URL.
        domain_id: Domain identifier.

    Returns:
        API response dict.
    """
    return api_post(f"/domains/regenerated_free_ssl/{domain_id}", data={},
                    api_key=api_key, base_url=base_url)
