"""Project operations for Langfuse CLI."""

from cli_anything.langfuse.utils.langfuse_backend import LangfuseClient


def get_projects(client: LangfuseClient) -> dict:
    """Get projects accessible with the current API key."""
    return client.get("/api/public/projects")


def get_health(client: LangfuseClient) -> dict:
    """Check Langfuse API health status."""
    return client.get("/api/public/health")
