"""Session management for the GTM CLI.

Stores the current account/container/workspace context so users don't
have to pass IDs on every command. Uses file-based locking for safe
concurrent writes.
"""
import os
import json
from pathlib import Path
from typing import Optional

# Default session file location
_DEFAULT_SESSION_DIR = Path.home() / ".config" / "cli-anything-gtm"
_DEFAULT_SESSION_FILE = _DEFAULT_SESSION_DIR / "session.json"


def _locked_save_json(path: str, data: dict, **dump_kwargs) -> None:
    """Atomically write JSON with exclusive file locking."""
    try:
        f = open(path, "r+")            # no truncation on open
    except FileNotFoundError:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        f = open(path, "w")             # first save — file doesn't exist yet
    with f:
        _locked = False
        try:
            import fcntl
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            _locked = True
        except (ImportError, OSError):
            pass                        # Windows / unsupported FS — proceed unlocked
        try:
            f.seek(0)
            f.truncate()                # truncate INSIDE the lock
            json.dump(data, f, **dump_kwargs)
            f.flush()
        finally:
            if _locked:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)


class Session:
    """Persistent session state for the GTM CLI.

    Stores account_id, container_id, workspace_id, and credentials_file
    between commands in both REPL and one-shot modes.
    """

    def __init__(self, session_file: Optional[str] = None):
        self.session_file = session_file or str(_DEFAULT_SESSION_FILE)
        self._data = self._load()

    def _load(self) -> dict:
        """Load session data from disk."""
        try:
            with open(self.session_file) as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save(self) -> None:
        """Persist session data to disk."""
        _locked_save_json(self.session_file, self._data, indent=2)

    # ── Context getters/setters ───────────────────────────────────────

    @property
    def account_id(self) -> Optional[str]:
        return (
            os.environ.get("GTM_ACCOUNT_ID")
            or self._data.get("account_id")
        )

    @account_id.setter
    def account_id(self, value: str) -> None:
        self._data["account_id"] = value

    @property
    def container_id(self) -> Optional[str]:
        return (
            os.environ.get("GTM_CONTAINER_ID")
            or self._data.get("container_id")
        )

    @container_id.setter
    def container_id(self, value: str) -> None:
        self._data["container_id"] = value

    @property
    def workspace_id(self) -> Optional[str]:
        return (
            os.environ.get("GTM_WORKSPACE_ID")
            or self._data.get("workspace_id")
        )

    @workspace_id.setter
    def workspace_id(self, value: str) -> None:
        self._data["workspace_id"] = value

    @property
    def credentials_file(self) -> Optional[str]:
        return self._data.get("credentials_file")

    @credentials_file.setter
    def credentials_file(self, value: str) -> None:
        self._data["credentials_file"] = value

    def set_context(self, account_id: str = None, container_id: str = None,
                    workspace_id: str = None) -> None:
        """Set multiple context values at once and save."""
        if account_id is not None:
            self._data["account_id"] = account_id
        if container_id is not None:
            self._data["container_id"] = container_id
        if workspace_id is not None:
            self._data["workspace_id"] = workspace_id
        self.save()

    def clear(self) -> None:
        """Clear all session data."""
        self._data = {}
        self.save()

    def to_dict(self) -> dict:
        """Return session data as a dictionary."""
        return {
            "account_id": self.account_id,
            "container_id": self.container_id,
            "workspace_id": self.workspace_id,
            "credentials_file": self.credentials_file,
            "session_file": self.session_file,
        }

    def require_account(self) -> str:
        """Get account_id or raise a clear error."""
        aid = self.account_id
        if not aid:
            raise ValueError(
                "No GTM Account ID set. Use --account-id or set GTM_ACCOUNT_ID env var.\n"
                "Run 'cli-anything-google-tag-manager account list' to see available accounts."
            )
        return aid

    def require_container(self) -> tuple[str, str]:
        """Get (account_id, container_id) or raise a clear error."""
        aid = self.require_account()
        cid = self.container_id
        if not cid:
            raise ValueError(
                "No GTM Container ID set. Use --container-id or set GTM_CONTAINER_ID env var.\n"
                "Run 'cli-anything-google-tag-manager container list' to see available containers."
            )
        return aid, cid

    def require_workspace(self) -> tuple[str, str, str]:
        """Get (account_id, container_id, workspace_id) or raise a clear error."""
        aid, cid = self.require_container()
        wid = self.workspace_id
        if not wid:
            raise ValueError(
                "No GTM Workspace ID set. Use --workspace-id or set GTM_WORKSPACE_ID env var.\n"
                "Run 'cli-anything-google-tag-manager workspace list' to see available workspaces."
            )
        return aid, cid, wid
