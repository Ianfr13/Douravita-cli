"""Private networking commands for cli-anything-railway."""

from __future__ import annotations

import json
import sys

import click

from cli_anything.railway.utils.railway_backend import RailwayBackend, RailwayAPIError


@click.group("networking")
def networking_group():
    """View Railway private network endpoints."""


@networking_group.command("list")
@click.option("--project", "project_id", required=True, help="Project ID.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def networking_list(ctx: click.Context, project_id: str, as_json: bool):
    """List private network endpoints (internal domains) in a project."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        endpoints = backend.networking_list(project_id)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps(endpoints, indent=2))
        return

    if not endpoints:
        skin.info("No private network endpoints found.")
        return

    skin.table(
        ["Service", "Internal Domain", "Domain ID"],
        [
            [
                e.get("serviceName", ""),
                e.get("internalDomain", ""),
                e.get("id", ""),
            ]
            for e in endpoints
        ],
    )
