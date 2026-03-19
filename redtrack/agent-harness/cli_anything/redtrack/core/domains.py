"""Domain management for RedTrack.

Wraps the RedTrack /domains REST API endpoints.
Confirmed working endpoints: GET, POST, PUT /{id}, DELETE /{id},
POST /regenerated_free_ssl/{id}.
"""

from cli_anything.redtrack.utils.redtrack_backend import (
    api_get, api_post, api_put, api_delete
)


def list_domains(api_key: str, base_url: str,
                 domain_type: str | None = None,
                 page: int = 1, per: int = 100) -> dict:
    """List all custom tracking domains.

    Args:
        api_key: RedTrack API key.
        base_url: API base URL.
        domain_type: Filter by domain type (optional).
        page: Page number.
        per: Results per page.

    Returns:
        Paginated response dict with {"items": [...], "total": N}.
    """
    params: dict = {"page": page, "per": per}
    if domain_type:
        params["type"] = domain_type
    return api_get("/domains", params=params, api_key=api_key, base_url=base_url)


def add_domain(api_key: str, base_url: str, domain: str,
               domain_type: str | None = None) -> dict:
    """Add a new custom tracking domain.

    Args:
        api_key: RedTrack API key.
        base_url: API base URL.
        domain: The domain name (e.g., 'track.example.com').
        domain_type: Domain type (optional).

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
    """Update an existing custom domain.

    Args:
        api_key: RedTrack API key.
        base_url: API base URL.
        domain_id: Domain identifier.
        domain: New domain name (optional).
        domain_type: New domain type (optional).

    Returns:
        Updated domain data dict.

    Raises:
        ValueError: If neither domain nor domain_type is provided.
    """
    data: dict = {}
    if domain is not None:
        data["domain"] = domain
    if domain_type is not None:
        data["type"] = domain_type
    if not data:
        raise ValueError(
            "At least one field must be provided: domain or domain_type."
        )
    return api_put(f"/domains/{domain_id}", data=data, api_key=api_key, base_url=base_url)


def delete_domain(api_key: str, base_url: str, domain_id: str) -> dict:
    """Delete a custom domain.

    Args:
        api_key: RedTrack API key.
        base_url: API base URL.
        domain_id: Domain identifier.

    Returns:
        Status dict.
    """
    return api_delete(f"/domains/{domain_id}", api_key=api_key, base_url=base_url)


def regenerate_ssl(api_key: str, base_url: str, domain_id: str) -> dict:
    """Regenerate the free SSL certificate for a domain.

    Args:
        api_key: RedTrack API key.
        base_url: API base URL.
        domain_id: Domain identifier.

    Returns:
        API response dict.
    """
    return api_post(f"/domains/regenerated_free_ssl/{domain_id}",
                    data=None, api_key=api_key, base_url=base_url)
