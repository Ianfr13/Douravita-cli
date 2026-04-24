"""WebSocket relay client for Railway remote exec / interactive shell.

Railway routes ``railway ssh`` / ``railway exec`` through a custom WebSocket
relay at ``wss://backboard.railway.com/relay``. This module implements the
same protocol the official CLI uses (reverse-engineered from the open-source
Rust client in ``railwayapp/cli``):

**Upgrade request headers:**
    Authorization: Bearer <token>
    X-Railway-Project-Id: <id>
    X-Railway-Service-Id: <id>
    X-Railway-Environment-Id: <id>
    X-Railway-Deployment-Instance-Id: <id>   (optional)
    X-Source: cli-anything-railway/<version>

**Client → server JSON messages:**
    {"type": "init_shell",   "payload": {"shell": "bash"}}          # start PTY shell
    {"type": "exec_command", "payload": {"command": "ls",
                                         "args": ["-la"],
                                         "env": {}}}                 # one-shot exec
    {"type": "data",         "payload": {"data": "<bytes as str>"}}  # stdin
    {"type": "window_size",  "payload": {"cols": 80, "rows": 24}}    # resize
    {"type": "signal",       "payload": {"signal": 2}}               # SIGINT

**Server → client JSON messages:**
    {"type": "welcome",      "payload": {"message": "..."}}
    {"type": "session_data", "payload": {"data": {"type":"Buffer","data":[u8,...]}}}
    {"type": "command_exit", "payload": {"code": 0}}
    {"type": "pty_closed",   "payload": {"message": "..."}}
    {"type": "error",        "payload": {"message": "..."}}
"""

from __future__ import annotations

import json
import os
import select
import signal as _signal
import sys
import threading
from typing import Callable

try:
    import websocket  # type: ignore
    _WS_AVAILABLE = True
except ImportError:  # pragma: no cover
    websocket = None  # type: ignore
    _WS_AVAILABLE = False


RELAY_WS_URL = "wss://backboard.railway.com/relay"

PING_INTERVAL_SECS = 10


class RelayError(Exception):
    """Raised when the relay connection fails or the server reports an error."""


def _decode_payload_data(payload: dict) -> bytes:
    """Extract bytes from a server-side data payload.

    Server sometimes sends ``data`` as a plain string, sometimes as a
    ``{"data": [u8, ...]}`` buffer. Both shapes are handled here.
    """
    data = payload.get("data")
    if data is None:
        return b""
    if isinstance(data, str):
        return data.encode("utf-8", errors="replace")
    if isinstance(data, dict):
        buf = data.get("data")
        if isinstance(buf, list):
            return bytes(buf)
    if isinstance(data, list):
        return bytes(data)
    return b""


def _headers(
    token: str,
    project_id: str,
    service_id: str,
    environment_id: str,
    deployment_instance_id: str | None = None,
    user_agent: str = "cli-anything-railway/1.2.0",
) -> dict:
    h = {
        "Authorization": f"Bearer {token}",
        "X-Railway-Project-Id": project_id,
        "X-Railway-Service-Id": service_id,
        "X-Railway-Environment-Id": environment_id,
        "X-Source": user_agent,
    }
    if deployment_instance_id:
        h["X-Railway-Deployment-Instance-Id"] = deployment_instance_id
    return h


def _connect(headers: dict, relay_url: str = RELAY_WS_URL):
    if not _WS_AVAILABLE:
        raise RelayError(
            "websocket-client is not installed. "
            "Install with: pip install websocket-client"
        )
    try:
        ws = websocket.create_connection(
            relay_url,
            header=[f"{k}: {v}" for k, v in headers.items()],
            timeout=30,
        )
    except Exception as exc:
        raise RelayError(f"Failed to connect to relay: {exc}") from exc
    return ws


def _send(ws, mtype: str, payload: dict) -> None:
    ws.send(json.dumps({"type": mtype, "payload": payload}))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def exec_command(
    token: str,
    project_id: str,
    service_id: str,
    environment_id: str,
    command: str,
    args: list[str] | None = None,
    env: dict[str, str] | None = None,
    deployment_instance_id: str | None = None,
    on_data: Callable[[bytes], None] | None = None,
    relay_url: str = RELAY_WS_URL,
) -> int:
    """Run a single command on the remote container and stream its output.

    Returns the server-reported exit code (``0`` when the server never sends
    one).  ``on_data`` receives each chunk of stdout/stderr as bytes; when
    ``None``, output is written directly to ``sys.stdout``.
    """
    if on_data is None:
        def on_data(b: bytes) -> None:
            try:
                sys.stdout.buffer.write(b)
                sys.stdout.buffer.flush()
            except Exception:
                sys.stdout.write(b.decode("utf-8", errors="replace"))
                sys.stdout.flush()

    ws = _connect(
        _headers(
            token, project_id, service_id, environment_id, deployment_instance_id
        ),
        relay_url,
    )
    exit_code = 0
    got_exit = False
    try:
        _send(
            ws,
            "exec_command",
            {
                "command": command,
                "args": args or [],
                "env": env or {},
            },
        )
        while True:
            try:
                raw = ws.recv()
            except websocket.WebSocketConnectionClosedException:
                break
            except Exception as exc:
                raise RelayError(f"Relay recv error: {exc}") from exc
            if not raw:
                continue
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue
            mtype = msg.get("type", "")
            payload = msg.get("payload") or {}
            if mtype in ("session_data", "data", "stdout", "stderr"):
                on_data(_decode_payload_data(payload))
            elif mtype in ("command_exit", "exit", "complete", "done"):
                exit_code = int(payload.get("code") or 0)
                got_exit = True
                # Keep reading briefly — server may still send pty_closed.
            elif mtype == "pty_closed":
                break
            elif mtype == "welcome":
                pass  # initial handshake
            elif mtype == "error":
                raise RelayError(payload.get("message") or "relay error")
            if got_exit and mtype not in ("session_data", "data", "stdout", "stderr"):
                break
    finally:
        try:
            ws.close()
        except Exception:
            pass
    return exit_code


