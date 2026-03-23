"""Langfuse API backend — HTTP client wrapping the Langfuse REST API.

This is the equivalent of the "real software backend" for web-based platforms.
Instead of invoking a local executable, it makes authenticated HTTP requests
to the Langfuse API server.
"""

import json
import urllib.request
import urllib.error
import urllib.parse
import base64
from typing import Any


class LangfuseAPIError(Exception):
    """Raised when the Langfuse API returns an error."""

    def __init__(self, status_code: int, message: str, body: str = ""):
        self.status_code = status_code
        self.body = body
        super().__init__(f"HTTP {status_code}: {message}")


class LangfuseClient:
    """HTTP client for the Langfuse public API.

    Uses only stdlib (urllib) — no requests dependency needed.
    """

    def __init__(self, public_key: str, secret_key: str, base_url: str):
        if not public_key or not secret_key:
            raise ValueError(
                "Langfuse API keys are required.\n"
                "Set them via:\n"
                "  cli-anything-langfuse config set --public-key pk-lf-... --secret-key sk-lf-...\n"
                "  or env vars: LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY"
            )
        self.public_key = public_key
        self.secret_key = secret_key
        self.base_url = base_url.rstrip("/")
        # Pre-compute auth header
        creds = base64.b64encode(f"{public_key}:{secret_key}".encode()).decode()
        self._auth_header = f"Basic {creds}"

    def _request(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        body: dict | None = None,
        timeout: int = 30,
    ) -> dict:
        """Make an HTTP request to the Langfuse API.

        Args:
            method: HTTP method (GET, POST, PATCH, DELETE).
            path: API path (e.g., "/api/public/traces").
            params: Query parameters.
            body: JSON request body.
            timeout: Request timeout in seconds.

        Returns:
            Parsed JSON response as dict.

        Raises:
            LangfuseAPIError: On HTTP errors.
        """
        url = f"{self.base_url}{path}"

        if params:
            # Filter out None values
            filtered = {k: v for k, v in params.items() if v is not None}
            if filtered:
                url += "?" + urllib.parse.urlencode(filtered, doseq=True)

        headers = {
            "Authorization": self._auth_header,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        data = None
        if body is not None:
            data = json.dumps(body).encode("utf-8")

        req = urllib.request.Request(url, data=data, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                resp_body = resp.read().decode("utf-8")
                if not resp_body:
                    return {}
                return json.loads(resp_body)
        except urllib.error.HTTPError as e:
            error_body = ""
            try:
                error_body = e.read().decode("utf-8")
            except Exception:
                pass
            msg = _parse_error_message(e.code, error_body)
            raise LangfuseAPIError(e.code, msg, error_body) from None
        except urllib.error.URLError as e:
            raise LangfuseAPIError(0, f"Connection error: {e.reason}") from None

    def get(self, path: str, params: dict | None = None, **kwargs) -> dict:
        return self._request("GET", path, params=params, **kwargs)

    def post(self, path: str, body: dict | None = None, **kwargs) -> dict:
        return self._request("POST", path, body=body, **kwargs)

    def patch(self, path: str, body: dict | None = None, **kwargs) -> dict:
        return self._request("PATCH", path, body=body, **kwargs)

    def delete(self, path: str, params: dict | None = None, **kwargs) -> dict:
        return self._request("DELETE", path, params=params, **kwargs)


def _parse_error_message(status_code: int, body: str) -> str:
    """Extract a human-readable error message from the API response."""
    if not body:
        messages = {
            400: "Bad request",
            401: "Unauthorized — check your API keys",
            403: "Forbidden — insufficient permissions",
            404: "Not found",
            405: "Method not allowed",
            429: "Rate limited — try again later",
            500: "Internal server error",
            503: "Service unavailable",
        }
        return messages.get(status_code, f"Unknown error (HTTP {status_code})")
    try:
        data = json.loads(body)
        return data.get("message", data.get("error", body[:200]))
    except (json.JSONDecodeError, AttributeError):
        return body[:200]
