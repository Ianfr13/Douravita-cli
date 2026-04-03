"""Metrics commands for cli-anything-railway."""

from __future__ import annotations

import json
import sys

import click

from cli_anything.railway.utils.railway_backend import RailwayBackend, RailwayAPIError


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

    # Build a summary from the latest value per measurement
    summary = {}
    for m in metrics:
        name = m.get("measurement", "?")
        values = m.get("values") or []
        if values:
            last = values[-1]
            val = last.get("value")
            if name == "CPU_USAGE":
                summary["CPU"] = f"{val:.4f}%" if val is not None else "N/A"
            elif name == "MEMORY_USAGE_GB":
                summary["Memory"] = f"{val:.3f} GB" if val is not None else "N/A"
            elif name == "NETWORK_RX_GB":
                summary["Network RX"] = f"{val:.4f} GB" if val is not None else "N/A"
            elif name == "NETWORK_TX_GB":
                summary["Network TX"] = f"{val:.4f} GB" if val is not None else "N/A"
            else:
                summary[name] = f"{val}" if val is not None else "N/A"

    skin.status_block(summary, title=f"Metrics — {service_id}")
