"""Prompt operations for Langfuse CLI."""

import json
from cli_anything.langfuse.utils.langfuse_backend import LangfuseClient


def list_prompts(
    client: LangfuseClient,
    page: int = 1,
    limit: int = 20,
    name: str | None = None,
    label: str | None = None,
    tag: str | None = None,
) -> dict:
    """List prompts."""
    params = {"page": page, "limit": limit}
    if name:
        params["name"] = name
    if label:
        params["label"] = label
    if tag:
        params["tag"] = tag
    return client.get("/api/public/v2/prompts", params=params)


def get_prompt(
    client: LangfuseClient,
    prompt_name: str,
    version: int | None = None,
    label: str | None = None,
) -> dict:
    """Get a prompt by name, optionally at a specific version or label."""
    params = {}
    if version is not None:
        params["version"] = version
    if label:
        params["label"] = label
    return client.get(f"/api/public/v2/prompts/{prompt_name}", params=params)


def create_prompt(
    client: LangfuseClient,
    name: str,
    prompt: str | list,
    prompt_type: str = "text",
    config: dict | None = None,
    labels: list[str] | None = None,
    tags: list[str] | None = None,
    commit_message: str | None = None,
) -> dict:
    """Create a new prompt version.

    Args:
        name: Prompt name.
        prompt: For type "text" — a string. For type "chat" — a list of message dicts.
        prompt_type: "text" or "chat".
        config: Optional config dict (e.g., model parameters).
        labels: Optional labels (e.g., ["production"]).
        tags: Optional tags.
        commit_message: Optional commit message for this version.
    """
    body: dict = {
        "name": name,
        "prompt": prompt,
        "type": prompt_type,
    }
    if config:
        body["config"] = config
    if labels:
        body["labels"] = labels
    if tags:
        body["tags"] = tags
    if commit_message:
        body["commitMessage"] = commit_message
    return client.post("/api/public/v2/prompts", body=body)
