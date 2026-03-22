"""Obsidian command operations — list and execute Obsidian commands."""

from cli_anything.obsidian.utils.obsidian_backend import api_get, api_post


def list_commands(base_url: str, api_key: str | None) -> list:
    """List all available Obsidian commands.

    Args:
        base_url: Obsidian server base URL.
        api_key: Bearer token.

    Returns:
        List of command dicts: [{id, name}].
    """
    result = api_get(base_url, "/commands/", api_key=api_key, accept="application/json")
    if isinstance(result, list):
        return result
    if isinstance(result, dict):
        return result.get("commands", [])
    return []


def run_command(base_url: str, api_key: str | None, command_id: str) -> dict:
    """Execute an Obsidian command by its ID.

    Args:
        base_url: Obsidian server base URL.
        api_key: Bearer token.
        command_id: The command ID (e.g., 'editor:toggle-bold').

    Returns:
        Status dict (204 No Content → {'status': 'ok'}).

    Raises:
        RuntimeError: If the command is not found (404).
    """
    return api_post(
        base_url, f"/commands/{command_id}/",
        api_key=api_key,
        content_type="application/json",
        accept="application/json",
    )
