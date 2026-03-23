"""Dataset operations for Langfuse CLI."""

import json
from cli_anything.langfuse.utils.langfuse_backend import LangfuseClient


# ── Datasets ─────────────────────────────────────────────────────────

def list_datasets(
    client: LangfuseClient,
    page: int = 1,
    limit: int = 20,
) -> dict:
    """List datasets."""
    return client.get("/api/public/v2/datasets", params={"page": page, "limit": limit})


def get_dataset(client: LangfuseClient, dataset_name: str) -> dict:
    """Get a dataset by name."""
    return client.get(f"/api/public/v2/datasets/{dataset_name}")


def create_dataset(
    client: LangfuseClient,
    name: str,
    description: str | None = None,
    metadata: dict | None = None,
) -> dict:
    """Create a new dataset."""
    body: dict = {"name": name}
    if description:
        body["description"] = description
    if metadata:
        body["metadata"] = metadata
    return client.post("/api/public/v2/datasets", body=body)


# ── Dataset Items ────────────────────────────────────────────────────

def list_dataset_items(
    client: LangfuseClient,
    dataset_name: str,
    page: int = 1,
    limit: int = 20,
    source_trace_id: str | None = None,
    source_observation_id: str | None = None,
) -> dict:
    """List items in a dataset."""
    params = {
        "datasetName": dataset_name,
        "page": page,
        "limit": limit,
    }
    if source_trace_id:
        params["sourceTraceId"] = source_trace_id
    if source_observation_id:
        params["sourceObservationId"] = source_observation_id
    return client.get("/api/public/dataset-items", params=params)


def get_dataset_item(client: LangfuseClient, item_id: str) -> dict:
    """Get a dataset item by ID."""
    return client.get(f"/api/public/dataset-items/{item_id}")


def create_dataset_item(
    client: LangfuseClient,
    dataset_name: str,
    input_data: dict | str | list,
    expected_output: dict | str | list | None = None,
    metadata: dict | None = None,
    source_trace_id: str | None = None,
    source_observation_id: str | None = None,
    item_id: str | None = None,
    status: str | None = None,
) -> dict:
    """Create a dataset item."""
    body: dict = {
        "datasetName": dataset_name,
        "input": input_data,
    }
    if expected_output is not None:
        body["expectedOutput"] = expected_output
    if metadata:
        body["metadata"] = metadata
    if source_trace_id:
        body["sourceTraceId"] = source_trace_id
    if source_observation_id:
        body["sourceObservationId"] = source_observation_id
    if item_id:
        body["id"] = item_id
    if status:
        body["status"] = status
    return client.post("/api/public/dataset-items", body=body)


def delete_dataset_item(client: LangfuseClient, item_id: str) -> dict:
    """Delete a dataset item by ID."""
    return client.delete(f"/api/public/dataset-items/{item_id}")


# ── Dataset Runs ─────────────────────────────────────────────────────

def list_dataset_runs(
    client: LangfuseClient,
    dataset_name: str,
    page: int = 1,
    limit: int = 20,
) -> dict:
    """List runs for a dataset."""
    return client.get(
        f"/api/public/datasets/{dataset_name}/runs",
        params={"page": page, "limit": limit},
    )


def get_dataset_run(
    client: LangfuseClient,
    dataset_name: str,
    run_name: str,
) -> dict:
    """Get a dataset run by name."""
    return client.get(f"/api/public/datasets/{dataset_name}/runs/{run_name}")


def delete_dataset_run(
    client: LangfuseClient,
    dataset_name: str,
    run_name: str,
) -> dict:
    """Delete a dataset run."""
    return client.delete(f"/api/public/datasets/{dataset_name}/runs/{run_name}")
