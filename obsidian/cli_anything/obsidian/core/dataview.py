"""Dataview plugin integration — run DQL queries with convenience wrappers.

The Obsidian Local REST API exposes Dataview queries via POST /search/
with Content-Type: application/vnd.olrapi.dataview.dql+txt.

This module provides higher-level functions that build DQL query strings
from structured parameters, as well as a raw passthrough.
"""

from cli_anything.obsidian.utils.obsidian_backend import api_post


def _to_list(result) -> list:
    """Normalise API response to a list."""
    if isinstance(result, list):
        return result
    if isinstance(result, dict):
        return result.get("results", [])
    return []


def raw(base_url: str, api_key: str | None, dql: str) -> list:
    """Execute a raw DQL query string.

    Args:
        base_url: Obsidian server base URL.
        api_key: Bearer token.
        dql: Complete DQL query (TABLE, LIST, TASK, or CALENDAR).

    Returns:
        List of result dicts.

    Raises:
        ValueError: If query is empty.
        RuntimeError: If Dataview plugin is not installed.
    """
    if not dql or not dql.strip():
        raise ValueError("DQL query cannot be empty.")
    result = api_post(
        base_url, "/search/",
        api_key=api_key,
        body=dql,
        content_type="application/vnd.olrapi.dataview.dql+txt",
        accept="application/json",
    )
    return _to_list(result)


def table(base_url: str, api_key: str | None,
          fields: str = "file.name",
          from_folder: str | None = None,
          where: str | None = None,
          sort: str | None = None,
          limit: int | None = None) -> list:
    """Run a Dataview TABLE query with structured parameters.

    Args:
        base_url: Obsidian server base URL.
        api_key: Bearer token.
        fields: Comma-separated list of fields (e.g., "file.name, status, date").
        from_folder: Optional source folder (e.g., '"Projects"' or '#tag').
        where: Optional WHERE clause (e.g., 'status = "rascunho"').
        sort: Optional SORT clause (e.g., 'file.mtime DESC').
        limit: Optional LIMIT for number of results.

    Returns:
        List of result dicts.
    """
    parts = [f"TABLE {fields}"]
    if from_folder:
        parts.append(f"FROM {from_folder}")
    if where:
        parts.append(f"WHERE {where}")
    if sort:
        parts.append(f"SORT {sort}")
    if limit:
        parts.append(f"LIMIT {limit}")
    dql = " ".join(parts)
    return raw(base_url, api_key, dql)


def list_query(base_url: str, api_key: str | None,
               expression: str | None = None,
               from_folder: str | None = None,
               where: str | None = None,
               sort: str | None = None,
               limit: int | None = None) -> list:
    """Run a Dataview LIST query.

    Args:
        base_url: Obsidian server base URL.
        api_key: Bearer token.
        expression: Optional expression to display (e.g., "file.name").
        from_folder: Optional source folder.
        where: Optional WHERE clause.
        sort: Optional SORT clause.
        limit: Optional LIMIT.

    Returns:
        List of result dicts.
    """
    parts = [f"LIST {expression}" if expression else "LIST"]
    if from_folder:
        parts.append(f"FROM {from_folder}")
    if where:
        parts.append(f"WHERE {where}")
    if sort:
        parts.append(f"SORT {sort}")
    if limit:
        parts.append(f"LIMIT {limit}")
    dql = " ".join(parts)
    return raw(base_url, api_key, dql)


def task(base_url: str, api_key: str | None,
         from_folder: str | None = None,
         where: str | None = None,
         sort: str | None = None,
         limit: int | None = None) -> list:
    """Run a Dataview TASK query.

    Args:
        base_url: Obsidian server base URL.
        api_key: Bearer token.
        from_folder: Optional source folder.
        where: Optional WHERE clause (e.g., '!completed').
        sort: Optional SORT clause.
        limit: Optional LIMIT.

    Returns:
        List of result dicts.
    """
    parts = ["TASK"]
    if from_folder:
        parts.append(f"FROM {from_folder}")
    if where:
        parts.append(f"WHERE {where}")
    if sort:
        parts.append(f"SORT {sort}")
    if limit:
        parts.append(f"LIMIT {limit}")
    dql = " ".join(parts)
    return raw(base_url, api_key, dql)


def calendar(base_url: str, api_key: str | None,
             date_field: str = "file.cday",
             from_folder: str | None = None,
             where: str | None = None) -> list:
    """Run a Dataview CALENDAR query.

    Args:
        base_url: Obsidian server base URL.
        api_key: Bearer token.
        date_field: Date field to use for calendar (default: file.cday).
        from_folder: Optional source folder.
        where: Optional WHERE clause.

    Returns:
        List of result dicts.
    """
    parts = [f"CALENDAR {date_field}"]
    if from_folder:
        parts.append(f"FROM {from_folder}")
    if where:
        parts.append(f"WHERE {where}")
    dql = " ".join(parts)
    return raw(base_url, api_key, dql)
