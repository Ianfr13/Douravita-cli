"""REPL session state for cli-anything-meta-ads."""

import fcntl
import json
import os
from pathlib import Path
from typing import Optional

SESSION_DIR = Path.home() / ".config" / "cli-anything-meta-ads"
SESSION_FILE = SESSION_DIR / "session.json"


def _locked_save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        f = open(path, "r+")
    except FileNotFoundError:
        f = open(path, "w")
    with f:
        _locked = False
        try:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            _locked = True
        except (ImportError, OSError):
            pass
        try:
            f.seek(0)
            f.truncate()
            json.dump(data, f, indent=2)
            f.flush()
        finally:
            if _locked:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)


class Session:
    """Holds REPL state: current ad account, active campaign/adset context."""

    def __init__(self):
        self.ad_account_id: Optional[str] = None
        self.active_campaign_id: Optional[str] = None
        self.active_campaign_name: Optional[str] = None
        self.active_adset_id: Optional[str] = None
        self.active_adset_name: Optional[str] = None
        self._load()

    def _load(self):
        if SESSION_FILE.exists():
            try:
                with open(SESSION_FILE) as f:
                    data = json.load(f)
                self.ad_account_id = data.get("ad_account_id")
                self.active_campaign_id = data.get("active_campaign_id")
                self.active_campaign_name = data.get("active_campaign_name")
                self.active_adset_id = data.get("active_adset_id")
                self.active_adset_name = data.get("active_adset_name")
            except (json.JSONDecodeError, OSError):
                pass

    def save(self):
        _locked_save_json(SESSION_FILE, {
            "ad_account_id": self.ad_account_id,
            "active_campaign_id": self.active_campaign_id,
            "active_campaign_name": self.active_campaign_name,
            "active_adset_id": self.active_adset_id,
            "active_adset_name": self.active_adset_name,
        })

    def set_account(self, account_id: str):
        self.ad_account_id = account_id
        self.active_campaign_id = None
        self.active_campaign_name = None
        self.active_adset_id = None
        self.active_adset_name = None
        self.save()

    def set_campaign(self, campaign_id: str, campaign_name: str = ""):
        self.active_campaign_id = campaign_id
        self.active_campaign_name = campaign_name
        self.active_adset_id = None
        self.active_adset_name = None
        self.save()

    def set_adset(self, adset_id: str, adset_name: str = ""):
        self.active_adset_id = adset_id
        self.active_adset_name = adset_name
        self.save()

    def clear(self):
        self.ad_account_id = None
        self.active_campaign_id = None
        self.active_campaign_name = None
        self.active_adset_id = None
        self.active_adset_name = None
        self.save()

    @property
    def context_label(self) -> str:
        """Short label for the REPL prompt context."""
        if self.active_adset_name:
            return self.active_adset_name
        if self.active_campaign_name:
            return self.active_campaign_name
        if self.ad_account_id:
            return self.ad_account_id.replace("act_", "")
        return ""
