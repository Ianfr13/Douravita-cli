"""Model operations for Langfuse CLI."""

from cli_anything.langfuse.utils.langfuse_backend import LangfuseClient


def list_models(
    client: LangfuseClient,
    page: int = 1,
    limit: int = 20,
) -> dict:
    """List models."""
    return client.get("/api/public/models", params={"page": page, "limit": limit})


def get_model(client: LangfuseClient, model_id: str) -> dict:
    """Get a model by ID."""
    return client.get(f"/api/public/models/{model_id}")


def create_model(
    client: LangfuseClient,
    model_name: str,
    match_pattern: str,
    unit: str = "TOKENS",
    input_price: float | None = None,
    output_price: float | None = None,
    total_price: float | None = None,
    tokenizer_id: str | None = None,
    start_date: str | None = None,
) -> dict:
    """Create a custom model definition."""
    body: dict = {
        "modelName": model_name,
        "matchPattern": match_pattern,
        "unit": unit,
    }
    if input_price is not None:
        body["inputPrice"] = input_price
    if output_price is not None:
        body["outputPrice"] = output_price
    if total_price is not None:
        body["totalPrice"] = total_price
    if tokenizer_id:
        body["tokenizerId"] = tokenizer_id
    if start_date:
        body["startDate"] = start_date
    return client.post("/api/public/models", body=body)


def delete_model(client: LangfuseClient, model_id: str) -> dict:
    """Delete a model."""
    return client.delete(f"/api/public/models/{model_id}")
