"""Periodic note operations — daily, weekly, monthly, quarterly, yearly notes."""

from datetime import datetime

from cli_anything.obsidian.utils.obsidian_backend import (
    api_get, api_post, api_put, api_patch, api_delete, accept_for_format,
)

VALID_PERIODS = ("daily", "weekly", "monthly", "quarterly", "yearly")


def _endpoint(period: str, date: str | None = None) -> str:
    """Build the API endpoint for a periodic note.

    Args:
        period: One of 'daily', 'weekly', 'monthly', 'quarterly', 'yearly'.
        date: Optional ISO date string 'YYYY-MM-DD' for a specific note.
              If None, targets the current period note.

    Returns:
        API endpoint path string.

    Raises:
        ValueError: If period is not valid.
    """
    if period not in VALID_PERIODS:
        raise ValueError(
            f"Invalid period '{period}'. Must be one of: {', '.join(VALID_PERIODS)}"
        )
    if date:
        try:
            d = datetime.strptime(date, "%Y-%m-%d")
            return f"/periodic/{period}/{d.year}/{d.month}/{d.day}/"
        except ValueError:
            raise ValueError(f"Invalid date '{date}'. Use YYYY-MM-DD format.")
    return f"/periodic/{period}/"


def get(base_url: str, api_key: str | None, period: str,
        date: str | None = None, fmt: str = "markdown") -> dict:
    """Get the content of a periodic note.

    Args:
        base_url: Obsidian server base URL.
        api_key: Bearer token.
        period: 'daily', 'weekly', 'monthly', 'quarterly', or 'yearly'.
        date: Optional 'YYYY-MM-DD' for a specific note (default: current).
        fmt: Output format — 'markdown', 'json', or 'map'.

    Returns:
        Dict with 'content' key or full NoteJson.
    """
    accept = accept_for_format(fmt)
    return api_get(base_url, _endpoint(period, date), api_key=api_key, accept=accept)


def append(base_url: str, api_key: str | None, period: str,
           content: str, date: str | None = None) -> dict:
    """Append content to a periodic note (creates it if it doesn't exist).

    Args:
        base_url: Obsidian server base URL.
        api_key: Bearer token.
        period: Periodic note period.
        content: Markdown text to append.
        date: Optional 'YYYY-MM-DD' for a specific note.

    Returns:
        Status dict.
    """
    return api_post(base_url, _endpoint(period, date), api_key=api_key, body=content)


def put(base_url: str, api_key: str | None, period: str,
        content: str, date: str | None = None) -> dict:
    """Replace the content of a periodic note.

    Args:
        base_url: Obsidian server base URL.
        api_key: Bearer token.
        period: Periodic note period.
        content: New markdown content.
        date: Optional 'YYYY-MM-DD' for a specific note.

    Returns:
        Status dict.
    """
    return api_put(base_url, _endpoint(period, date), api_key=api_key, body=content)


def patch(base_url: str, api_key: str | None, period: str, content: str,
          operation: str, target_type: str, target: str,
          date: str | None = None, delimiter: str = "::",
          trim_whitespace: bool = False, create_if_missing: bool = False) -> dict:
    """Partially update a periodic note.

    Args:
        base_url: Obsidian server base URL.
        api_key: Bearer token.
        period: Periodic note period.
        content: Content to insert.
        operation: 'append', 'prepend', or 'replace'.
        target_type: 'heading', 'block', or 'frontmatter'.
        target: Section name, block ref, or frontmatter key.
        date: Optional 'YYYY-MM-DD' for a specific note.
        delimiter: Nested heading separator (default '::').
        trim_whitespace: Whether to trim target whitespace.
        create_if_missing: Create section if absent.

    Returns:
        Status dict.
    """
    return api_patch(
        base_url, _endpoint(period, date), api_key=api_key, body=content,
        operation=operation, target_type=target_type, target=target,
        delimiter=delimiter, trim_whitespace=trim_whitespace,
        create_if_missing=create_if_missing,
    )


def delete(base_url: str, api_key: str | None, period: str,
           date: str | None = None) -> dict:
    """Delete a periodic note.

    Args:
        base_url: Obsidian server base URL.
        api_key: Bearer token.
        period: Periodic note period.
        date: Optional 'YYYY-MM-DD' for a specific note.

    Returns:
        Status dict.
    """
    return api_delete(base_url, _endpoint(period, date), api_key=api_key)
