"""Configuration management for cli-anything-meta-ads.

Credentials stored in ~/.config/cli-anything-meta-ads/config.json.
Environment variables META_ADS_ACCESS_TOKEN and META_ADS_AD_ACCOUNT_ID
always take precedence over stored config.
"""

import fcntl
import json
import os
from pathlib import Path
from typing import Optional

CONFIG_DIR = Path.home() / ".config" / "cli-anything-meta-ads"
CONFIG_FILE = CONFIG_DIR / "config.json"

ENV_ACCESS_TOKEN = "META_ADS_ACCESS_TOKEN"
ENV_AD_ACCOUNT_ID = "META_ADS_AD_ACCOUNT_ID"
ENV_APP_ID = "META_ADS_APP_ID"
ENV_APP_SECRET = "META_ADS_APP_SECRET"


def _locked_save_json(path: Path, data: dict) -> None:
    """Atomically write JSON with exclusive file locking."""
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


def load_config() -> dict:
    if not CONFIG_FILE.exists():
        return {}
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_config(data: dict) -> None:
    _locked_save_json(CONFIG_FILE, data)


def get_access_token() -> Optional[str]:
    return os.environ.get(ENV_ACCESS_TOKEN) or load_config().get("access_token")


def get_ad_account_id() -> Optional[str]:
    raw = os.environ.get(ENV_AD_ACCOUNT_ID) or load_config().get("ad_account_id")
    if raw and not raw.startswith("act_"):
        return f"act_{raw}"
    return raw


def get_app_id() -> Optional[str]:
    return os.environ.get(ENV_APP_ID) or load_config().get("app_id")


def get_app_secret() -> Optional[str]:
    return os.environ.get(ENV_APP_SECRET) or load_config().get("app_secret")


def set_credentials(access_token=None, ad_account_id=None,
                    app_id=None, app_secret=None) -> dict:
    cfg = load_config()
    if access_token is not None:
        cfg["access_token"] = access_token
    if ad_account_id is not None:
        cfg["ad_account_id"] = ad_account_id.lstrip("act_")
    if app_id is not None:
        cfg["app_id"] = app_id
    if app_secret is not None:
        cfg["app_secret"] = app_secret
    save_config(cfg)
    return cfg


def clear_credentials() -> None:
    save_config({})


def require_access_token() -> str:
    token = get_access_token()
    if not token:
        raise RuntimeError(
            "No Meta access token configured.\n"
            "Set it with:\n"
            "  cli-anything-meta-ads config set-token YOUR_TOKEN\n"
            "Or set the environment variable:\n"
            f"  export {ENV_ACCESS_TOKEN}=YOUR_TOKEN"
        )
    return token


def require_ad_account_id(override: str = None) -> str:
    account_id = override or get_ad_account_id()
    if not account_id:
        raise RuntimeError(
            "No ad account ID configured.\n"
            "Set it with:\n"
            "  cli-anything-meta-ads config set-account YOUR_ACCOUNT_ID\n"
            "Or set the environment variable:\n"
            f"  export {ENV_AD_ACCOUNT_ID}=YOUR_ACCOUNT_ID"
        )
    if not account_id.startswith("act_"):
        account_id = f"act_{account_id}"
    return account_id


def show_config() -> dict:
    cfg = load_config()
    result = {}
    if token := cfg.get("access_token"):
        result["access_token"] = token[:8] + "..." + token[-4:] if len(token) > 12 else "***"
    else:
        result["access_token"] = None
    result["ad_account_id"] = cfg.get("ad_account_id")
    result["app_id"] = cfg.get("app_id")
    result["app_secret"] = "***" if cfg.get("app_secret") else None
    result["config_file"] = str(CONFIG_FILE)
    if os.environ.get(ENV_ACCESS_TOKEN):
        result["access_token_source"] = "environment variable"
    elif cfg.get("access_token"):
        result["access_token_source"] = "config file"
    else:
        result["access_token_source"] = "not set"
    return result
