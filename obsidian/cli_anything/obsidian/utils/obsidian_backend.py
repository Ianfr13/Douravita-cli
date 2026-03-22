"""Obsidian Local REST API wrapper — the single module that makes network requests.

Obsidian exposes a local REST API via a plugin (obsidian-local-rest-api).
Default URLs:
  - HTTPS: https://127.0.0.1:27124  (self-signed cert — SSL verification disabled)
  - HTTP:  http://127.0.0.1:27123

Authentication: Bearer token in Authorization header.
Token is found in Obsidian Settings → Local REST API.
"""

import os
import requests
from typing import Any, NoReturn
from urllib.parse import quote

# Default Obsidian REST API base URL (HTTPS with self-signed cert)
DEFAULT_BASE_URL = "https://127.0.0.1:27124"
DEFAULT_HTTP_URL = "http://127.0.0.1:27123"

# Suppress InsecureRequestWarning for self-signed cert
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def _get_api_key(api_key: str | None) -> str:
    """Resolve API key from argument or environment variable.

    Args:
        api_key: Explicit API key, or None to read from env.

    Returns:
        API key string.

    Raises:
        RuntimeError: If no API key is available.
    """
    key = api_key or os.environ.get("OBSIDIAN_API_KEY", "")
    if not key:
        raise RuntimeError(
            "No Obsidian API key found. Set OBSIDIAN_API_KEY environment variable "
            "or use --api-key flag. "
            "Find your key in Obsidian Settings → Local REST API."
        )
    return key


def _headers(api_key: str | None, accept: str = "application/json",
             content_type: str | None = None, extra: dict | None = None) -> dict:
    """Build request headers with auth token and content negotiation.

    Args:
        api_key: Bearer token for authentication.
        accept: Accept header value for response format.
        content_type: Optional Content-Type header.
        extra: Optional extra headers dict (e.g., PATCH headers).

    Returns:
        Dict of HTTP headers.
    """
    key = _get_api_key(api_key)
    h = {
        "Authorization": f"Bearer {key}",
        "Accept": accept,
    }
    if content_type:
        h["Content-Type"] = content_type
    if extra:
        h.update(extra)
    return h


def _url(base_url: str, path: str) -> str:
    """Construct a full URL from base and path.

    Args:
        base_url: Server base URL (e.g., 'https://127.0.0.1:27124').
        path: API path, already URL-encoded (e.g., '/vault/Notes/my%20file.md').

    Returns:
        Full URL string.
    """
    return f"{base_url.rstrip('/')}{path}"


def encode_path(path: str) -> str:
    """URL-encode a vault file path, preserving forward slashes.

    Args:
        path: Vault-relative file path (e.g., 'folder/My Note.md').

    Returns:
        URL-encoded path safe for use in request URLs.
    """
    # Encode each segment but keep slashes intact
    parts = path.split("/")
    return "/".join(quote(p, safe="") for p in parts)


def _handle_response(resp: requests.Response, endpoint: str, method: str) -> Any:
    """Parse and return a response, raising on HTTP errors.

    Args:
        resp: requests Response object.
        endpoint: API endpoint (for error messages).
        method: HTTP method (for error messages).

    Returns:
        Parsed JSON, text content, or status dict.

    Raises:
        RuntimeError: On HTTP 4xx/5xx responses.
    """
    if resp.status_code == 204 or not resp.content:
        return {"status": "ok"}

    content_type = resp.headers.get("Content-Type", "")

    if "application/json" in content_type or "vnd.olrapi" in content_type:
        try:
            return resp.json()
        except Exception:
            pass

    # Markdown or plain text
    return {"content": resp.text}


def api_get(base_url: str, endpoint: str, api_key: str | None = None,
            accept: str = "application/json",
            params: dict | None = None, timeout: int = 30) -> Any:
    """Perform an authenticated GET request.

    Args:
        base_url: Obsidian server base URL.
        endpoint: API path (e.g., '/vault/Notes/my-note.md').
        api_key: Bearer token (falls back to OBSIDIAN_API_KEY env var).
        accept: Accept header for response format.
        params: Optional query parameters.
        timeout: Request timeout in seconds.

    Returns:
        Parsed response (dict, list, or content dict).

    Raises:
        RuntimeError: On HTTP error or connection failure.
    """
    url = _url(base_url, endpoint)
    auth_required = endpoint != "/"
    if auth_required:
        headers = _headers(api_key, accept=accept)
    else:
        # GET / is public — no Bearer token needed, but still send Accept header
        headers = {"Accept": accept}

    try:
        resp = requests.get(url, headers=headers, params=params,
                            timeout=timeout, verify=False)
        resp.raise_for_status()
        return _handle_response(resp, endpoint, "GET")
    except requests.exceptions.ConnectionError as e:
        raise RuntimeError(
            f"Cannot connect to Obsidian at {base_url}. "
            "Is Obsidian running with the Local REST API plugin enabled?"
        ) from e
    except requests.exceptions.HTTPError as e:
        _raise_http_error(resp, "GET", endpoint)
    except requests.exceptions.Timeout as e:
        raise RuntimeError(f"Request timed out: GET {endpoint}") from e


