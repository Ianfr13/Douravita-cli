"""Google Tag Manager API v2 backend wrapper.

This module wraps the GTM API v2 using google-api-python-client.
It handles authentication (service account and OAuth2) and provides
functions for all GTM API resources.

The GTM API is a HARD DEPENDENCY — this CLI is useless without it.
Install: pip install google-api-python-client google-auth google-auth-oauthlib
"""
import os
import json
from pathlib import Path
from typing import Optional, Any

# GTM API is a hard dependency — raise clear error if missing
try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from google.oauth2.service_account import Credentials as SACredentials
    from google.oauth2.credentials import Credentials as OAuthCredentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    import google.auth
    import google.auth.transport.requests
except ImportError as _e:
    raise RuntimeError(
        "Google API client libraries are not installed.\n"
        "Install them with:\n"
        "  pip install google-api-python-client google-auth google-auth-oauthlib google-auth-httplib2\n"
        f"Original error: {_e}"
    )

# ── Scopes ──────────────────────────────────────────────────────────

SCOPES_READONLY = ["https://www.googleapis.com/auth/tagmanager.readonly"]
SCOPES_EDIT = [
    "https://www.googleapis.com/auth/tagmanager.edit.containers",
    "https://www.googleapis.com/auth/tagmanager.edit.containerversions",
    "https://www.googleapis.com/auth/tagmanager.delete.containers",
    "https://www.googleapis.com/auth/tagmanager.publish",
    "https://www.googleapis.com/auth/tagmanager.manage.users",
    "https://www.googleapis.com/auth/tagmanager.manage.accounts",
]
SCOPES_ALL = SCOPES_READONLY + SCOPES_EDIT

# Default config directory
_CONFIG_DIR = Path.home() / ".config" / "cli-anything-gtm"
_DEFAULT_CREDS_FILE = _CONFIG_DIR / "credentials.json"
_TOKEN_FILE = _CONFIG_DIR / "token.json"


# ── Authentication ───────────────────────────────────────────────────

def find_credentials() -> Optional[str]:
    """Find credentials file from env or default location.

    Search order:
    1. GOOGLE_APPLICATION_CREDENTIALS env var
    2. GTM_CREDENTIALS_FILE env var
    3. ~/.config/cli-anything-gtm/credentials.json

    Returns:
        Path to credentials file, or None if not found.
    """
    # Check environment variables
    for env_var in ("GOOGLE_APPLICATION_CREDENTIALS", "GTM_CREDENTIALS_FILE"):
        val = os.environ.get(env_var, "").strip()
        if val and Path(val).is_file():
            return val

    # Check default config location
    if _DEFAULT_CREDS_FILE.is_file():
        return str(_DEFAULT_CREDS_FILE)

    return None


def _is_service_account(creds_data: dict) -> bool:
    """Determine if credentials JSON is a service account key."""
    return creds_data.get("type") == "service_account"


def _is_oauth_token(creds_data: dict) -> bool:
    """Determine if credentials JSON is a saved OAuth token."""
    return "token" in creds_data or "refresh_token" in creds_data


