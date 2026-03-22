"""Tag operations — list all tags in the vault with usage counts.

Note: open_file() was moved to core/ui.py to keep responsibilities separate.
"""

from cli_anything.obsidian.utils.obsidian_backend import api_get


def list_tags(base_url: str, api_key: str | None) -> list:
    """List all tags in the vault with their usage counts.

    Hierarchical tags (e.g., 'work/tasks') contribute counts to parent tags.
    Tag names are returned without the '#' prefix.

    Args:
        base_url: Obsidian server base URL.
        api_key: Bearer token.

    Returns:
        List of tag dicts: [{name, count}], sorted by count descending.
    """
    result = api_get(base_url, "/tags/", api_key=api_key, accept="application/json")
    # API returns {"tagCounts": {"tag": count, ...}} or {"tags": [...]}
    if isinstance(result, dict):
        # Handle tagCounts format: {"tagCounts": {"tag-name": count}}
        if "tagCounts" in result:
            tags = [
                {"name": name, "count": count}
                for name, count in result["tagCounts"].items()
            ]
            return sorted(tags, key=lambda t: t["count"], reverse=True)
        # Handle tags list format
        if "tags" in result:
            return result["tags"]
    if isinstance(result, list):
        return result
    return []
