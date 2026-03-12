"""Environments commands for cli-anything-railway."""

from __future__ import annotations

import json
import sys

import click

from cli_anything.railway.utils.railway_backend import RailwayBackend, RailwayAPIError


@click.group("environments")
def environments_group():
    """Manage Railway environments."""


@environments_group.command("list")
@click.option("--project", "project_id", required=True, help="Project ID.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def environments_list(ctx: click.Context, project_id: str, as_json: bool):
    """List environments in a project."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        environments = backend.environments_list(project_id)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps(environments, indent=2))
        return

    if not environments:
        skin.info("No environments found.")
        return

    skin.table(
        ["ID", "Name"],
        [[e.get("id", ""), e.get("name", "")] for e in environments],
    )


@environments_group.command("create")
@click.argument("name")
@click.option("--project", "project_id", required=True, help="Project ID.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def environments_create(
    ctx: click.Context, name: str, project_id: str, as_json: bool
):
    """Create a new environment in a project."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        env = backend.environment_create(name, project_id)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps(env, indent=2))
        return

    skin.success(
        f"Environment created: {env.get('name')} ({env.get('id')})"
    )
