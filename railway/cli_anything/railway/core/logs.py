"""Logs commands for cli-anything-railway."""

from __future__ import annotations

import json
import sys

import click

from cli_anything.railway.utils.railway_backend import RailwayBackend, RailwayAPIError

_SEVERITY_COLORS = {
    "ERROR": "\033[38;5;196m",
    "WARN":  "\033[38;5;220m",
    "WARNING": "\033[38;5;220m",
    "INFO":  "\033[38;5;75m",
    "DEBUG": "\033[38;5;245m",
}
_RESET = "\033[0m"


def _fmt_log_line(entry: dict) -> str:
    ts = (entry.get("timestamp") or "")[:19]
    severity = (entry.get("severity") or "INFO").upper()
    message = entry.get("message") or ""
    color = _SEVERITY_COLORS.get(severity, "")
    sev_tag = f"{color}[{severity:<5}]{_RESET}" if color else f"[{severity:<5}]"
    ts_tag = f"\033[38;5;245m{ts}{_RESET}" if ts else ""
    return f"  {ts_tag}  {sev_tag}  {message}"


@click.group("logs")
def logs_group():
    """Stream and retrieve Railway logs."""


@logs_group.command("deployment")
@click.argument("deployment_id")
@click.option("--lines", default=100, show_default=True, help="Number of log lines.")
@click.option("--build", "build_logs", is_flag=True, help="Show build logs instead of runtime logs.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def logs_deployment(
    ctx: click.Context,
    deployment_id: str,
    lines: int,
    build_logs: bool,
    as_json: bool,
):
    """Show logs for a deployment (runtime or build)."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        if build_logs:
            entries = backend.build_logs(deployment_id, limit=lines)
        else:
            entries = backend.deployment_logs(deployment_id, limit=lines)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps(entries, indent=2))
        return

    if not entries:
        skin.info("No log entries found.")
        return

    log_type = "Build" if build_logs else "Runtime"
    skin.section(f"{log_type} Logs — {deployment_id}")
    for entry in entries:
        click.echo(_fmt_log_line(entry))


@logs_group.command("service")
@click.argument("service_id")
@click.option("--env", "environment_id", required=True, help="Environment ID.")
@click.option("--lines", default=100, show_default=True, help="Number of log lines.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def logs_service(
    ctx: click.Context,
    service_id: str,
    environment_id: str,
    lines: int,
    as_json: bool,
):
    """Show recent logs for a service (fetches latest deployment logs)."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    # Retrieve the most recent deployment for the service then fetch its logs.
    try:
        deployments = backend.deployments_list(service_id, environment_id)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if not deployments:
        skin.info("No deployments found for this service.")
        return

    # deployments are returned newest-first by Railway
    latest_dep = deployments[0]
    deployment_id = latest_dep.get("id", "")

    try:
        entries = backend.deployment_logs(deployment_id, limit=lines)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps(entries, indent=2))
        return

    if not entries:
        skin.info("No log entries found.")
        return

    skin.section(f"Service Logs — {service_id} (deployment {deployment_id})")
    for entry in entries:
        click.echo(_fmt_log_line(entry))


@logs_group.command("http")
@click.argument("deployment_id")
@click.option("--lines", default=100, show_default=True, help="Number of log lines.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def logs_http(
    ctx: click.Context, deployment_id: str, lines: int, as_json: bool
):
    """Show HTTP request logs for a deployment."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        entries = backend.http_logs(deployment_id, limit=lines)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps(entries, indent=2))
        return

    if not entries:
        skin.info("No HTTP log entries found.")
        return

    skin.section(f"HTTP Logs — {deployment_id}")
    skin.table(
        ["Timestamp", "Method", "Path", "Status", "Duration", "Source IP"],
        [
            [
                (e.get("timestamp") or "")[:19],
                e.get("method", ""),
                e.get("path", ""),
                str(e.get("httpStatus", "")),
                str(e.get("totalDuration", "")),
                e.get("srcIp") or "",
            ]
            for e in entries
        ],
    )


@logs_group.command("environment")
@click.option("--env", "environment_id", required=True, help="Environment ID.")
@click.option("--project", "project_id", required=True, help="Project ID.")
@click.option("--lines", default=100, show_default=True, help="Number of log lines.")
@click.option("--filter", "filter_text", default=None, help="Filter logs by text.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def logs_environment(
    ctx: click.Context,
    environment_id: str,
    project_id: str,
    lines: int,
    filter_text: str | None,
    as_json: bool,
):
    """Show logs from all services in an environment."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        entries = backend.environment_logs(
            environment_id, project_id, limit=lines, filter_text=filter_text
        )
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps(entries, indent=2))
        return

    if not entries:
        skin.info("No log entries found.")
        return

    skin.section(f"Environment Logs — {environment_id}")
    for entry in entries:
        svc = entry.get("serviceName") or "unknown"
        ts = (entry.get("timestamp") or "")[:19]
        severity = (entry.get("severity") or "INFO").upper()
        message = entry.get("message") or ""
        color = _SEVERITY_COLORS.get(severity, "")
        sev_tag = f"{color}[{severity:<5}]{_RESET}" if color else f"[{severity:<5}]"
        click.echo(f"  \033[38;5;245m{ts}{_RESET}  \033[38;5;141m{svc:<15}{_RESET}  {sev_tag}  {message}")
