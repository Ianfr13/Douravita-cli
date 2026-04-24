"""Logs commands for cli-anything-railway.

Railway logging reference: https://docs.railway.com/reference/logging

Filter syntax (server-side via API):
    @level:error AND "failed"            # severity + keyword
    @service:<service_id>                # narrow to service (env logs)
    @httpStatus:>=500                    # numeric comparisons
    @path:/api AND -@method:OPTIONS      # boolean + negation
"""

from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime, timedelta, timezone

import click

from cli_anything.railway.utils.railway_backend import RailwayBackend, RailwayAPIError
from cli_anything.railway.utils import railway_stream

_SEVERITY_COLORS = {
    "ERROR": "\033[38;5;196m",
    "WARN":  "\033[38;5;220m",
    "WARNING": "\033[38;5;220m",
    "INFO":  "\033[38;5;75m",
    "DEBUG": "\033[38;5;245m",
}
_RESET = "\033[0m"

_SEVERITY_RANK = {"DEBUG": 0, "INFO": 1, "WARN": 2, "WARNING": 2, "ERROR": 3}

_REL_RE = re.compile(r"^(\d+)([smhd])$")


def _parse_time(value: str | None) -> str | None:
    """Accept ISO-8601 ("2026-04-24T13:00:00Z") or relative ("30m", "2h", "1d").

    Returns an ISO-8601 UTC string or None when value is falsy.
    """
    if not value:
        return None
    m = _REL_RE.match(value.strip())
    if m:
        qty = int(m.group(1))
        unit = m.group(2)
        seconds = {"s": 1, "m": 60, "h": 3600, "d": 86400}[unit] * qty
        dt = datetime.now(timezone.utc) - timedelta(seconds=seconds)
        return dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    # Accept as-is; Railway parses ISO-8601.
    return value


def _compose_filter(filter_text: str | None, severity: str | None) -> str | None:
    """Merge --filter and --severity into a single Railway filter string."""
    parts: list[str] = []
    if filter_text:
        parts.append(filter_text)
    if severity:
        parts.append(f"@level:{severity.lower()}")
    if not parts:
        return None
    return " AND ".join(f"({p})" for p in parts) if len(parts) > 1 else parts[0]


def _fmt_log_line(entry: dict, color: bool = True, raw: bool = False) -> str:
    message = entry.get("message") or ""
    if raw:
        return message
    ts = (entry.get("timestamp") or "")[:19]
    severity = (entry.get("severity") or "INFO").upper()
    if color:
        sev_color = _SEVERITY_COLORS.get(severity, "")
        sev_tag = f"{sev_color}[{severity:<5}]{_RESET}" if sev_color else f"[{severity:<5}]"
        ts_tag = f"\033[38;5;245m{ts}{_RESET}" if ts else ""
    else:
        sev_tag = f"[{severity:<5}]"
        ts_tag = ts
    return f"  {ts_tag}  {sev_tag}  {message}"


def _fmt_env_line(entry: dict, color: bool = True, raw: bool = False) -> str:
    if raw:
        return entry.get("message") or ""
    tags = entry.get("tags") or {}
    svc = tags.get("serviceId") or (entry.get("serviceName") or "unknown")
    svc = (svc or "")[:15]
    ts = (entry.get("timestamp") or "")[:19]
    severity = (entry.get("severity") or "INFO").upper()
    message = entry.get("message") or ""
    if color:
        sev_color = _SEVERITY_COLORS.get(severity, "")
        sev_tag = f"{sev_color}[{severity:<5}]{_RESET}" if sev_color else f"[{severity:<5}]"
        return (
            f"  \033[38;5;245m{ts}{_RESET}  "
            f"\033[38;5;141m{svc:<15}{_RESET}  {sev_tag}  {message}"
        )
    return f"  {ts}  {svc:<15}  [{severity:<5}]  {message}"


def _filter_severity_local(entries: list[dict], min_severity: str | None) -> list[dict]:
    """Client-side fallback when server filter is bypassed (e.g. smoke tests)."""
    if not min_severity:
        return entries
    floor = _SEVERITY_RANK.get(min_severity.upper(), 0)
    return [
        e for e in entries
        if _SEVERITY_RANK.get((e.get("severity") or "INFO").upper(), 1) >= floor
    ]


def _dedup_key(entry: dict) -> tuple[str, str]:
    return (entry.get("timestamp") or "", entry.get("message") or "")