def get_gtm_service(
    credentials_file: Optional[str] = None,
    readonly: bool = False,
) -> Any:
    """Build and return the authenticated GTM API v2 service client.

    Credential search order:
    1. GOOGLE_APPLICATION_CREDENTIALS env var (service account)
    2. GTM_CREDENTIALS_FILE env var (service account or oauth token)
    3. credentials_file argument
    4. ~/.config/cli-anything-gtm/credentials.json
    5. Saved OAuth token at ~/.config/cli-anything-gtm/token.json

    Args:
        credentials_file: Explicit path to credentials JSON.
        readonly: If True, use read-only scopes only.

    Returns:
        Authenticated googleapiclient Resource for GTM API v2.

    Raises:
        RuntimeError: If no credentials are found or authentication fails.
    """
    scopes = SCOPES_READONLY if readonly else SCOPES_ALL
    creds = None

    # Try explicit file first
    cred_path = credentials_file or find_credentials()

    if cred_path:
        try:
            with open(cred_path) as f:
                creds_data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            raise RuntimeError(f"Failed to read credentials file '{cred_path}': {e}")

        if _is_service_account(creds_data):
            creds = SACredentials.from_service_account_info(creds_data, scopes=scopes)
        elif _is_oauth_token(creds_data):
            creds = OAuthCredentials.from_authorized_user_info(creds_data, scopes)
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(google.auth.transport.requests.Request())
        else:
            # Might be an OAuth2 client secrets file — need to run flow
            raise RuntimeError(
                f"The credentials file at '{cred_path}' appears to be an OAuth2 client "
                "secrets file. Run 'cli-anything-google-tag-manager auth init' to "
                "authenticate and save a token."
            )

    # Fall back to saved OAuth token
    if creds is None and _TOKEN_FILE.is_file():
        with open(_TOKEN_FILE) as f:
            token_data = json.load(f)
        creds = OAuthCredentials.from_authorized_user_info(token_data, scopes)
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(google.auth.transport.requests.Request())

    if creds is None:
        raise RuntimeError(
            "No GTM credentials found. To authenticate, run:\n"
            "  cli-anything-google-tag-manager auth init\n\n"
            "Or set one of:\n"
            "  GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json\n"
            "  GTM_CREDENTIALS_FILE=/path/to/credentials.json\n\n"
            "Get credentials from: https://console.cloud.google.com/iam-admin/serviceaccounts"
        )

    return build("tagmanager", "v2", credentials=creds, cache_discovery=False)


def run_oauth_flow(client_secrets_file: str, readonly: bool = False) -> str:
    """Run the OAuth2 browser-based authorization flow and save the token.

    Args:
        client_secrets_file: Path to OAuth2 client secrets JSON.
        readonly: If True, request read-only scopes.

    Returns:
        Path to the saved token file.
    """
    scopes = SCOPES_READONLY if readonly else SCOPES_ALL
    flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, scopes)
    creds = flow.run_local_server(port=0)

    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    token_data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": list(creds.scopes or []),
    }
    with open(_TOKEN_FILE, "w") as f:
        json.dump(token_data, f, indent=2)

    return str(_TOKEN_FILE)


def install_service_account(sa_json_path: str) -> str:
    """Copy a service account JSON to the default config location.

    Args:
        sa_json_path: Path to the service account key JSON file.

    Returns:
        Path where it was installed.
    """
    with open(sa_json_path) as f:
        data = json.load(f)
    if not _is_service_account(data):
        raise ValueError(f"File '{sa_json_path}' is not a service account key JSON.")

    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    dest = str(_DEFAULT_CREDS_FILE)
    with open(dest, "w") as f:
        json.dump(data, f, indent=2)
    return dest


# ── Accounts ─────────────────────────────────────────────────────────

def list_accounts(service) -> list:
    """List all GTM accounts accessible to the authenticated user."""
    resp = service.accounts().list().execute()
    return resp.get("account", [])


def get_account(service, account_id: str) -> dict:
    """Get details for a specific GTM account."""
    path = f"accounts/{account_id}"
    return service.accounts().get(path=path).execute()


def update_account(service, account_id: str, body: dict) -> dict:
    """Update a GTM account (e.g., display name)."""
    path = f"accounts/{account_id}"
    return service.accounts().update(path=path, body=body).execute()


# ── Containers ───────────────────────────────────────────────────────

def list_containers(service, account_id: str) -> list:
    """List all containers in a GTM account."""
    parent = f"accounts/{account_id}"
    resp = service.accounts().containers().list(parent=parent).execute()
    return resp.get("container", [])


def get_container(service, account_id: str, container_id: str) -> dict:
    """Get a specific GTM container."""
    path = f"accounts/{account_id}/containers/{container_id}"
    return service.accounts().containers().get(path=path).execute()


def create_container(service, account_id: str, name: str, usage_context: list,
                     domain_name: list = None, notes: str = "") -> dict:
    """Create a new container in a GTM account.

    Args:
        usage_context: List of contexts, e.g. ['web', 'androidSdk5', 'iosSdk5', 'amp']
        domain_name: List of domain names for the container.
    """
    parent = f"accounts/{account_id}"
    body = {
        "name": name,
        "usageContext": usage_context,
    }
    if domain_name:
        body["domainName"] = domain_name
    if notes:
        body["notes"] = notes
    return service.accounts().containers().create(parent=parent, body=body).execute()


