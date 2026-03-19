"""Environment operations for GTM CLI."""
from googleapiclient.errors import HttpError
from cli_anything.google_tag_manager.utils import gtm_backend as backend

ENVIRONMENT_TABLE_HEADERS = ["Env ID", "Name", "Type", "URL", "Auth Code"]


def list_environments(service, account_id: str, container_id: str) -> list[dict]:
    """List all environments for a container."""
    if not account_id or not container_id:
        raise ValueError("account_id and container_id are required.")
    try:
        return backend.list_environments(service, str(account_id), str(container_id))
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))


def get_environment(service, account_id: str, container_id: str,
                    environment_id: str) -> dict:
    """Get a specific environment."""
    if not all([account_id, container_id, environment_id]):
        raise ValueError("account_id, container_id, and environment_id are required.")
    try:
        return backend.get_environment(service, str(account_id), str(container_id),
                                        str(environment_id))
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))


def create_environment(service, account_id: str, container_id: str,
                       name: str, env_type: str = "user",
                       description: str = "", url: str = "") -> dict:
    """Create a new environment.

    Args:
        env_type: 'live', 'latest', or 'user' (user-created environments).
    """
    if not account_id or not container_id:
        raise ValueError("account_id and container_id are required.")
    if not name or not name.strip():
        raise ValueError("Environment name cannot be empty.")

    valid_types = {"live", "latest", "user"}
    if env_type not in valid_types:
        raise ValueError(f"env_type must be one of {valid_types}, got '{env_type}'.")

    try:
        return backend.create_environment(
            service, str(account_id), str(container_id),
            name.strip(), env_type, description, url
        )
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))


def update_environment(service, account_id: str, container_id: str,
                       environment_id: str, name: str = None,
                       description: str = None, url: str = None) -> dict:
    """Update an environment."""
    if not all([account_id, container_id, environment_id]):
        raise ValueError("account_id, container_id, and environment_id are required.")

    try:
        current = backend.get_environment(service, str(account_id), str(container_id),
                                           str(environment_id))
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))

    body = dict(current)
    if name is not None:
        body["name"] = name.strip()
    if description is not None:
        body["description"] = description
    if url is not None:
        body["url"] = url

    try:
        return backend.update_environment(service, str(account_id), str(container_id),
                                           str(environment_id), body)
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))


def delete_environment(service, account_id: str, container_id: str,
                       environment_id: str) -> dict:
    """Delete an environment."""
    if not all([account_id, container_id, environment_id]):
        raise ValueError("account_id, container_id, and environment_id are required.")
    try:
        backend.delete_environment(service, str(account_id), str(container_id),
                                    str(environment_id))
        return {"deleted": True, "environment_id": environment_id}
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))


def reauthorize_environment(service, account_id: str, container_id: str,
                            environment_id: str) -> dict:
    """Reauthorize an environment (regenerate auth code)."""
    if not all([account_id, container_id, environment_id]):
        raise ValueError("account_id, container_id, and environment_id are required.")
    try:
        return backend.reauthorize_environment(service, str(account_id),
                                               str(container_id), str(environment_id))
    except HttpError as e:
        raise RuntimeError(backend.format_http_error(e))


def format_environment_row(env: dict) -> list:
    """Format an environment dict into a table row."""
    return [
        env.get("environmentId", ""),
        env.get("name", ""),
        env.get("type", ""),
        env.get("url", "")[:30],
        (env.get("authorizationCode", "") or "")[:16],
    ]
