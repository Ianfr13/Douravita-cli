"""Obsidian UI operations — open files in the Obsidian desktop app."""

from cli_anything.obsidian.utils.obsidian_backend import api_post, encode_path


def open_file(base_url: str, api_key: str | None, path: str,
              new_leaf: bool = False) -> dict:
    """Open a file in the Obsidian UI.

    Creates the file if it doesn't already exist in the vault.

    Args:
        base_url: Obsidian server base URL.
        api_key: Bearer token.
        path: File path relative to vault root (e.g., 'Notes/My Note.md').
        new_leaf: If True, open in a new tab/leaf (default: False).

    Returns:
        Status dict.
    """
    encoded = encode_path(path)
    params = {"newLeaf": "true"} if new_leaf else None
    return api_post(
        base_url, f"/open/{encoded}",
        api_key=api_key,
        content_type="application/json",
        accept="application/json",
        params=params,
    )
