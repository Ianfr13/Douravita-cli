"""Score operations for Langfuse CLI."""

from cli_anything.langfuse.utils.langfuse_backend import LangfuseClient


def list_scores(
    client: LangfuseClient,
    page: int = 1,
    limit: int = 20,
    name: str | None = None,
    user_id: str | None = None,
    data_type: str | None = None,
    source: str | None = None,
    config_id: str | None = None,
) -> dict:
    """List scores with optional filters."""
    params = {
        "page": page,
        "limit": limit,
        "name": name,
        "userId": user_id,
        "dataType": data_type,
        "source": source,
        "configId": config_id,
    }
    return client.get("/api/public/scores", params=params)


def get_score(client: LangfuseClient, score_id: str) -> dict:
    """Get a single score by ID."""
    return client.get(f"/api/public/scores/{score_id}")


def create_score(
    client: LangfuseClient,
    trace_id: str,
    name: str,
    value: float | str | None = None,
    observation_id: str | None = None,
    data_type: str | None = None,
    comment: str | None = None,
    config_id: str | None = None,
    score_id: str | None = None,
) -> dict:
    """Create a score on a trace or observation."""
    body = {
        "traceId": trace_id,
        "name": name,
    }
    if value is not None:
        body["value"] = value
    if observation_id:
        body["observationId"] = observation_id
    if data_type:
        body["dataType"] = data_type
    if comment:
        body["comment"] = comment
    if config_id:
        body["configId"] = config_id
    if score_id:
        body["id"] = score_id
    return client.post("/api/public/scores", body=body)


def delete_score(client: LangfuseClient, score_id: str) -> dict:
    """Delete a score by ID."""
    return client.delete(f"/api/public/scores/{score_id}")


# Score Configs

def list_score_configs(
    client: LangfuseClient,
    page: int = 1,
    limit: int = 20,
) -> dict:
    """List score configurations."""
    return client.get("/api/public/score-configs", params={"page": page, "limit": limit})


def get_score_config(client: LangfuseClient, config_id: str) -> dict:
    """Get a score configuration by ID."""
    return client.get(f"/api/public/score-configs/{config_id}")


def create_score_config(
    client: LangfuseClient,
    name: str,
    data_type: str,
    min_value: float | None = None,
    max_value: float | None = None,
    categories: list[dict] | None = None,
    description: str | None = None,
) -> dict:
    """Create a score configuration."""
    body: dict = {"name": name, "dataType": data_type}
    if min_value is not None:
        body["minValue"] = min_value
    if max_value is not None:
        body["maxValue"] = max_value
    if categories:
        body["categories"] = categories
    if description:
        body["description"] = description
    return client.post("/api/public/score-configs", body=body)