def interactive_shell(
    token: str,
    project_id: str,
    service_id: str,
    environment_id: str,
    shell: str | None = None,
    deployment_instance_id: str | None = None,
    relay_url: str = RELAY_WS_URL,
) -> int:
    """Open an interactive PTY session over the relay.

    Switches the local terminal into raw mode, multiplexes stdin into the
    WebSocket as ``data`` messages, and writes server ``data`` back to
    stdout. Window resize events are forwarded via ``window_size`` messages.

    Returns the exit code reported by the server, or 0 on clean disconnect.
    """
    import termios
    import tty

    ws = _connect(
        _headers(
            token, project_id, service_id, environment_id, deployment_instance_id
        ),
        relay_url,
    )
    _send(ws, "init_shell", {"shell": shell} if shell else {})

    # Seed the remote with our current terminal size
    try:
        cols, rows = os.get_terminal_size(sys.stdout.fileno())
        _send(ws, "window_size", {"cols": cols, "rows": rows})
    except Exception:
        pass

    # Stash terminal state so we can restore it on exit
    stdin_fd = sys.stdin.fileno()
    old_attrs = None
    try:
        if sys.stdin.isatty():
            old_attrs = termios.tcgetattr(stdin_fd)
            tty.setraw(stdin_fd)
    except Exception:
        old_attrs = None

    exit_code = 0
    done = threading.Event()

    # SIGWINCH forwards resize to the remote PTY
    def on_winch(signum, frame):
        try:
            cols, rows = os.get_terminal_size(sys.stdout.fileno())
            _send(ws, "window_size", {"cols": cols, "rows": rows})
        except Exception:
            pass

    prev_winch = None
    try:
        prev_winch = _signal.signal(_signal.SIGWINCH, on_winch)
    except Exception:
        pass

    # Reader: server -> stdout
    def reader():
        nonlocal exit_code
        try:
            while not done.is_set():
                try:
                    raw = ws.recv()
                except websocket.WebSocketConnectionClosedException:
                    return
                except Exception:
                    return
                if not raw:
                    continue
                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                mtype = msg.get("type", "")
                payload = msg.get("payload") or {}
                if mtype in ("session_data", "data", "stdout", "stderr"):
                    buf = _decode_payload_data(payload)
                    if buf:
                        try:
                            sys.stdout.buffer.write(buf)
                            sys.stdout.buffer.flush()
                        except Exception:
                            pass
                elif mtype in ("command_exit", "exit", "complete", "done"):
                    exit_code = int(payload.get("code") or 0)
                elif mtype == "pty_closed":
                    return
                elif mtype == "welcome":
                    pass
                elif mtype == "error":
                    sys.stderr.write(f"\r\n[relay error] {payload.get('message','')}\r\n")
                    return
        finally:
            done.set()

    reader_thread = threading.Thread(target=reader, daemon=True)
    reader_thread.start()

    # Writer: stdin -> server (main thread, select-based)
    try:
        while not done.is_set():
            r, _, _ = select.select([stdin_fd], [], [], 0.1)
            if not r:
                continue
            try:
                data = os.read(stdin_fd, 4096)
            except OSError:
                break
            if not data:
                break
            _send(ws, "data", {"data": data.decode("utf-8", errors="replace")})
    except KeyboardInterrupt:
        pass
    finally:
        done.set()
        try:
            ws.close()
        except Exception:
            pass
        reader_thread.join(timeout=1.0)
        if old_attrs is not None:
            try:
                termios.tcsetattr(stdin_fd, termios.TCSADRAIN, old_attrs)
            except Exception:
                pass
        if prev_winch is not None:
            try:
                _signal.signal(_signal.SIGWINCH, prev_winch)
            except Exception:
                pass

    return exit_code


def ws_available() -> bool:
    return _WS_AVAILABLE
