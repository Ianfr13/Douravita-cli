"""Search operations — simple fuzzy search, Dataview DQL, and JsonLogic."""

import json
from cli_anything.obsidian.utils.obsidian_backend import api_post, api_get


def _to_list(result) -> list:
    """Normalise an API response to a list, handling all known response shapes.

    Args:
        result: Raw response from the backend (list, dict, or other).

    Returns:
        List of result items, or empty list on unexpected types.
    """
    if isinstance(result, list):
        return result
    if isinstance(result, dict):
        # /search/simple/ wraps results under "results" key in some versions
        return result.get("results", [])
    return []


def simple(base_url: str, api_key: str | None, query: str,
           context_length: int = 100) -> list:
    """Perform a simple full-text fuzzy search across the vault.

    Args:
        base_url: Obsidian server base URL.
        api_key: Bearer token.
        query: Search term. Must be a non-empty string.
        context_length: Characters of context around each match (default 100).

    Returns:
        List of match dicts: [{filename, matches: [{match, context}], score}].

    Raises:
        ValueError: If query is empty.
    """
    if not query or not query.strip():
        raise ValueError("Search query cannot be empty.")
    result = api_post(
        base_url, "/search/simple/",
        api_key=api_key,
        params={"query": query, "contextLength": context_length},
        content_type="application/json",
        accept="application/json",
    )
    return _to_list(result)


def dql(base_url: str, api_key: str | None, query: str) -> list:
    """Search with a Dataview DQL TABLE query.

    Requires the Dataview plugin to be installed in Obsidian.

    Args:
        base_url: Obsidian server base URL.
        api_key: Bearer token.
        query: Dataview DQL TABLE query string (e.g., 'TABLE file.name FROM "Notes"').
               Must be a non-empty string.

    Returns:
        List of result dicts: [{filename, result}].

    Raises:
        ValueError: If query is empty.
    """
    if not query or not query.strip():
        raise ValueError("DQL query cannot be empty.")
    result = api_post(
        base_url, "/search/",
        api_key=api_key,
        body=query,
        content_type="application/vnd.olrapi.dataview.dql+txt",
        accept="application/json",
    )
    return _to_list(result)


def jsonlogic(base_url: str, api_key: str | None, logic: dict | str) -> list:
    """Search with a JsonLogic expression.

    Supports standard JsonLogic operators plus Obsidian extensions:
    - 'glob': file glob pattern matching (e.g., '*.md')
    - 'regexp': regular expression matching

    Files are represented as NoteJson schema objects.

    Args:
        base_url: Obsidian server base URL.
        api_key: Bearer token.
        logic: JsonLogic dict or JSON string. Must be non-empty.

    Returns:
        List of result dicts: [{filename, result}].

    Raises:
        ValueError: If logic is empty or invalid JSON string.
    """
    if isinstance(logic, str):
        if not logic.strip():
            raise ValueError("JsonLogic expression cannot be empty.")
        try:
            logic = json.loads(logic)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON for JsonLogic query: {e}") from e

    if not logic:
        raise ValueError("JsonLogic expression cannot be an empty object.")

    result = api_post(
        base_url, "/search/",
        api_key=api_key,
        body=logic,
        content_type="application/vnd.olrapi.jsonlogic+json",
        accept="application/json",
    )
    return _to_list(result)
