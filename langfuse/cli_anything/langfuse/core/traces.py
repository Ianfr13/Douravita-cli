"""Trace operations for Langfuse CLI."""

from cli_anything.langfuse.utils.langfuse_backend import LangfuseClient


def list_traces(
    client: LangfuseClient,
    page: int = 1,
    limit: int = 20,
    name: str | None = None,
    user_id: str | None = None,
    session_id: str | None = None,
    tags: list[str] | None = None,
    environment: str | None = None,
    from_timestamp: str | None = None,
    to_timestamp: str | None = None,
    version: str | None = None,
) -> dict:
    """List traces with optional filters."""
    params = {
        "page": page,
        "limit": limit,
        "name": name,
        "userId": user_id,
        "sessionId": session_id,
        "environment": environment,
        "fromTimestamp": from_timestamp,
        "toTimestamp": to_timestamp,
        "version": version,
    }
    if tags:
        params["tags"] = tags
    return client.get("/api/public/traces", params=params)


def get_trace(client: LangfuseClient, trace_id: str) -> dict:
    """Get a single trace by ID."""
    return client.get(f"/api/public/traces/{trace_id}")


def delete_trace(client: LangfuseClient, trace_id: str) -> dict:
    """Delete a trace by ID."""
    return client.delete(f"/api/public/traces/{trace_id}")
