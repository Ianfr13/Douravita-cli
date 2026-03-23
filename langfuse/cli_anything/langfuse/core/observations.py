"""Observation operations for Langfuse CLI."""

from cli_anything.langfuse.utils.langfuse_backend import LangfuseClient


def list_observations(
    client: LangfuseClient,
    page: int = 1,
    limit: int = 20,
    name: str | None = None,
    user_id: str | None = None,
    trace_id: str | None = None,
    obs_type: str | None = None,
    parent_observation_id: str | None = None,
    from_start_time: str | None = None,
    to_start_time: str | None = None,
    version: str | None = None,
) -> dict:
    """List observations with optional filters."""
    params = {
        "page": page,
        "limit": limit,
        "name": name,
        "userId": user_id,
        "traceId": trace_id,
        "type": obs_type,
        "parentObservationId": parent_observation_id,
        "fromStartTime": from_start_time,
        "toStartTime": to_start_time,
        "version": version,
    }
    return client.get("/api/public/observations", params=params)


def get_observation(client: LangfuseClient, observation_id: str) -> dict:
    """Get a single observation by ID."""
    return client.get(f"/api/public/observations/{observation_id}")
