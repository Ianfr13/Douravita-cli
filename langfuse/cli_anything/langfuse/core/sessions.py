"""Session operations for Langfuse CLI."""

from cli_anything.langfuse.utils.langfuse_backend import LangfuseClient


def list_sessions(
    client: LangfuseClient,
    page: int = 1,
    limit: int = 20,
    from_timestamp: str | None = None,
    to_timestamp: str | None = None,
) -> dict:
    """List sessions."""
    params = {"page": page, "limit": limit}
    if from_timestamp:
        params["fromTimestamp"] = from_timestamp
    if to_timestamp:
        params["toTimestamp"] = to_timestamp
    return client.get("/api/public/sessions", params=params)


def get_session(client: LangfuseClient, session_id: str) -> dict:
    """Get a session with its traces."""
    return client.get(f"/api/public/sessions/{session_id}")
