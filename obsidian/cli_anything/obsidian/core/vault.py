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
    stripped = path.strip("/") if path else ""
    if stripped:
        encoded = encode_path(stripped)
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


def exists(base_url: str, api_key: str | None, path: str) -> bool:
    """Check if a vault file exists without fetching its content.

    Uses a HEAD-like approach: requests minimal data (document map) and
    checks for a 404 error.

    Args:
        base_url: Obsidian server base URL.
        api_key: Bearer token.
        path: File path relative to vault root.

    Returns:
        True if the file exists, False otherwise.
    """
    try:
        get(base_url, api_key, path, fmt="map")
        return True
    except RuntimeError:
        return False


def move(base_url: str, api_key: str | None, src: str, dst: str) -> dict:
    """Move (rename) a vault file from src to dst.

    Implemented as get → put → delete since the API has no native move.

    Args:
        base_url: Obsidian server base URL.
        api_key: Bearer token.
        src: Current file path relative to vault root.
        dst: New file path relative to vault root.

    Returns:
        Status dict with 'src' and 'dst' keys.

    Raises:
        RuntimeError: If source doesn't exist or destination already exists.
    """
    content_result = get(base_url, api_key, src, fmt="markdown")
    content = content_result.get("content", "") if isinstance(content_result, dict) else str(content_result)

    if exists(base_url, api_key, dst):
        raise RuntimeError(f"Destination already exists: {dst}")

    put(base_url, api_key, dst, content)
    delete(base_url, api_key, src)
    return {"status": "ok", "src": src, "dst": dst}


def list_dir_recursive(base_url: str, api_key: str | None, path: str = "") -> list:
    """Recursively list all files under a vault directory.

    Args:
        base_url: Obsidian server base URL.
        api_key: Bearer token.
        path: Directory path relative to vault root (empty = vault root).

    Returns:
        Flat list of all file paths (directories are traversed, not listed).
    """
    result = list_dir(base_url, api_key, path)
    files_raw = result.get("files", result) if isinstance(result, dict) else result
    if not isinstance(files_raw, list):
        return []

    all_files = []
    for item in files_raw:
        if item.endswith("/"):
            sub_path = f"{path}/{item}".strip("/") if path else item.rstrip("/")
            all_files.extend(list_dir_recursive(base_url, api_key, sub_path))
        else:
            full = f"{path}/{item}".strip("/") if path else item
            all_files.append(full)
    return all_files


def get_heading(base_url: str, api_key: str | None, path: str,
                heading: str, delimiter: str = "::") -> dict:
    """Get the content under a specific heading in a vault file.

    Uses the PATCH-style API with a GET on the heading target.
    Falls back to fetching the full document and extracting the section.

    Args:
        base_url: Obsidian server base URL.
        api_key: Bearer token.
        path: File path relative to vault root.
        heading: Heading name (use delimiter for nested, e.g. 'Parent::Child').
        delimiter: Nested heading separator (default '::').

    Returns:
        Dict with 'content' key containing the section text.
    """
    encoded = encode_path(path)
    from urllib.parse import quote as url_quote
    target_encoded = url_quote(heading, safe="")
    params = {
        "heading": target_encoded,
        "delimiter": delimiter,
    }
    return api_get(
        base_url, f"/vault/{encoded}",
        api_key=api_key,
        accept="text/markdown",
        params=params,
    )
