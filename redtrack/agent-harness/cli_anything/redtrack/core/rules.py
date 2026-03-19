"""Automation rules management for RedTrack.

Wraps the RedTrack /rules REST API endpoints.
"""

from cli_anything.redtrack.utils.redtrack_backend import (
    api_get, api_post, api_patch, api_delete
)


def list_rules(api_key: str, base_url: str) -> dict:
    """List all automation rules.

    Args:
        api_key: RedTrack API key.
        base_url: API base URL.

    Returns:
        API response with rules list.
    """
    return api_get("/rules", api_key=api_key, base_url=base_url)


def get_rule(api_key: str, base_url: str, rule_id: str) -> dict:
    """Get a single automation rule by ID.

    Args:
        api_key: RedTrack API key.
        base_url: API base URL.
        rule_id: Rule identifier.

    Returns:
        Rule data dict.
    """
    return api_get(f"/rules/{rule_id}", api_key=api_key, base_url=base_url)


def create_rule(api_key: str, base_url: str, name: str,
                condition: str | None = None,
                action: str | None = None) -> dict:
    """Create a new automation rule.

    Args:
        api_key: RedTrack API key.
        base_url: API base URL.
        name: Rule name.
        condition: Rule condition expression (JSON string or condition descriptor).
        action: Rule action to take when condition is met.

    Returns:
        Created rule data dict.
    """
    data: dict = {"name": name}
    if condition:
        data["condition"] = condition
    if action:
        data["action"] = action
    return api_post("/rules", data=data, api_key=api_key, base_url=base_url)


def update_rule(api_key: str, base_url: str, rule_id: str,
                name: str | None = None,
                status: str | None = None,
                condition: str | None = None,
                action: str | None = None) -> dict:
    """Update an existing automation rule.

    Args:
        api_key: RedTrack API key.
        base_url: API base URL.
        rule_id: Rule identifier.
        name: New rule name (optional).
        status: New status — 'active' to enable, 'paused' to disable (optional).
        condition: New condition (optional).
        action: New action (optional).

    Returns:
        Updated rule data dict.
    """
    data: dict = {}
    if name is not None:
        data["name"] = name
    if status is not None:
        data["status"] = status
    if condition is not None:
        data["condition"] = condition
    if action is not None:
        data["action"] = action
    return api_patch(f"/rules/{rule_id}", data=data,
                     api_key=api_key, base_url=base_url)


def delete_rule(api_key: str, base_url: str, rule_id: str) -> dict:
    """Delete an automation rule.

    Args:
        api_key: RedTrack API key.
        base_url: API base URL.
        rule_id: Rule identifier.

    Returns:
        Status dict.
    """
    return api_delete(f"/rules/{rule_id}", api_key=api_key, base_url=base_url)