def api_post(base_url: str, endpoint: str, api_key: str | None = None,
             body: str | bytes | dict | None = None,
             content_type: str = "text/markdown",
             accept: str = "application/json",
             params: dict | None = None,
             extra_headers: dict | None = None,
             timeout: int = 30) -> Any:
    """Perform an authenticated POST request.

    Args:
        base_url: Obsidian server base URL.
        endpoint: API path.
        api_key: Bearer token.
        body: Request body — string/bytes sent as-is, dict sent as JSON.
        content_type: Content-Type header.
        accept: Accept header.
        params: Optional query parameters.
        extra_headers: Optional additional headers.
        timeout: Request timeout.

    Returns:
        Parsed response.

    Raises:
        RuntimeError: On HTTP error or connection failure.
    """
    url = _url(base_url, endpoint)
    headers = _headers(api_key, accept=accept, content_type=content_type,
                       extra=extra_headers)
    try:
        if isinstance(body, dict):
            # Serialize to string and use data= to preserve our custom Content-Type header.
            # Using json= would let requests overwrite Content-Type with "application/json",
            # breaking custom MIME types like application/vnd.olrapi.jsonlogic+json.
            import json as _json
            body_bytes = _json.dumps(body).encode("utf-8")
            resp = requests.post(url, data=body_bytes, headers=headers,
                                 params=params, timeout=timeout, verify=False)
        elif body is not None:
            resp = requests.post(url, data=body.encode() if isinstance(body, str) else body,
                                 headers=headers, params=params,
                                 timeout=timeout, verify=False)
        else:
            resp = requests.post(url, headers=headers, params=params,
                                 timeout=timeout, verify=False)
        resp.raise_for_status()
        return _handle_response(resp, endpoint, "POST")
    except requests.exceptions.ConnectionError as e:
        raise RuntimeError(
            f"Cannot connect to Obsidian at {base_url}. "
            "Is Obsidian running with the Local REST API plugin enabled?"
        ) from e
    except requests.exceptions.HTTPError as e:
        _raise_http_error(resp, "POST", endpoint)
    except requests.exceptions.Timeout as e:
        raise RuntimeError(f"Request timed out: POST {endpoint}") from e


def api_put(base_url: str, endpoint: str, api_key: str | None = None,
            body: str | bytes | None = None,
            content_type: str = "text/markdown",
            timeout: int = 30) -> Any:
    """Perform an authenticated PUT request (create or replace file).

    Args:
        base_url: Obsidian server base URL.
        endpoint: API path.
        api_key: Bearer token.
        body: File content as string or bytes.
        content_type: Content-Type header.
        timeout: Request timeout.

    Returns:
        Status dict.

    Raises:
        RuntimeError: On HTTP error or connection failure.
    """
    url = _url(base_url, endpoint)
    headers = _headers(api_key, content_type=content_type)
    try:
        data = body.encode() if isinstance(body, str) else (body or b"")
        resp = requests.put(url, data=data, headers=headers,
                            timeout=timeout, verify=False)
        resp.raise_for_status()
        return _handle_response(resp, endpoint, "PUT")
    except requests.exceptions.ConnectionError as e:
        raise RuntimeError(
            f"Cannot connect to Obsidian at {base_url}. "
            "Is Obsidian running with the Local REST API plugin enabled?"
        ) from e
    except requests.exceptions.HTTPError as e:
        _raise_http_error(resp, "PUT", endpoint)
    except requests.exceptions.Timeout as e:
        raise RuntimeError(f"Request timed out: PUT {endpoint}") from e


