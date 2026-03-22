"""Vault file and directory operations — read/write any file by path."""

from cli_anything.obsidian.utils.obsidian_backend import (
    api_get, api_post, api_put, api_patch, api_delete,
    accept_for_format, encode_path,
)


def list_dir(base_url: str, api_key: str | None, path: str = "") -> dict:
    """List the contents of a vault directory.

    Args:
        base_url: Obsidian server base URL.
        api_key: Bearer token.
        path: Directory path relative to vault root (empty = vault root).
              Must NOT include a leading slash.

    Returns:
        Dict with 'files' key containing list of file/directory names.
    """
    if path:
        encoded = encode_path(path.strip("/"))
        endpoint = f"/vault/{encoded}/"
    else:
        endpoint = "/vault/"
    return api_get(base_url, endpoint, api_key=api_key, accept="application/json")


def get(base_url: str, api_key: str | None, path: str,
        fmt: str = "markdown") -> dict:
    """Get the content of a vault file by path.

    Args:
        base_url: Obsidian server base URL.
        api_key: Bearer token.
        path: File path relative to vault root (e.g., 'Notes/My Note.md').
        fmt: Output format — 'markdown', 'json', or 'map'.

    Returns:
        Dict with 'content' key (markdown), or full NoteJson/DocumentMap.
    """
    encoded = encode_path(path)
    accept = accept_for_format(fmt)
    return api_get(base_url, f"/vault/{encoded}", api_key=api_key, accept=accept)


def append(base_url: str, api_key: str | None, path: str,
           content: str) -> dict:
    """Append markdown content to a vault file (creates if it doesn't exist).

    Args:
        base_url: Obsidian server base URL.
        api_key: Bearer token.
        path: File path relative to vault root.
        content: Markdown text to append.

    Returns:
        Status dict.
    """
    encoded = encode_path(path)
    return api_post(base_url, f"/vault/{encoded}", api_key=api_key, body=content)


def put(base_url: str, api_key: str | None, path: str, content: str) -> dict:
    """Create or replace a vault file with given content.

    Args:
        base_url: Obsidian server base URL.
        api_key: Bearer token.
        path: File path relative to vault root.
        content: New file content.

    Returns:
        Status dict.
    """
    encoded = encode_path(path)
    return api_put(base_url, f"/vault/{encoded}", api_key=api_key, body=content)


def patch(base_url: str, api_key: str | None, path: str, content: str,
          operation: str, target_type: str, target: str,
          delimiter: str = "::", trim_whitespace: bool = False,
          create_if_missing: bool = False) -> dict:
    """Partially update a vault file at a specific heading, block, or frontmatter key.

    Args:
        base_url: Obsidian server base URL.
        api_key: Bearer token.
        path: File path relative to vault root.
        content: Content to insert.
        operation: 'append', 'prepend', or 'replace'.
        target_type: 'heading', 'block', or 'frontmatter'.
        target: Section name, block reference (e.g. '^2d9b4a'), or frontmatter key.
        delimiter: Separator for nested headings, default '::'.
        trim_whitespace: Whether to trim target whitespace.
        create_if_missing: Create section if it doesn't exist.

    Returns:
        Status dict.
    """
    encoded = encode_path(path)
    return api_patch(
        base_url, f"/vault/{encoded}", api_key=api_key, body=content,
        operation=operation, target_type=target_type, target=target,
        delimiter=delimiter, trim_whitespace=trim_whitespace,
        create_if_missing=create_if_missing,
    )


def delete(base_url: str, api_key: str | None, path: str) -> dict:
    """Delete a vault file.

    Args:
        base_url: Obsidian server base URL.
        api_key: Bearer token.
        path: File path relative to vault root.

    Returns:
        Status dict.
    """
    encoded = encode_path(path)
    return api_delete(base_url, f"/vault/{encoded}", api_key=api_key)
