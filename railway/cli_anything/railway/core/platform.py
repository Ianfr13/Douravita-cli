"""Platform commands for cli-anything-railway."""

from __future__ import annotations

import json
import sys

import click

from cli_anything.railway.utils.railway_backend import RailwayBackend, RailwayAPIError


@click.group("platform")
def platform_group():
    """Railway platform status and metadata."""


@platform_group.command("status")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def platform_status(ctx: click.Context, as_json: bool):
    """Check Railway platform status."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        status = backend.platform_status()
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps(status, indent=2))
        return

    is_stable = status.get("isStable", False)
    incident = status.get("incident")

    if is_stable:
        skin.success("Railway platform is stable.")
    else:
        skin.warning("Railway platform has issues.")

    if incident:
        skin.status_block(
            {
                "ID": incident.get("id", ""),
                "Status": incident.get("status", ""),
                "Message": incident.get("message", ""),
                "URL": incident.get("url", ""),
            },
            title="Active Incident",
        )


@platform_group.command("regions")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def platform_regions(ctx: click.Context, as_json: bool):
    """List available deployment regions."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        regions = backend.regions()
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps(regions, indent=2))
        return

    if not regions:
        skin.info("No regions returned.")
        return

    skin.table(
        ["Name", "Region", "Country", "Location", "Metal"],
        [
            [
                r.get("name", ""),
                r.get("region") or "",
                r.get("country", ""),
                r.get("location", ""),
                "yes" if r.get("railwayMetal") else "",
            ]
            for r in regions
        ],
    )


@platform_group.command("me")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def platform_me(ctx: click.Context, as_json: bool):
    """Show current authenticated user info."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        me = backend.me()
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps(me, indent=2))
        return

    if not me:
        skin.error("Could not retrieve user info.")
        sys.exit(1)

    skin.status_block(
        {
            "ID": me.get("id", ""),
            "Name": me.get("name", ""),
            "Email": me.get("email", ""),
        },
        title="Current User",
    )

    workspaces = me.get("workspaces") or []
    if workspaces:
        skin.section("Workspaces")
        skin.table(
            ["ID", "Name"],
            [[w.get("id", ""), w.get("name", "")] for w in workspaces],
        )