def update_container(service, account_id: str, container_id: str, body: dict) -> dict:
    """Update a GTM container."""
    path = f"accounts/{account_id}/containers/{container_id}"
    return service.accounts().containers().update(path=path, body=body).execute()


def delete_container(service, account_id: str, container_id: str) -> None:
    """Delete a GTM container."""
    path = f"accounts/{account_id}/containers/{container_id}"
    service.accounts().containers().delete(path=path).execute()


def get_snippet(service, account_id: str, container_id: str) -> dict:
    """Get the tagging snippet for a container."""
    path = f"accounts/{account_id}/containers/{container_id}"
    return service.accounts().containers().snippet(path=path).execute()


# ── Workspaces ───────────────────────────────────────────────────────

def list_workspaces(service, account_id: str, container_id: str) -> list:
    """List all workspaces in a container."""
    parent = f"accounts/{account_id}/containers/{container_id}"
    resp = service.accounts().containers().workspaces().list(parent=parent).execute()
    return resp.get("workspace", [])


def get_workspace(service, account_id: str, container_id: str, workspace_id: str) -> dict:
    """Get a specific workspace."""
    path = f"accounts/{account_id}/containers/{container_id}/workspaces/{workspace_id}"
    return service.accounts().containers().workspaces().get(path=path).execute()


def create_workspace(service, account_id: str, container_id: str,
                     name: str, description: str = "") -> dict:
    """Create a new workspace."""
    parent = f"accounts/{account_id}/containers/{container_id}"
    body = {"name": name}
    if description:
        body["description"] = description
    return service.accounts().containers().workspaces().create(
        parent=parent, body=body
    ).execute()


def update_workspace(service, account_id: str, container_id: str,
                     workspace_id: str, body: dict) -> dict:
    """Update a workspace."""
    path = f"accounts/{account_id}/containers/{container_id}/workspaces/{workspace_id}"
    return service.accounts().containers().workspaces().update(
        path=path, body=body
    ).execute()


def delete_workspace(service, account_id: str, container_id: str,
                     workspace_id: str) -> None:
    """Delete a workspace."""
    path = f"accounts/{account_id}/containers/{container_id}/workspaces/{workspace_id}"
    service.accounts().containers().workspaces().delete(path=path).execute()


def workspace_status(service, account_id: str, container_id: str,
                     workspace_id: str) -> dict:
    """Get status (changes, conflicts) for a workspace."""
    path = f"accounts/{account_id}/containers/{container_id}/workspaces/{workspace_id}"
    return service.accounts().containers().workspaces().getStatus(path=path).execute()


def sync_workspace(service, account_id: str, container_id: str,
                   workspace_id: str) -> dict:
    """Sync a workspace with the latest container version."""
    path = f"accounts/{account_id}/containers/{container_id}/workspaces/{workspace_id}"
    return service.accounts().containers().workspaces().sync(path=path).execute()


def create_version(service, account_id: str, container_id: str,
                   workspace_id: str, name: str = "",
                   notes: str = "") -> dict:
    """Create a new container version from a workspace."""
    path = f"accounts/{account_id}/containers/{container_id}/workspaces/{workspace_id}"
    body = {}
    if name:
        body["name"] = name
    if notes:
        body["notes"] = notes
    return service.accounts().containers().workspaces().create_version(
        path=path, body=body
    ).execute()


def quick_preview(service, account_id: str, container_id: str,
                  workspace_id: str) -> dict:
    """Create a quick preview of a workspace."""
    path = f"accounts/{account_id}/containers/{container_id}/workspaces/{workspace_id}"
    return service.accounts().containers().workspaces().quick_preview(
        path=path
    ).execute()


# ── Tags ─────────────────────────────────────────────────────────────

def list_tags(service, account_id: str, container_id: str,
              workspace_id: str) -> list:
    """List all tags in a workspace."""
    parent = f"accounts/{account_id}/containers/{container_id}/workspaces/{workspace_id}"
    resp = service.accounts().containers().workspaces().tags().list(
        parent=parent
    ).execute()
    return resp.get("tag", [])


def get_tag(service, account_id: str, container_id: str,
            workspace_id: str, tag_id: str) -> dict:
    """Get a specific tag."""
    path = (
        f"accounts/{account_id}/containers/{container_id}"
        f"/workspaces/{workspace_id}/tags/{tag_id}"
    )
    return service.accounts().containers().workspaces().tags().get(path=path).execute()