def api_patch(base_url: str, endpoint: str, api_key: str | None = None,
              body: str = "",
              operation: str = "append",
              target_type: str = "heading",
              target: str = "",
              delimiter: str = "::",
              trim_whitespace: bool = False,
              create_if_missing: bool = False,
              timeout: int = 30) -> Any:
    """Perform an authenticated PATCH request (partial note update).

    Args:
        base_url: Obsidian server base URL.
        endpoint: API path.
        api_key: Bearer token.
        body: Content to insert/replace.
        operation: 'append', 'prepend', or 'replace'.
        target_type: 'heading', 'block', or 'frontmatter'.
        target: Section name, block reference, or frontmatter key.
        delimiter: Separator for nested headings (default '::').
        trim_whitespace: Whether to trim target whitespace.
        create_if_missing: Create target section if it doesn't exist.
        timeout: Request timeout.

    Returns:
        Status dict.

    Raises:
        RuntimeError: On HTTP error or connection failure.
    """
    from urllib.parse import quote as url_quote
    url = _url(base_url, endpoint)

    patch_headers = {
        "Operation": operation,
        "Target-Type": target_type,
        "Target": url_quote(target, safe=""),
        "Target-Delimiter": delimiter,
        "Trim-Target-Whitespace": str(trim_whitespace).lower(),
        "Create-Target-If-Missing": str(create_if_missing).lower(),
    }
    headers = _headers(api_key, content_type="text/markdown", extra=patch_headers)

    try:
        resp = requests.patch(url, data=body.encode(), headers=headers,
                              timeout=timeout, verify=False)
        resp.raise_for_status()
        return _handle_response(resp, endpoint, "PATCH")
    except requests.exceptions.ConnectionError as e:
        raise RuntimeError(
            f"Cannot connect to Obsidian at {base_url}. "
            "Is Obsidian running with the Local REST API plugin enabled?"
        ) from e
    except requests.exceptions.HTTPError as e:
        _raise_http_error(resp, "PATCH", endpoint)
    except requests.exceptions.Timeout as e:
        raise RuntimeError(f"Request timed out: PATCH {endpoint}") from e


def api_delete(base_url: str, endpoint: str, api_key: str | None = None,
               timeout: int = 30) -> Any:
    """Perform an authenticated DELETE request.

    Args:
        base_url: Obsidian server base URL.
        endpoint: API path.
        api_key: Bearer token.
        timeout: Request timeout.

    Returns:
        Status dict.

    Raises:
        RuntimeError: On HTTP error or connection failure.
    """
    url = _url(base_url, endpoint)
    headers = _headers(api_key)
    try:
        resp = requests.delete(url, headers=headers, timeout=timeout, verify=False)
        resp.raise_for_status()
        return _handle_response(resp, endpoint, "DELETE")
    except requests.exceptions.ConnectionError as e:
        raise RuntimeError(
            f"Cannot connect to Obsidian at {base_url}. "
            "Is Obsidian running with the Local REST API plugin enabled?"
        ) from e
    except requests.exceptions.HTTPError as e:
        _raise_http_error(resp, "DELETE", endpoint)
    except requests.exceptions.Timeout as e:
        raise RuntimeError(f"Request timed out: DELETE {endpoint}") from e


def _raise_http_error(resp: requests.Response, method: str, endpoint: str) -> NoReturn:
    """Raise a descriptive RuntimeError for HTTP error responses.

    Args:
        resp: The failed response.
        method: HTTP method string.
        endpoint: API endpoint path.

    Raises:
        RuntimeError: Always raised with a descriptive message.
    """
    try:
        err_body = resp.json()
        msg = err_body.get("message", resp.text)
    except Exception:
        msg = resp.text or f"HTTP {resp.status_code}"

    if resp.status_code == 401:
        raise RuntimeError(
            f"Authentication failed (401). Check your OBSIDIAN_API_KEY. "
            f"API key is in Obsidian Settings → Local REST API."
        )
    if resp.status_code == 404:
        raise RuntimeError(f"Not found (404): {endpoint} — {msg}")
    if resp.status_code == 405:
        raise RuntimeError(f"Method not allowed (405): {method} {endpoint}")

    raise RuntimeError(f"Obsidian API error {resp.status_code} on {method} {endpoint}: {msg}")


def is_available(base_url: str = DEFAULT_BASE_URL) -> bool:
    """Check if Obsidian REST API is reachable (no auth required for GET /).

    Args:
        base_url: Obsidian server base URL.

    Returns:
        True if the server responds, False otherwise.
    """
    try:
        resp = requests.get(f"{base_url.rstrip('/')}/", timeout=5, verify=False)
        return resp.status_code == 200
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return False


def accept_for_format(fmt: str) -> str:
    """Map a format name to the appropriate Accept header value.

    Args:
        fmt: Format name — 'markdown', 'json', or 'map'.

    Returns:
        MIME type string for the Accept header.
    """
    return {
        "markdown": "text/markdown",
        "json": "application/vnd.olrapi.note+json",
        "map": "application/vnd.olrapi.document-map+json",
    }.get(fmt, "text/markdown")
