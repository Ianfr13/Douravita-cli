"""Configuration management for cli-anything-langfuse.

Supports profiles stored in ~/.cli-anything-langfuse/config.json,
environment variables, and CLI flags. Priority: flags > env > config.
"""

import json
import os
from pathlib import Path
from typing import Any

CONFIG_DIR = Path.home() / ".cli-anything-langfuse"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_BASE_URL = "https://cloud.langfuse.com"

# Environment variable names
ENV_PUBLIC_KEY = "LANGFUSE_PUBLIC_KEY"
ENV_SECRET_KEY = "LANGFUSE_SECRET_KEY"
ENV_BASE_URL = "LANGFUSE_BASE_URL"
ENV_PROFILE = "LANGFUSE_PROFILE"


def _load_config() -> dict:
    """Load the config file, or return empty config."""
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            return {"profiles": {}, "active_profile": "default"}
    return {"profiles": {}, "active_profile": "default"}


def _save_config(config: dict) -> None:
    """Save config to file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, indent=2))


def get_profile(profile_name: str | None = None) -> dict:
    """Get a profile's configuration.

    Args:
        profile_name: Profile to load. Falls back to env var, then active profile.

    Returns:
        Dict with keys: public_key, secret_key, base_url.
    """
    config = _load_config()

    name = (
        profile_name
        or os.environ.get(ENV_PROFILE)
        or config.get("active_profile", "default")
    )

    profile = config.get("profiles", {}).get(name, {})

    return {
        "public_key": profile.get("public_key", ""),
        "secret_key": profile.get("secret_key", ""),
        "base_url": profile.get("base_url", DEFAULT_BASE_URL),
    }


def resolve_credentials(
    public_key: str | None = None,
    secret_key: str | None = None,
    base_url: str | None = None,
    profile: str | None = None,
) -> dict:
    """Resolve credentials with priority: flags > env > config profile.

    Returns:
        Dict with keys: public_key, secret_key, base_url.
    """
    prof = get_profile(profile)

    return {
        "public_key": public_key or os.environ.get(ENV_PUBLIC_KEY) or prof["public_key"],
        "secret_key": secret_key or os.environ.get(ENV_SECRET_KEY) or prof["secret_key"],
        "base_url": base_url or os.environ.get(ENV_BASE_URL) or prof["base_url"] or DEFAULT_BASE_URL,
    }


def set_profile(
    profile_name: str,
    public_key: str | None = None,
    secret_key: str | None = None,
    base_url: str | None = None,
) -> dict:
    """Create or update a profile.

    Returns:
        The updated profile dict.
    """
    config = _load_config()

    if "profiles" not in config:
        config["profiles"] = {}

    existing = config["profiles"].get(profile_name, {})

    if public_key is not None:
        existing["public_key"] = public_key
    if secret_key is not None:
        existing["secret_key"] = secret_key
    if base_url is not None:
        existing["base_url"] = base_url

    config["profiles"][profile_name] = existing
    _save_config(config)
    return existing


def set_active_profile(profile_name: str) -> None:
    """Set the active profile."""
    config = _load_config()
    config["active_profile"] = profile_name
    _save_config(config)


def list_profiles() -> list[dict]:
    """List all profiles.

    Returns:
        List of dicts with profile info.
    """
    config = _load_config()
    active = config.get("active_profile", "default")
    profiles = config.get("profiles", {})

    result = []
    for name, prof in profiles.items():
        result.append({
            "name": name,
            "active": name == active,
            "base_url": prof.get("base_url", DEFAULT_BASE_URL),
            "public_key": _mask_key(prof.get("public_key", "")),
            "has_secret": bool(prof.get("secret_key")),
        })
    return result


def delete_profile(profile_name: str) -> bool:
    """Delete a profile. Returns True if deleted."""
    config = _load_config()
    if profile_name in config.get("profiles", {}):
        del config["profiles"][profile_name]
        if config.get("active_profile") == profile_name:
            config["active_profile"] = "default"
        _save_config(config)
        return True
    return False


def _mask_key(key: str) -> str:
    """Mask a key for display, showing only prefix."""
    if not key:
        return "(not set)"
    if len(key) <= 10:
        return key[:4] + "****"
    return key[:10] + "****"