def create_tag(service, account_id: str, container_id: str,
               workspace_id: str, name: str, tag_type: str,
               parameters: list = None, firing_trigger_ids: list = None,
               blocking_trigger_ids: list = None,
               tag_firing_option: str = "oncePerEvent") -> dict:
    """Create a new tag in a workspace."""
    parent = (
        f"accounts/{account_id}/containers/{container_id}"
        f"/workspaces/{workspace_id}"
    )
    body = {"name": name, "type": tag_type, "tagFiringOption": tag_firing_option}
    if parameters:
        body["parameter"] = parameters
    if firing_trigger_ids:
        body["firingTriggerId"] = firing_trigger_ids
    if blocking_trigger_ids:
        body["blockingTriggerId"] = blocking_trigger_ids
    return service.accounts().containers().workspaces().tags().create(
        parent=parent, body=body
    ).execute()


def update_tag(service, account_id: str, container_id: str,
               workspace_id: str, tag_id: str, body: dict) -> dict:
    """Update a tag."""
    path = (
        f"accounts/{account_id}/containers/{container_id}"
        f"/workspaces/{workspace_id}/tags/{tag_id}"
    )
    return service.accounts().containers().workspaces().tags().update(
        path=path, body=body
    ).execute()


def delete_tag(service, account_id: str, container_id: str,
               workspace_id: str, tag_id: str) -> None:
    """Delete a tag."""
    path = (
        f"accounts/{account_id}/containers/{container_id}"
        f"/workspaces/{workspace_id}/tags/{tag_id}"
    )
    service.accounts().containers().workspaces().tags().delete(path=path).execute()


def revert_tag(service, account_id: str, container_id: str,
               workspace_id: str, tag_id: str) -> dict:
    """Revert changes to a tag."""
    path = (
        f"accounts/{account_id}/containers/{container_id}"
        f"/workspaces/{workspace_id}/tags/{tag_id}"
    )
    return service.accounts().containers().workspaces().tags().revert(
        path=path
    ).execute()


# ── Triggers ─────────────────────────────────────────────────────────

def list_triggers(service, account_id: str, container_id: str,
                  workspace_id: str) -> list:
    """List all triggers in a workspace."""
    parent = (
        f"accounts/{account_id}/containers/{container_id}"
        f"/workspaces/{workspace_id}"
    )
    resp = service.accounts().containers().workspaces().triggers().list(
        parent=parent
    ).execute()
    return resp.get("trigger", [])


def get_trigger(service, account_id: str, container_id: str,
                workspace_id: str, trigger_id: str) -> dict:
    """Get a specific trigger."""
    path = (
        f"accounts/{account_id}/containers/{container_id}"
        f"/workspaces/{workspace_id}/triggers/{trigger_id}"
    )
    return service.accounts().containers().workspaces().triggers().get(
        path=path
    ).execute()


def create_trigger(service, account_id: str, container_id: str,
                   workspace_id: str, name: str, trigger_type: str,
                   filters: list = None, custom_event_filter: list = None) -> dict:
    """Create a new trigger."""
    parent = (
        f"accounts/{account_id}/containers/{container_id}"
        f"/workspaces/{workspace_id}"
    )
    body = {"name": name, "type": trigger_type}
    if filters:
        body["filter"] = filters
    if custom_event_filter:
        body["customEventFilter"] = custom_event_filter
    return service.accounts().containers().workspaces().triggers().create(
        parent=parent, body=body
    ).execute()


def update_trigger(service, account_id: str, container_id: str,
                   workspace_id: str, trigger_id: str, body: dict) -> dict:
    """Update a trigger."""
    path = (
        f"accounts/{account_id}/containers/{container_id}"
        f"/workspaces/{workspace_id}/triggers/{trigger_id}"
    )
    return service.accounts().containers().workspaces().triggers().update(
        path=path, body=body
    ).execute()


def delete_trigger(service, account_id: str, container_id: str,
                   workspace_id: str, trigger_id: str) -> None:
    """Delete a trigger."""
    path = (
        f"accounts/{account_id}/containers/{container_id}"
        f"/workspaces/{workspace_id}/triggers/{trigger_id}"
    )
    service.accounts().containers().workspaces().triggers().delete(
        path=path
    ).execute()


