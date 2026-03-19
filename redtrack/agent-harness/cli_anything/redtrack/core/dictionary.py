"""Dictionary / reference data endpoints for RedTrack.

These endpoints return static reference lists (browsers, countries, OS, etc.)
and do NOT require authentication — no api_key needed.

Confirmed endpoints (from Swagger):
    /browser_fullnames, /browsers, /categories, /cities,
    /connection_types, /countries, /currencies, /device_brands,
    /device_fullnames, /devices, /isp, /languages, /os, /os_fullnames
"""

import requests
from typing import Any

DEFAULT_BASE_URL = "https://api.redtrack.io"

_DICT_ENDPOINTS = {
    "browsers": "/browsers",
    "browser_fullnames": "/browser_fullnames",
    "categories": "/categories",
    "cities": "/cities",
    "connection_types": "/connection_types",
    "countries": "/countries",
    "currencies": "/currencies",
    "device_brands": "/device_brands",
    "device_fullnames": "/device_fullnames",
    "devices": "/devices",
    "isp": "/isp",
    "languages": "/languages",
    "os": "/os",
    "os_fullnames": "/os_fullnames",
}


def _dict_get(endpoint: str, base_url: str = DEFAULT_BASE_URL) -> Any:
    """Perform an unauthenticated GET on a dictionary endpoint."""
    url = f"{base_url.rstrip('/')}{endpoint}"
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        if not resp.content:
            return []
        return resp.json()
    except requests.exceptions.ConnectionError as e:
        raise RuntimeError(f"Cannot connect to RedTrack API at {base_url}.") from e
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(
            f"RedTrack API error {resp.status_code} on GET {endpoint}: {resp.text}"
        ) from e
    except requests.exceptions.Timeout as e:
        raise RuntimeError(f"Request timed out: GET {endpoint}") from e


def get_browsers(base_url: str = DEFAULT_BASE_URL) -> list:
    """Get list of browser names."""
    return _dict_get("/browsers", base_url)


def get_browser_fullnames(base_url: str = DEFAULT_BASE_URL) -> list:
    """Get list of full browser names."""
    return _dict_get("/browser_fullnames", base_url)


def get_categories(base_url: str = DEFAULT_BASE_URL) -> list:
    """Get list of offer categories."""
    return _dict_get("/categories", base_url)


def get_cities(base_url: str = DEFAULT_BASE_URL) -> list:
    """Get list of city names."""
    return _dict_get("/cities", base_url)


def get_connection_types(base_url: str = DEFAULT_BASE_URL) -> list:
    """Get list of connection types."""
    return _dict_get("/connection_types", base_url)


def get_countries(base_url: str = DEFAULT_BASE_URL) -> list:
    """Get list of country codes and names."""
    return _dict_get("/countries", base_url)


def get_currencies(base_url: str = DEFAULT_BASE_URL) -> list:
    """Get list of supported currencies."""
    return _dict_get("/currencies", base_url)


def get_device_brands(base_url: str = DEFAULT_BASE_URL) -> list:
    """Get list of device brands."""
    return _dict_get("/device_brands", base_url)


def get_device_fullnames(base_url: str = DEFAULT_BASE_URL) -> list:
    """Get list of full device names."""
    return _dict_get("/device_fullnames", base_url)


def get_devices(base_url: str = DEFAULT_BASE_URL) -> list:
    """Get list of device types."""
    return _dict_get("/devices", base_url)


def get_isp(base_url: str = DEFAULT_BASE_URL) -> list:
    """Get list of ISP names."""
    return _dict_get("/isp", base_url)


def get_languages(base_url: str = DEFAULT_BASE_URL) -> list:
    """Get list of languages."""
    return _dict_get("/languages", base_url)


def get_os(base_url: str = DEFAULT_BASE_URL) -> list:
    """Get list of operating system names."""
    return _dict_get("/os", base_url)


def get_os_fullnames(base_url: str = DEFAULT_BASE_URL) -> list:
    """Get list of full OS names."""
    return _dict_get("/os_fullnames", base_url)


def list_all_keys() -> list[str]:
    """Return all available dictionary keys."""
    return list(_DICT_ENDPOINTS.keys())
