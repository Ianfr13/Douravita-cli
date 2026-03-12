"""Metrics commands for cli-anything-railway."""

from __future__ import annotations

import json
import sys

import click

from cli_anything.railway.utils.railway_backend import RailwayBackend, RailwayAPIError


def _bytes_human(value) -> str:
    """Format a byte count as a human-readable string."""
    if value is None:
        return "N/A"
    try:
        n = float(value)
    except (TypeError, ValueError):
        return str(value)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


@click.group("metrics")
def metrics_group():
    """View Railway service metrics."""


@metrics_group.command("service")
@click.argument("service_id")
@click.option("--env", "environment_id", required=True, help="Environment ID.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def metrics_service(
    ctx: click.Context, service_id: str, environment_id: str, as_json: bool
):
    """Show CPU, memory, and network metrics for a service."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        metrics = backend.service_metrics(service_id, environment_id)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps(metrics, indent=2))
        return

    if not metrics:
        skin.info("No metrics available.")
        return

    cpu = metrics.get("cpuPercentage")
    cpu_str = f"{cpu:.2f}%" if cpu is not None else "N/A"

    skin.status_block(
        {
            "CPU":        cpu_str,
            "Memory":     _bytes_human(metrics.get("memoryUsageBytes")),
            "Network RX": _bytes_human(metrics.get("networkRxBytes")),
            "Network TX": _bytes_human(metrics.get("networkTxBytes")),
        },
        title=f"Metrics — {service_id}",
    )