def revert_trigger(service, account_id: str, container_id: str,
                   workspace_id: str, trigger_id: str) -> dict:
    """Revert changes to a trigger."""
    path = (
        f"accounts/{account_id}/containers/{container_id}"
        f"/workspaces/{workspace_id}/triggers/{trigger_id}"
    )
    return service.accounts().containers().workspaces().triggers().revert(
        path=path
    ).execute()


# ── Variables ────────────────────────────────────────────────────────

def list_variables(service, account_id: str, container_id: str,
                   workspace_id: str) -> list:
    """List all variables in a workspace."""
    parent = (
        f"accounts/{account_id}/containers/{container_id}"
        f"/workspaces/{workspace_id}"
    )
    resp = service.accounts().containers().workspaces().variables().list(
        parent=parent
    ).execute()
    return resp.get("variable", [])


def get_variable(service, account_id: str, container_id: str,
                 workspace_id: str, variable_id: str) -> dict:
    """Get a specific variable."""
    path = (
        f"accounts/{account_id}/containers/{container_id}"
        f"/workspaces/{workspace_id}/variables/{variable_id}"
    )
    return service.accounts().containers().workspaces().variables().get(
        path=path
    ).execute()


def create_variable(service, account_id: str, container_id: str,
                    workspace_id: str, name: str, variable_type: str,
                    parameters: list = None) -> dict:
    """Create a new variable."""
    parent = (
        f"accounts/{account_id}/containers/{container_id}"
        f"/workspaces/{workspace_id}"
    )
    body = {"name": name, "type": variable_type}
    if parameters:
        body["parameter"] = parameters
    return service.accounts().containers().workspaces().variables().create(
        parent=parent, body=body
    ).execute()


def update_variable(service, account_id: str, container_id: str,
                    workspace_id: str, variable_id: str, body: dict) -> dict:
    """Update a variable."""
    path = (
        f"accounts/{account_id}/containers/{container_id}"
        f"/workspaces/{workspace_id}/variables/{variable_id}"
    )
    return service.accounts().containers().workspaces().variables().update(
        path=path, body=body
    ).execute()


def delete_variable(service, account_id: str, container_id: str,
                    workspace_id: str, variable_id: str) -> None:
    """Delete a variable."""
    path = (
        f"accounts/{account_id}/containers/{container_id}"
        f"/workspaces/{workspace_id}/variables/{variable_id}"
    )
    service.accounts().containers().workspaces().variables().delete(
        path=path
    ).execute()


def revert_variable(service, account_id: str, container_id: str,
                    workspace_id: str, variable_id: str) -> dict:
    """Revert changes to a variable."""
    path = (
        f"accounts/{account_id}/containers/{container_id}"
        f"/workspaces/{workspace_id}/variables/{variable_id}"
    )
    return service.accounts().containers().workspaces().variables().revert(
        path=path
    ).execute()


# ── Folders ──────────────────────────────────────────────────────────

def list_folders(service, account_id: str, container_id: str,
                 workspace_id: str) -> list:
    """List all folders in a workspace."""
    parent = (
        f"accounts/{account_id}/containers/{container_id}"
        f"/workspaces/{workspace_id}"
    )
    resp = service.accounts().containers().workspaces().folders().list(
        parent=parent
    ).execute()
    return resp.get("folder", [])


def get_folder(service, account_id: str, container_id: str,
               workspace_id: str, folder_id: str) -> dict:
    """Get a specific folder."""
    path = (
        f"accounts/{account_id}/containers/{container_id}"
        f"/workspaces/{workspace_id}/folders/{folder_id}"
    )
    return service.accounts().containers().workspaces().folders().get(
        path=path
    ).execute()


def create_folder(service, account_id: str, container_id: str,
                  workspace_id: str, name: str) -> dict:
    """Create a new folder."""
    parent = (
        f"accounts/{account_id}/containers/{container_id}"
        f"/workspaces/{workspace_id}"
    )
    body = {"name": name}
    return service.accounts().containers().workspaces().folders().create(
        parent=parent, body=body
    ).execute()


