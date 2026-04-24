"""WebSocket streaming client for Railway GraphQL subscriptions.

Railway exposes GraphQL subscriptions over ``wss://backboard.railway.app/graphql/v2``
using the ``graphql-transport-ws`` subprotocol.

Handshake sequence:
    1. connect with subprotocol=['graphql-transport-ws'] + Bearer header
    2. client -> {"type":"connection_init","payload":{"Authorization":"Bearer <token>"}}
    3. server -> {"type":"connection_ack"}
    4. client -> {"id":"<uuid>","type":"subscribe","payload":{"query":..., "variables":...}}
    5. server -> {"id":"...","type":"next","payload":{"data":{...}}}   (repeat)
    6. server -> {"id":"...","type":"complete"}  OR  client sends "complete" to unsubscribe
"""

from __future__ import annotations

import json
import threading
import uuid
from typing import Callable, Iterator

try:
    import websocket  # type: ignore
    _WS_AVAILABLE = True
except ImportError:  # pragma: no cover
    websocket = None  # type: ignore
    _WS_AVAILABLE = False


RAILWAY_WS_URL = "wss://backboard.railway.app/graphql/v2"


class StreamError(Exception):
    """Raised when the streaming subscription fails."""


def ws_available() -> bool:
    """True when ``websocket-client`` is installed."""
    return _WS_AVAILABLE


# ---------------------------------------------------------------------------
# Subscription queries
# ---------------------------------------------------------------------------

_SUB_DEPLOYMENT_LOGS = """
subscription StreamDeploymentLogs(
    $deploymentId: String!, $limit: Int, $filter: String
) {
    deploymentLogs(deploymentId: $deploymentId, limit: $limit, filter: $filter) {
        message
        severity
        timestamp
        tags { deploymentInstanceId serviceId environmentId projectId }
        attributes { key value }
    }
}
"""

_SUB_BUILD_LOGS = """
subscription StreamBuildLogs(
    $deploymentId: String!, $limit: Int, $filter: String
) {
    buildLogs(deploymentId: $deploymentId, limit: $limit, filter: $filter) {
        message
        severity
        timestamp
        attributes { key value }
    }
}
"""

_SUB_ENV_LOGS = """
subscription StreamEnvironmentLogs(
    $environmentId: String!, $filter: String,
    $beforeLimit: Int, $afterLimit: Int, $anchorDate: String
) {
    environmentLogs(
        environmentId: $environmentId, filter: $filter,
        beforeLimit: $beforeLimit, afterLimit: $afterLimit, anchorDate: $anchorDate
    ) {
        message
        severity
        timestamp
        tags { serviceId deploymentId deploymentInstanceId projectId environmentId }
        attributes { key value }
    }
}
"""

_SUB_HTTP_LOGS = """
subscription StreamHttpLogs(
    $deploymentId: String!, $filter: String,
    $beforeLimit: Int, $afterLimit: Int, $anchorDate: String
) {
    httpLogs(
        deploymentId: $deploymentId, filter: $filter,
        beforeLimit: $beforeLimit, afterLimit: $afterLimit, anchorDate: $anchorDate
    ) {
        timestamp requestId method path host httpStatus totalDuration
        upstreamRqDuration rxBytes txBytes srcIp edgeRegion clientUa
        responseDetails upstreamErrors
    }
}
"""


# ---------------------------------------------------------------------------
# Streaming primitive
# ---------------------------------------------------------------------------

