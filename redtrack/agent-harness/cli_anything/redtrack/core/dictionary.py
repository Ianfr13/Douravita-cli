"""Reference data (dictionary) lookups for RedTrack.

These endpoints do not require authentication (no api_key needed).
Wraps the RedTrack reference data REST API endpoints.
"""

from cli_anything.redtrack.utils.redtrack_backend import DEFAULT_BASE_URL
import requests

_LOOKUP_KEYS = [
    "browser_fullnames",
    "browsers",
    "categories",
    "cities",
    "connection_types",
    "countries",
    "currencies",
    "device_brands",
    "device_fullnames",
    "devices",
    "isp",
    "languages",
    "os",
    "os_fullnames",
]


def _dict_get(base_url: str, path: str):
    """Make an unauthenticated GET request to the dictionary endpoint.

    Args:
        base_url: API base URL.
        path: Endpoint path (e.g. '/countries').

    Returns:
        Parsed JSON response.

    Raises:
        RuntimeError: On connection errors, timeouts, or non-2xx responses.
    """
    url = base_url.rstrip("/") + path
    try:
        resp = requests.get(url, timeout=30)
    except requests.exceptions.ConnectionError:
        raise RuntimeError(f"Cannot connect to RedTrack at {base_url}")
    except requests.exceptions.Timeout:
        raise RuntimeError(f"Request to {url} timed out")
    if not resp.content:
        return {"status": "ok"}
    try:
        resp.raise_for_status()
    except requests.exceptions.HTTPError:
        raise RuntimeError(f"RedTrack API error {resp.status_code} on GET {path}: {resp.text}")
    return resp.json()


def get_browsers(base_url: str = DEFAULT_BASE_URL):
    """Get list of browser identifiers."""
    return _dict_get(base_url, "/browsers")


def get_browser_fullnames(base_url: str = DEFAULT_BASE_URL):
    """Get list of browser full names."""
    return _dict_get(base_url, "/browser_fullnames")


def get_categories(base_url: str = DEFAULT_BASE_URL):
    """Get list of offer categories."""
    return _dict_get(base_url, "/categories")


def get_cities(base_url: str = DEFAULT_BASE_URL):
    """Get list of cities."""
    return _dict_get(base_url, "/cities")


def get_connection_types(base_url: str = DEFAULT_BASE_URL):
    """Get list of connection types."""
    return _dict_get(base_url, "/connection_types")


def get_countries(base_url: str = DEFAULT_BASE_URL):
    """Get list of countries."""
    return _dict_get(base_url, "/countries")


def get_currencies(base_url: str = DEFAULT_BASE_URL):
    """Get list of currencies."""
    return _dict_get(base_url, "/currencies")


def get_device_brands(base_url: str = DEFAULT_BASE_URL):
    """Get list of device brands."""
    return _dict_get(base_url, "/device_brands")


def get_device_fullnames(base_url: str = DEFAULT_BASE_URL):
    """Get list of device full names."""
    return _dict_get(base_url, "/device_fullnames")


def get_devices(base_url: str = DEFAULT_BASE_URL):
    """Get list of device types."""
    return _dict_get(base_url, "/devices")


def get_isp(base_url: str = DEFAULT_BASE_URL):
    """Get list of ISPs."""
    return _dict_get(base_url, "/isp")


def get_languages(base_url: str = DEFAULT_BASE_URL):
    """Get list of languages."""
    return _dict_get(base_url, "/languages")


def get_os(base_url: str = DEFAULT_BASE_URL):
    """Get list of operating systems."""
    return _dict_get(base_url, "/os")


def get_os_fullnames(base_url: str = DEFAULT_BASE_URL):
    """Get list of OS full names."""
    return _dict_get(base_url, "/os_fullnames")


def list_all_keys() -> list:
    """Return the list of all available lookup type keys.

    Returns:
        List of lookup key name strings (14 total).
    """
    return list(_LOOKUP_KEYS)