def _tail_loop(
    fetch_fn,
    interval: float,
    printer,
    already_seen: set,
):
    """Generic polling loop for --follow mode.

    ``fetch_fn()`` returns a fresh list of entries (newest-last).
    """
    try:
        while True:
            try:
                entries = fetch_fn()
            except RailwayAPIError as exc:
                click.echo(f"  ⚠ {exc}", err=True)
                time.sleep(max(interval, 2.0))
                continue
            for entry in entries:
                key = _dedup_key(entry)
                if key in already_seen:
                    continue
                already_seen.add(key)
                printer(entry)
            # Prevent unbounded memory growth on long follows
            if len(already_seen) > 5000:
                # Keep only the latest 2500 keys (set can't slice; rebuild)
                already_seen.clear()
                for e in entries[-2500:]:
                    already_seen.add(_dedup_key(e))
            time.sleep(interval)
    except (KeyboardInterrupt, EOFError):
        click.echo("", err=True)


# ---------------------------------------------------------------------------
# Click group
# ---------------------------------------------------------------------------

@click.group("logs")
def logs_group():
    """Stream and retrieve Railway logs."""


# ---------------------------------------------------------------------------
# logs deployment
# ---------------------------------------------------------------------------

@logs_group.command("deployment")
@click.argument("deployment_id")
@click.option("--lines", default=100, show_default=True, help="Number of historical lines.")
@click.option("--build", "build_logs", is_flag=True, help="Show build logs instead of runtime logs.")
@click.option("--filter", "filter_text", default=None, help="Railway filter query (e.g. '@level:error AND failed').")
@click.option("--severity", type=click.Choice(["debug", "info", "warn", "error"], case_sensitive=False), default=None, help="Minimum severity level.")
@click.option("--since", "since", default=None, help="Relative ('30m', '2h', '1d') or ISO-8601 start time.")
@click.option("--until", "until", default=None, help="Relative or ISO-8601 end time.")
@click.option("--follow", "-f", is_flag=True, help="Stream new logs via polling.")
@click.option("--interval", default=1.5, show_default=True, help="Poll interval (s) in --follow mode.")
@click.option("--no-color", is_flag=True, help="Disable ANSI colors.")
@click.option("--raw", is_flag=True, help="Print only message text (no timestamp/severity).")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def logs_deployment(
    ctx: click.Context,
    deployment_id: str,
    lines: int,
    build_logs: bool,
    filter_text: str | None,
    severity: str | None,
    since: str | None,
    until: str | None,
    follow: bool,
    interval: float,
    no_color: bool,
    raw: bool,
    as_json: bool,
):
    """Show logs for a deployment (runtime or build)."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    combined_filter = _compose_filter(filter_text, severity)
    start = _parse_time(since)
    end = _parse_time(until)

    fetcher = backend.build_logs if build_logs else backend.deployment_logs

    def fetch(limit: int, start_date: str | None = start, end_date: str | None = end):
        return fetcher(
            deployment_id,
            limit=limit,
            filter_text=combined_filter,
            start_date=start_date,
            end_date=end_date,
        )

    try:
        entries = fetch(lines)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps(entries, indent=2))
        return

    log_type = "Build" if build_logs else "Runtime"
    use_color = not no_color and sys.stdout.isatty()

    if not entries and not follow:
        skin.info("No log entries found.")
        return

    if entries:
        skin.section(f"{log_type} Logs — {deployment_id}")
        for entry in entries:
            click.echo(_fmt_log_line(entry, color=use_color, raw=raw))

    if follow:
        seen = {_dedup_key(e) for e in entries}
        last_ts = entries[-1]["timestamp"] if entries else None

        def printer(e):
            key = _dedup_key(e)
            if key in seen:
                return
            seen.add(key)
            click.echo(_fmt_log_line(e, color=use_color, raw=raw))

        if railway_stream.ws_available():
            skin.info("Streaming logs (WebSocket)... (Ctrl-C to stop)")
            try:
                railway_stream.stream_deployment_logs(
                    token=backend._token,
                    deployment_id=deployment_id,
                    on_entry=printer,
                    filter_text=combined_filter,
                    limit=0,
                    build=build_logs,
                )
            except railway_stream.StreamError as exc:
                skin.error(f"Stream failed: {exc}")
            except KeyboardInterrupt:
                click.echo("", err=True)
        else:
            skin.info("Polling logs (install websocket-client for streaming)... (Ctrl-C to stop)")

            def poll():
                start_from = last_ts or _parse_time("30s")
                return fetch(200, start_date=start_from, end_date=None)

            _tail_loop(
                poll,
                interval,
                lambda e: click.echo(_fmt_log_line(e, color=use_color, raw=raw)),
                seen,
            )


# ---------------------------------------------------------------------------
# logs service
# ---------------------------------------------------------------------------

@logs_group.command("service")
@click.argument("service_id")
@click.option("--env", "environment_id", required=True, help="Environment ID.")
@click.option("--lines", default=100, show_default=True, help="Number of historical lines.")
@click.option("--filter", "filter_text", default=None, help="Railway filter query.")
@click.option("--severity", type=click.Choice(["debug", "info", "warn", "error"], case_sensitive=False), default=None)
@click.option("--since", default=None, help="Relative ('30m') or ISO-8601 start time.")
@click.option("--until", default=None, help="Relative or ISO-8601 end time.")
@click.option("--follow", "-f", is_flag=True, help="Stream new logs via polling.")
@click.option("--interval", default=1.5, show_default=True)
@click.option("--no-color", is_flag=True)
@click.option("--raw", is_flag=True)
@click.option("--json", "as_json", is_flag=True)
@click.pass_context
def logs_service(
    ctx: click.Context,
    service_id: str,
    environment_id: str,
    lines: int,
    filter_text: str | None,
    severity: str | None,
    since: str | None,
    until: str | None,
    follow: bool,
    interval: float,
    no_color: bool,
    raw: bool,
    as_json: bool,
):
    """Show recent logs for a service (fetches latest deployment logs)."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        deployments = backend.deployments_list(service_id, environment_id)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if not deployments:
        skin.info("No deployments found for this service.")
        return

    latest_dep = deployments[0]
    deployment_id = latest_dep.get("id", "")
    combined_filter = _compose_filter(filter_text, severity)
    start = _parse_time(since)
    end = _parse_time(until)

    def fetch(limit: int, start_date: str | None = start, end_date: str | None = end):
        return backend.deployment_logs(
            deployment_id,
            limit=limit,
            filter_text=combined_filter,
            start_date=start_date,
            end_date=end_date,
        )

    try:
        entries = fetch(lines)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps(entries, indent=2))
        return

    use_color = not no_color and sys.stdout.isatty()
    if entries:
        skin.section(f"Service Logs — {service_id} (deployment {deployment_id})")
        for entry in entries:
            click.echo(_fmt_log_line(entry, color=use_color, raw=raw))
    elif not follow:
        skin.info("No log entries found.")
        return

    if follow:
        seen = {_dedup_key(e) for e in entries}
        last_ts = entries[-1]["timestamp"] if entries else None

        def printer(e):
            key = _dedup_key(e)
            if key in seen:
                return
            seen.add(key)
            click.echo(_fmt_log_line(e, color=use_color, raw=raw))

        if railway_stream.ws_available():
            skin.info("Streaming logs (WebSocket)... (Ctrl-C to stop)")
            try:
                railway_stream.stream_deployment_logs(
                    token=backend._token,
                    deployment_id=deployment_id,
                    on_entry=printer,
                    filter_text=combined_filter,
                    limit=0,
                    build=False,
                )
            except railway_stream.StreamError as exc:
                skin.error(f"Stream failed: {exc}")
            except KeyboardInterrupt:
                click.echo("", err=True)
        else:
            skin.info("Polling logs (install websocket-client for streaming)... (Ctrl-C to stop)")

            def poll():
                start_from = last_ts or _parse_time("30s")
                return fetch(200, start_date=start_from, end_date=None)

            _tail_loop(
                poll,
                interval,
                lambda e: click.echo(_fmt_log_line(e, color=use_color, raw=raw)),
                seen,
            )