def update_folder(service, account_id: str, container_id: str,
                  workspace_id: str, folder_id: str, body: dict) -> dict:
    """Update a folder."""
    path = (
        f"accounts/{account_id}/containers/{container_id}"
        f"/workspaces/{workspace_id}/folders/{folder_id}"
    )
    return service.accounts().containers().workspaces().folders().update(
        path=path, body=body
    ).execute()


def delete_folder(service, account_id: str, container_id: str,
                  workspace_id: str, folder_id: str) -> None:
    """Delete a folder."""
    path = (
        f"accounts/{account_id}/containers/{container_id}"
        f"/workspaces/{workspace_id}/folders/{folder_id}"
    )
    service.accounts().containers().workspaces().folders().delete(
        path=path
    ).execute()


def folder_entities(service, account_id: str, container_id: str,
                    workspace_id: str, folder_id: str) -> dict:
    """List entities (tags, triggers, variables) in a folder."""
    path = (
        f"accounts/{account_id}/containers/{container_id}"
        f"/workspaces/{workspace_id}/folders/{folder_id}"
    )
    return service.accounts().containers().workspaces().folders().entities(
        path=path
    ).execute()


def move_to_folder(service, account_id: str, container_id: str,
                   workspace_id: str, folder_id: str,
                   tag_id: list = None, trigger_id: list = None,
                   variable_id: list = None) -> None:
    """Move entities to a folder."""
    path = (
        f"accounts/{account_id}/containers/{container_id}"
        f"/workspaces/{workspace_id}/folders/{folder_id}"
    )
    body = {}
    if tag_id:
        body["tag"] = [{"tagId": tid} for tid in tag_id]
    if trigger_id:
        body["trigger"] = [{"triggerId": tid} for tid in trigger_id]
    if variable_id:
        body["variable"] = [{"variableId": vid} for vid in variable_id]
    service.accounts().containers().workspaces().folders().move_entities_to_folder(
        path=path, body=body
    ).execute()


def revert_folder(service, account_id: str, container_id: str,
                  workspace_id: str, folder_id: str) -> dict:
    """Revert changes to a folder."""
    path = (
        f"accounts/{account_id}/containers/{container_id}"
        f"/workspaces/{workspace_id}/folders/{folder_id}"
    )
    return service.accounts().containers().workspaces().folders().revert(
        path=path
    ).execute()


# ── Environments ─────────────────────────────────────────────────────

def list_environments(service, account_id: str, container_id: str) -> list:
    """List all environments for a container."""
    parent = f"accounts/{account_id}/containers/{container_id}"
    resp = service.accounts().containers().environments().list(
        parent=parent
    ).execute()
    return resp.get("environment", [])


def get_environment(service, account_id: str, container_id: str,
                    environment_id: str) -> dict:
    """Get a specific environment."""
    path = (
        f"accounts/{account_id}/containers/{container_id}"
        f"/environments/{environment_id}"
    )
    return service.accounts().containers().environments().get(path=path).execute()


def create_environment(service, account_id: str, container_id: str,
                       name: str, env_type: str = "user",
                       description: str = "", url: str = "") -> dict:
    """Create a new environment."""
    parent = f"accounts/{account_id}/containers/{container_id}"
    body = {"name": name, "type": env_type}
    if description:
        body["description"] = description
    if url:
        body["url"] = url
    return service.accounts().containers().environments().create(
        parent=parent, body=body
    ).execute()


def update_environment(service, account_id: str, container_id: str,
                       environment_id: str, body: dict) -> dict:
    """Update an environment."""
    path = (
        f"accounts/{account_id}/containers/{container_id}"
        f"/environments/{environment_id}"
    )
    return service.accounts().containers().environments().update(
        path=path, body=body
    ).execute()


def delete_environment(service, account_id: str, container_id: str,
                       environment_id: str) -> None:
    """Delete an environment."""
    path = (
        f"accounts/{account_id}/containers/{container_id}"
        f"/environments/{environment_id}"
    )
    service.accounts().containers().environments().delete(path=path).execute()


def reauthorize_environment(service, account_id: str, container_id: str,
                            environment_id: str) -> dict:
    """Reauthorize an environment (regenerate auth code)."""
    path = (
        f"accounts/{account_id}/containers/{container_id}"
        f"/environments/{environment_id}"
    )
    return service.accounts().containers().environments().reauthorize(
        path=path, body={}
    ).execute()


