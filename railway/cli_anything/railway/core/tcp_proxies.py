"""TCP Proxies commands for cli-anything-railway."""

from __future__ import annotations

import json
import sys

import click

from cli_anything.railway.utils.railway_backend import RailwayBackend, RailwayAPIError


@click.group("tcp-proxies")
def tcp_proxies_group():
    """Manage Railway TCP proxies."""


@tcp_proxies_group.command("list")
@click.option("--service", "service_id", required=True, help="Service ID.")
@click.option("--env", "environment_id", required=True, help="Environment ID.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def tcp_proxies_list(
    ctx: click.Context, service_id: str, environment_id: str, as_json: bool
):
    """List TCP proxies for a service."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        proxies = backend.tcp_proxies_list(service_id, environment_id)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps(proxies, indent=2))
        return

    if not proxies:
        skin.info("No TCP proxies found.")
        return

    skin.table(
        ["ID", "App Port", "Proxy Port", "Domain"],
        [
            [
                p.get("id", ""),
                str(p.get("applicationPort", "")),
                str(p.get("proxyPort", "")),
                p.get("domain") or "",
            ]
            for p in proxies
        ],
    )


@tcp_proxies_group.command("create")
@click.option("--service", "service_id", required=True, help="Service ID.")
@click.option("--env", "environment_id", required=True, help="Environment ID.")
@click.option("--port", "application_port", required=True, type=int, help="Application port to proxy.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def tcp_proxies_create(
    ctx: click.Context,
    service_id: str,
    environment_id: str,
    application_port: int,
    as_json: bool,
):
    """Create a TCP proxy for a service port."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        result = backend.tcp_proxy_create(service_id, environment_id, application_port)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps(result, indent=2))
        return

    skin.success(
        f"TCP proxy created: {result.get('domain')} "
        f"proxy-port {result.get('proxyPort')} → app-port {application_port} "
        f"(id: {result.get('id')})"
    )


@tcp_proxies_group.command("delete")
@click.argument("proxy_id")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def tcp_proxies_delete(ctx: click.Context, proxy_id: str, as_json: bool):
    """Delete a TCP proxy by ID."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        result = backend.tcp_proxy_delete(proxy_id)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps({"deleted": result, "id": proxy_id}, indent=2))
        return

    if result:
        skin.success(f"TCP proxy {proxy_id} deleted.")
    else:
        skin.warning(f"TCP proxy delete returned false for {proxy_id}.")