# ---------------------------------------------------------------------------
# logs http
# ---------------------------------------------------------------------------

@logs_group.command("http")
@click.argument("deployment_id")
@click.option("--lines", default=100, show_default=True)
@click.option("--filter", "filter_text", default=None, help="Railway filter query (e.g. '@httpStatus:>=500').")
@click.option("--since", default=None)
@click.option("--until", default=None)
@click.option("--follow", "-f", is_flag=True)
@click.option("--interval", default=1.5, show_default=True)
@click.option("--no-color", is_flag=True)
@click.option("--json", "as_json", is_flag=True)
@click.pass_context
def logs_http(
    ctx: click.Context,
    deployment_id: str,
    lines: int,
    filter_text: str | None,
    since: str | None,
    until: str | None,
    follow: bool,
    interval: float,
    no_color: bool,
    as_json: bool,
):
    """Show HTTP request logs for a deployment."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    start = _parse_time(since)
    end = _parse_time(until)

    def fetch(limit: int, start_date: str | None = start, end_date: str | None = end):
        return backend.http_logs(
            deployment_id,
            limit=limit,
            filter_text=filter_text,
            start_date=start_date,
            end_date=end_date,
        )

    try:
        entries = fetch(lines)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps(entries, indent=2))
        return

    if not entries and not follow:
        skin.info("No HTTP log entries found.")
        return

    def render_row(e: dict) -> list[str]:
        return [
            (e.get("timestamp") or "")[:19],
            e.get("method") or "",
            (e.get("path") or "")[:40],
            str(e.get("httpStatus", "")),
            str(e.get("totalDuration", "")),
            e.get("srcIp") or "",
        ]

    if entries:
        skin.section(f"HTTP Logs — {deployment_id}")
        skin.table(
            ["Timestamp", "Method", "Path", "Status", "Duration(ms)", "Source IP"],
            [render_row(e) for e in entries],
        )

    if follow:
        seen = {_dedup_key(e) for e in entries}
        last_ts = entries[-1]["timestamp"] if entries else None

        def printer(e):
            key = _dedup_key(e)
            if key in seen:
                return
            seen.add(key)
            row = render_row(e)
            click.echo("  " + " │ ".join(row))

        if railway_stream.ws_available():
            skin.info("Streaming HTTP logs (WebSocket)... (Ctrl-C to stop)")
            try:
                railway_stream.stream_http_logs(
                    token=backend._token,
                    deployment_id=deployment_id,
                    on_entry=printer,
                    filter_text=filter_text,
                    before_limit=0,
                )
            except railway_stream.StreamError as exc:
                skin.error(f"Stream failed: {exc}")
            except KeyboardInterrupt:
                click.echo("", err=True)
        else:
            skin.info("Polling HTTP logs... (Ctrl-C to stop)")

            def poll():
                start_from = last_ts or _parse_time("30s")
                return fetch(200, start_date=start_from, end_date=None)

            _tail_loop(poll, interval, printer, seen)


# ---------------------------------------------------------------------------
# logs environment
# ---------------------------------------------------------------------------

@logs_group.command("environment")
@click.option("--env", "environment_id", required=True, help="Environment ID.")
@click.option("--lines", default=100, show_default=True, help="Historical lines (beforeLimit).")
@click.option("--filter", "filter_text", default=None, help="Railway filter (e.g. '@service:<id> AND @level:error').")
@click.option("--severity", type=click.Choice(["debug", "info", "warn", "error"], case_sensitive=False), default=None)
@click.option("--service", "service_id", default=None, help="Shortcut for '@service:<id>' in the filter.")
@click.option("--since", default=None, help="Relative ('30m') or ISO-8601; maps to afterDate.")
@click.option("--follow", "-f", is_flag=True, help="Stream new env logs via polling.")
@click.option("--interval", default=1.5, show_default=True)
@click.option("--no-color", is_flag=True)
@click.option("--raw", is_flag=True)
@click.option("--json", "as_json", is_flag=True)
@click.pass_context
def logs_environment(
    ctx: click.Context,
    environment_id: str,
    lines: int,
    filter_text: str | None,
    severity: str | None,
    service_id: str | None,
    since: str | None,
    follow: bool,
    interval: float,
    no_color: bool,
    raw: bool,
    as_json: bool,
):
    """Show logs from all services in an environment."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]

    # Compose full filter (filter + severity + service shortcut)
    parts: list[str] = []
    if filter_text:
        parts.append(filter_text)
    if severity:
        parts.append(f"@level:{severity.lower()}")
    if service_id:
        parts.append(f"@service:{service_id}")
    combined_filter = " AND ".join(f"({p})" for p in parts) if len(parts) > 1 else (parts[0] if parts else None)

    after = _parse_time(since)

    def fetch(before_limit: int, after_date: str | None = after):
        return backend.environment_logs(
            environment_id,
            filter_text=combined_filter,
            before_limit=before_limit,
            after_date=after_date,
        )

    try:
        entries = fetch(lines)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps(entries, indent=2))
        return

    use_color = not no_color and sys.stdout.isatty()

    if entries:
        skin.section(f"Environment Logs — {environment_id}")
        for entry in entries:
            click.echo(_fmt_env_line(entry, color=use_color, raw=raw))
    elif not follow:
        skin.info("No log entries found.")
        return

    if follow:
        seen = {_dedup_key(e) for e in entries}
        last_ts = entries[-1]["timestamp"] if entries else None

        def printer(e):
            key = _dedup_key(e)
            if key in seen:
                return
            seen.add(key)
            click.echo(_fmt_env_line(e, color=use_color, raw=raw))

        if railway_stream.ws_available():
            skin.info("Streaming env logs (WebSocket)... (Ctrl-C to stop)")
            try:
                railway_stream.stream_environment_logs(
                    token=backend._token,
                    environment_id=environment_id,
                    on_entry=printer,
                    filter_text=combined_filter,
                    before_limit=0,
                )
            except railway_stream.StreamError as exc:
                skin.error(f"Stream failed: {exc}")
            except KeyboardInterrupt:
                click.echo("", err=True)
        else:
            skin.info("Polling env logs... (Ctrl-C to stop)")

            def poll():
                after_from = last_ts or _parse_time("30s")
                return backend.environment_logs(
                    environment_id,
                    filter_text=combined_filter,
                    after_date=after_from,
                    after_limit=200,
                    anchor_date=after_from,
                )

            _tail_loop(
                poll,
                interval,
                lambda e: click.echo(_fmt_env_line(e, color=use_color, raw=raw)),
                seen,
            )
