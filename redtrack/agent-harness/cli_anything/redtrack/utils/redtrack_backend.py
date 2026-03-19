"""RedTrack REST API wrapper — the single module that makes network requests.

RedTrack API base URL: https://api.redtrack.io
Authentication: API key passed as ?api_key={key} query parameter AND via Api-Key header.
The API key is read from the REDTRACK_API_KEY environment variable by default.
"""

import os
import requests
from typing import Any

DEFAULT_BASE_URL = "https://api.redtrack.io"


def _get_api_key(api_key: str | None = None) -> str:
    """Resolve API key from argument or environment variable.

    Args:
        api_key: Explicit API key, or None to read from environment.

    Returns:
        The API key string.

    Raises:
        RuntimeError: If no API key is available.
    """
    if api_key:
        return api_key
    key = os.environ.get("REDTRACK_API_KEY", "")
    if not key:
        raise RuntimeError(
            "No API key found. Set the REDTRACK_API_KEY environment variable "
            "or pass --api-key on the command line."
        )
    return key


def _build_params(params: dict | None, api_key: str) -> dict:
    """Merge user params with api_key query parameter."""
    merged = {"api_key": api_key}
    if params:
        merged.update(params)
    return merged


def _build_headers(api_key: str) -> dict:
    """Build request headers including the Api-Key header."""
    return {
        "Api-Key": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def api_get(endpoint: str, params: dict | None = None,
            api_key: str | None = None,
            base_url: str = DEFAULT_BASE_URL) -> Any:
    """Perform a GET request against the RedTrack API.

    Args:
        endpoint: API endpoint path (e.g., '/campaigns').
        params: Optional query parameters (api_key is added automatically).
        api_key: Explicit API key, or None to use REDTRACK_API_KEY env var.
        base_url: RedTrack API base URL.

    Returns:
        Parsed JSON response as a dict or list.

    Raises:
        RuntimeError: On HTTP error, connection failure, or missing API key.
    """
    key = _get_api_key(api_key)
    url = f"{base_url.rstrip('/')}{endpoint}"
    merged_params = _build_params(params, key)
    headers = _build_headers(key)
    try:
        resp = requests.get(url, params=merged_params, headers=headers, timeout=30)
        resp.raise_for_status()
        if resp.status_code == 204 or not resp.content:
            return {"status": "ok"}
        return resp.json()
    except requests.exceptions.ConnectionError as e:
        raise RuntimeError(
            f"Cannot connect to RedTrack API at {base_url}. "
            "Check your internet connection."
        ) from e
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(
            f"RedTrack API error {resp.status_code} on GET {endpoint}: {resp.text}"
        ) from e
    except requests.exceptions.Timeout as e:
        raise RuntimeError(
            f"Request to RedTrack API timed out: GET {endpoint}"
        ) from e


def api_post(endpoint: str, data: dict | None = None,
             api_key: str | None = None,
             base_url: str = DEFAULT_BASE_URL) -> Any:
    """Perform a POST request against the RedTrack API.

    Args:
        endpoint: API endpoint path.
        data: JSON request body.
        api_key: Explicit API key, or None to use REDTRACK_API_KEY env var.
        base_url: RedTrack API base URL.

    Returns:
        Parsed JSON response.

    Raises:
        RuntimeError: On HTTP error, connection failure, or missing API key.
    """
    key = _get_api_key(api_key)
    url = f"{base_url.rstrip('/')}{endpoint}"
    params = _build_params(None, key)
    headers = _build_headers(key)
    try:
        resp = requests.post(url, json=data, params=params, headers=headers, timeout=30)
        resp.raise_for_status()
        if resp.status_code == 204 or not resp.content:
            return {"status": "ok"}
        return resp.json()
    except requests.exceptions.ConnectionError as e:
        raise RuntimeError(
            f"Cannot connect to RedTrack API at {base_url}. "
            "Check your internet connection."
        ) from e
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(
            f"RedTrack API error {resp.status_code} on POST {endpoint}: {resp.text}"
        ) from e
    except requests.exceptions.Timeout as e:
        raise RuntimeError(
            f"Request to RedTrack API timed out: POST {endpoint}"
        ) from e


def api_patch(endpoint: str, data: dict | None = None,
              api_key: str | None = None,
              base_url: str = DEFAULT_BASE_URL) -> Any:
    """Perform a PATCH request against the RedTrack API.

    Args:
        endpoint: API endpoint path.
        data: JSON request body with fields to update.
        api_key: Explicit API key, or None to use REDTRACK_API_KEY env var.
        base_url: RedTrack API base URL.

    Returns:
        Parsed JSON response.

    Raises:
        RuntimeError: On HTTP error, connection failure, or missing API key.
    """
    key = _get_api_key(api_key)
    url = f"{base_url.rstrip('/')}{endpoint}"
    params = _build_params(None, key)
    headers = _build_headers(key)
    try:
        resp = requests.patch(url, json=data, params=params, headers=headers, timeout=30)
        resp.raise_for_status()
        if resp.status_code == 204 or not resp.content:
            return {"status": "ok"}
        return resp.json()
    except requests.exceptions.ConnectionError as e:
        raise RuntimeError(
            f"Cannot connect to RedTrack API at {base_url}. "
            "Check your internet connection."
        ) from e
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(
            f"RedTrack API error {resp.status_code} on PATCH {endpoint}: {resp.text}"
        ) from e
    except requests.exceptions.Timeout as e:
        raise RuntimeError(
            f"Request to RedTrack API timed out: PATCH {endpoint}"
        ) from e


def api_delete(endpoint: str, api_key: str | None = None,
               base_url: str = DEFAULT_BASE_URL) -> Any:
    """Perform a DELETE request against the RedTrack API.

    Args:
        endpoint: API endpoint path.
        api_key: Explicit API key, or None to use REDTRACK_API_KEY env var.
        base_url: RedTrack API base URL.

    Returns:
        Parsed JSON response or status dict.

    Raises:
        RuntimeError: On HTTP error, connection failure, or missing API key.
    """
    key = _get_api_key(api_key)
    url = f"{base_url.rstrip('/')}{endpoint}"
    params = _build_params(None, key)
    headers = _build_headers(key)
    try:
        resp = requests.delete(url, params=params, headers=headers, timeout=30)
        resp.raise_for_status()
        if resp.status_code == 204 or not resp.content:
            return {"status": "ok"}
        return resp.json()
    except requests.exceptions.ConnectionError as e:
        raise RuntimeError(
            f"Cannot connect to RedTrack API at {base_url}. "
            "Check your internet connection."
        ) from e
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(
            f"RedTrack API error {resp.status_code} on DELETE {endpoint}: {resp.text}"
        ) from e
    except requests.exceptions.Timeout as e:
        raise RuntimeError(
            f"Request to RedTrack API timed out: DELETE {endpoint}"
        ) from e


def is_available(api_key: str | None = None,
                 base_url: str = DEFAULT_BASE_URL) -> bool:
    """Check if the RedTrack API is reachable and the API key is valid.

    Args:
        api_key: Explicit API key, or None to use REDTRACK_API_KEY env var.
        base_url: RedTrack API base URL.

    Returns:
        True if the API responds successfully, False otherwise.
    """
    try:
        key = _get_api_key(api_key)
        url = f"{base_url.rstrip('/')}/user"
        params = {"api_key": key}
        headers = _build_headers(key)
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        return resp.status_code == 200
    except (requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            RuntimeError):
        return False