def stream_subscription(
    token: str,
    query: str,
    variables: dict,
    result_key: str,
    on_entry: Callable[[dict], None],
    stop: threading.Event | None = None,
    ping_interval: int = 20,
    ws_url: str = RAILWAY_WS_URL,
) -> None:
    """Open a GraphQL subscription, deliver each entry via ``on_entry``.

    Blocks until the server completes the subscription, the peer closes, or
    ``stop`` is set. Intended to be called from a Ctrl-C-friendly caller.

    ``result_key`` is the top-level field name inside ``payload.data``
    (e.g. ``"deploymentLogs"``). Each message under that key is expected to be
    a list and each list item is forwarded to ``on_entry`` individually.
    """
    if not _WS_AVAILABLE:
        raise StreamError(
            "websocket-client is not installed. "
            "Install with: pip install websocket-client"
        )

    stop = stop or threading.Event()
    sub_id = str(uuid.uuid4())
    seen_error: list[str] = []

    def on_open(ws):
        ws.send(json.dumps({
            "type": "connection_init",
            "payload": {"Authorization": f"Bearer {token}"},
        }))

    def on_message(ws, raw):
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            return
        mtype = msg.get("type")

        if mtype == "connection_ack":
            ws.send(json.dumps({
                "id": sub_id,
                "type": "subscribe",
                "payload": {"query": query, "variables": variables},
            }))
            return

        if mtype == "next":
            payload = (msg.get("payload") or {}).get("data") or {}
            entries = payload.get(result_key) or []
            # A tick can return a batch; forward each entry.
            for entry in entries:
                if stop.is_set():
                    break
                on_entry(entry)
            return

        if mtype == "error":
            payload = msg.get("payload") or []
            detail = "; ".join(
                e.get("message", str(e)) for e in payload
            ) if isinstance(payload, list) else str(payload)
            seen_error.append(detail or "subscription error")
            stop.set()
            try:
                ws.close()
            except Exception:
                pass
            return

        if mtype == "complete":
            stop.set()
            try:
                ws.close()
            except Exception:
                pass

    def on_error(ws, exc):
        seen_error.append(str(exc))
        stop.set()

    def on_close(ws, code, reason):
        stop.set()

    ws = websocket.WebSocketApp(
        ws_url,
        header={"Authorization": f"Bearer {token}"},
        subprotocols=["graphql-transport-ws"],
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    )

    runner = threading.Thread(
        target=lambda: ws.run_forever(ping_interval=ping_interval),
        daemon=True,
    )
    runner.start()

    try:
        while runner.is_alive() and not stop.is_set():
            runner.join(timeout=0.25)
    except KeyboardInterrupt:
        stop.set()
    finally:
        try:
            # Try to send a clean unsubscribe before closing.
            ws.send(json.dumps({"id": sub_id, "type": "complete"}))
        except Exception:
            pass
        try:
            ws.close()
        except Exception:
            pass
        runner.join(timeout=2)

    if seen_error:
        raise StreamError(seen_error[0])


# ---------------------------------------------------------------------------
# High-level helpers per log type
# ---------------------------------------------------------------------------

def stream_deployment_logs(
    token: str,
    deployment_id: str,
    on_entry: Callable[[dict], None],
    filter_text: str | None = None,
    limit: int = 500,
    build: bool = False,
    stop: threading.Event | None = None,
) -> None:
    stream_subscription(
        token=token,
        query=_SUB_BUILD_LOGS if build else _SUB_DEPLOYMENT_LOGS,
        variables={
            "deploymentId": deployment_id,
            "limit": limit,
            "filter": filter_text,
        },
        result_key="buildLogs" if build else "deploymentLogs",
        on_entry=on_entry,
        stop=stop,
    )


def stream_environment_logs(
    token: str,
    environment_id: str,
    on_entry: Callable[[dict], None],
    filter_text: str | None = None,
    before_limit: int = 100,
    after_limit: int | None = None,
    anchor_date: str | None = None,
    stop: threading.Event | None = None,
) -> None:
    stream_subscription(
        token=token,
        query=_SUB_ENV_LOGS,
        variables={
            "environmentId": environment_id,
            "filter": filter_text,
            "beforeLimit": before_limit,
            "afterLimit": after_limit,
            "anchorDate": anchor_date,
        },
        result_key="environmentLogs",
        on_entry=on_entry,
        stop=stop,
    )


def stream_http_logs(
    token: str,
    deployment_id: str,
    on_entry: Callable[[dict], None],
    filter_text: str | None = None,
    before_limit: int = 100,
    after_limit: int | None = None,
    anchor_date: str | None = None,
    stop: threading.Event | None = None,
) -> None:
    stream_subscription(
        token=token,
        query=_SUB_HTTP_LOGS,
        variables={
            "deploymentId": deployment_id,
            "filter": filter_text,
            "beforeLimit": before_limit,
            "afterLimit": after_limit,
            "anchorDate": anchor_date,
        },
        result_key="httpLogs",
        on_entry=on_entry,
        stop=stop,
    )
