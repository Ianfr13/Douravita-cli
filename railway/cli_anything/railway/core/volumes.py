"""Volumes commands for cli-anything-railway."""

from __future__ import annotations

import json
import sys

import click

from cli_anything.railway.utils.railway_backend import RailwayBackend, RailwayAPIError


@click.group("volumes")
def volumes_group():
    """Manage Railway persistent volumes."""


@volumes_group.command("list")
@click.option("--project", "project_id", required=True, help="Project ID.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def volumes_list(ctx: click.Context, project_id: str, as_json: bool):
    """List volumes in a project."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        volumes = backend.volumes_list(project_id)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps(volumes, indent=2))
        return

    if not volumes:
        skin.info("No volumes found.")
        return

    skin.table(
        ["ID", "Name", "Created"],
        [
            [v.get("id", ""), v.get("name", ""), (v.get("createdAt") or "")[:19]]
            for v in volumes
        ],
    )


@volumes_group.command("create")
@click.argument("name")
@click.option("--project", "project_id", required=True, help="Project ID.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def volumes_create(ctx: click.Context, name: str, project_id: str, as_json: bool):
    """Create a volume in a project."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        volume = backend.volume_create(name, project_id)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps(volume, indent=2))
        return

    skin.success(f"Volume created: {volume.get('name')} (id: {volume.get('id')})")


@volumes_group.command("delete")
@click.argument("volume_id")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def volumes_delete(ctx: click.Context, volume_id: str, as_json: bool):
    """Delete a volume by ID."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        result = backend.volume_delete(volume_id)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps({"deleted": result, "id": volume_id}, indent=2))
        return

    if result:
        skin.success(f"Volume {volume_id} deleted.")
    else:
        skin.warning(f"Volume delete returned false for {volume_id}.")
