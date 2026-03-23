"""Comment operations for Langfuse CLI."""

from cli_anything.langfuse.utils.langfuse_backend import LangfuseClient


def list_comments(
    client: LangfuseClient,
    page: int = 1,
    limit: int = 20,
    object_type: str | None = None,
    object_id: str | None = None,
    author_user_id: str | None = None,
) -> dict:
    """List comments."""
    params = {"page": page, "limit": limit}
    if object_type:
        params["objectType"] = object_type
    if object_id:
        params["objectId"] = object_id
    if author_user_id:
        params["authorUserId"] = author_user_id
    return client.get("/api/public/comments", params=params)


def get_comment(client: LangfuseClient, comment_id: str) -> dict:
    """Get a comment by ID."""
    return client.get(f"/api/public/comments/{comment_id}")


def create_comment(
    client: LangfuseClient,
    object_type: str,
    object_id: str,
    content: str,
    author_user_id: str | None = None,
) -> dict:
    """Create a comment on an object.

    Args:
        object_type: One of TRACE, OBSERVATION, SESSION, PROMPT.
        object_id: ID of the object to comment on.
        content: Comment content (markdown, max 5000 chars).
        author_user_id: Optional author user ID.
    """
    body: dict = {
        "objectType": object_type,
        "objectId": object_id,
        "content": content,
    }
    if author_user_id:
        body["authorUserId"] = author_user_id
    return client.post("/api/public/comments", body=body)
