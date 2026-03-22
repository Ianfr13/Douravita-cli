"""Active file operations — read/write the currently open note in Obsidian."""

from cli_anything.obsidian.utils.obsidian_backend import (
    api_get, api_post, api_put, api_patch, api_delete, accept_for_format,
)


def get(base_url: str, api_key: str | None, fmt: str = "markdown") -> dict:
    """Get the content of the currently active (open) file.

    Args:
        base_url: Obsidian server base URL.
        api_key: Bearer token.
        fmt: Output format — 'markdown', 'json', or 'map'.

    Returns:
        Dict with 'content' key (markdown), or full NoteJson/DocumentMap.
    """
    accept = accept_for_format(fmt)
    return api_get(base_url, "/active/", api_key=api_key, accept=accept)


def append(base_url: str, api_key: str | None, content: str) -> dict:
    """Append markdown content to the active file.

    Args:
        base_url: Obsidian server base URL.
        api_key: Bearer token.
        content: Markdown text to append.

    Returns:
        Status dict.
    """
    return api_post(base_url, "/active/", api_key=api_key, body=content)


def put(base_url: str, api_key: str | None, content: str) -> dict:
    """Replace the entire content of the active file.

    Args:
        base_url: Obsidian server base URL.
        api_key: Bearer token.
        content: New markdown content.

    Returns:
        Status dict.
    """
    return api_put(base_url, "/active/", api_key=api_key, body=content)


def patch(base_url: str, api_key: str | None, content: str,
          operation: str, target_type: str, target: str,
          delimiter: str = "::", trim_whitespace: bool = False,
          create_if_missing: bool = False) -> dict:
    """Partially update the active file at a specific heading, block, or frontmatter key.

    Args:
        base_url: Obsidian server base URL.
        api_key: Bearer token.
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
    return api_patch(
        base_url, "/active/", api_key=api_key, body=content,
        operation=operation, target_type=target_type, target=target,
        delimiter=delimiter, trim_whitespace=trim_whitespace,
        create_if_missing=create_if_missing,
    )


def delete(base_url: str, api_key: str | None) -> dict:
    """Delete the currently active file.

    Args:
        base_url: Obsidian server base URL.
        api_key: Bearer token.

    Returns:
        Status dict.
    """
    return api_delete(base_url, "/active/", api_key=api_key)
