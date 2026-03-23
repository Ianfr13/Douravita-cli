"""Metrics operations for Langfuse CLI."""

from cli_anything.langfuse.utils.langfuse_backend import LangfuseClient


def get_daily_metrics(
    client: LangfuseClient,
    page: int = 1,
    limit: int = 50,
    trace_name: str | None = None,
    user_id: str | None = None,
    tags: list[str] | None = None,
    environment: str | None = None,
    from_timestamp: str | None = None,
    to_timestamp: str | None = None,
) -> dict:
    """Get daily usage metrics."""
    params = {"page": page, "limit": limit}
    if trace_name:
        params["traceName"] = trace_name
    if user_id:
        params["userId"] = user_id
    if tags:
        params["tags"] = tags
    if environment:
        params["environment"] = environment
    if from_timestamp:
        params["fromTimestamp"] = from_timestamp
    if to_timestamp:
        params["toTimestamp"] = to_timestamp
    return client.get("/api/public/metrics/daily", params=params)