# ── Version Headers ───────────────────────────────────────────────────

def list_version_headers(service, account_id: str, container_id: str,
                         include_deleted: bool = False) -> list:
    """List all version headers for a container."""
    parent = f"accounts/{account_id}/containers/{container_id}"
    resp = service.accounts().containers().version_headers().list(
        parent=parent, includeDeleted=include_deleted
    ).execute()
    return resp.get("containerVersionHeader", [])


def latest_version_header(service, account_id: str, container_id: str) -> dict:
    """Get the latest version header for a container."""
    parent = f"accounts/{account_id}/containers/{container_id}"
    return service.accounts().containers().version_headers().latest(
        parent=parent
    ).execute()


# ── User Permissions ─────────────────────────────────────────────────

def list_permissions(service, account_id: str) -> list:
    """List all user permissions for a GTM account."""
    parent = f"accounts/{account_id}"
    resp = service.accounts().user_permissions().list(parent=parent).execute()
    return resp.get("userPermission", [])


def get_permission(service, account_id: str, user_permission_id: str) -> dict:
    """Get a specific user permission."""
    path = f"accounts/{account_id}/user_permissions/{user_permission_id}"
    return service.accounts().user_permissions().get(path=path).execute()


def create_permission(service, account_id: str, email: str,
                      account_access: dict = None,
                      container_accesses: list = None) -> dict:
    """Grant permissions to a user.

    Args:
        email: User's email address.
        account_access: Account-level access dict, e.g. {"permission": "admin"}.
        container_accesses: List of container access dicts.
    """
    parent = f"accounts/{account_id}"
    body = {"emailAddress": email}
    if account_access:
        body["accountAccess"] = account_access
    if container_accesses:
        body["containerAccess"] = container_accesses
    return service.accounts().user_permissions().create(
        parent=parent, body=body
    ).execute()


def update_permission(service, account_id: str, user_permission_id: str,
                      body: dict) -> dict:
    """Update user permissions."""
    path = f"accounts/{account_id}/user_permissions/{user_permission_id}"
    return service.accounts().user_permissions().update(
        path=path, body=body
    ).execute()


def delete_permission(service, account_id: str, user_permission_id: str) -> None:
    """Delete (revoke) a user's permissions."""
    path = f"accounts/{account_id}/user_permissions/{user_permission_id}"
    service.accounts().user_permissions().delete(path=path).execute()


# ── Built-in Variables ───────────────────────────────────────────────

def list_builtin_variables(service, account_id: str, container_id: str,
                           workspace_id: str) -> list:
    """List all enabled built-in variables in a workspace."""
    parent = (
        f"accounts/{account_id}/containers/{container_id}"
        f"/workspaces/{workspace_id}"
    )
    resp = service.accounts().containers().workspaces().built_in_variables().list(
        parent=parent
    ).execute()
    return resp.get("builtInVariable", [])


def enable_builtin_variable(service, account_id: str, container_id: str,
                            workspace_id: str, variable_type: list) -> dict:
    """Enable one or more built-in variable types."""
    parent = (
        f"accounts/{account_id}/containers/{container_id}"
        f"/workspaces/{workspace_id}"
    )
    return service.accounts().containers().workspaces().built_in_variables().create(
        parent=parent, type=variable_type
    ).execute()


def disable_builtin_variable(service, account_id: str, container_id: str,
                             workspace_id: str, variable_type: list) -> None:
    """Disable one or more built-in variable types."""
    path = (
        f"accounts/{account_id}/containers/{container_id}"
        f"/workspaces/{workspace_id}"
    )
    service.accounts().containers().workspaces().built_in_variables().delete(
        path=path, type=variable_type
    ).execute()


# ── HTTP Error Helper ────────────────────────────────────────────────

def format_http_error(e: "HttpError") -> str:
    """Format an HttpError into a human-readable error message."""
    try:
        details = json.loads(e.content.decode())
        msg = details.get("error", {}).get("message", str(e))
        code = details.get("error", {}).get("code", e.resp.status)
        return f"GTM API Error {code}: {msg}"
    except Exception:
        return f"GTM API Error: {e}"
