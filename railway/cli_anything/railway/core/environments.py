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


@environments_group.command("delete")
@click.argument("environment_id")
@click.option("--yes", is_flag=True, help="Skip confirmation.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def environments_delete(ctx: click.Context, environment_id: str, yes: bool, as_json: bool):
    """Delete an environment (irreversible)."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]

    if not yes:
        skin.warning(f"This will permanently delete environment {environment_id}.")
        if not click.confirm("Continue?"):
            skin.info("Aborted.")
            return

    try:
        result = backend.environment_delete(environment_id)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps({"deleted": result, "environmentId": environment_id}, indent=2))
        return

    if result:
        skin.success(f"Environment {environment_id} deleted.")
    else:
        skin.warning("Delete returned false — check Railway dashboard.")


@environments_group.command("rename")
@click.argument("environment_id")
@click.argument("name")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def environments_rename(ctx: click.Context, environment_id: str, name: str, as_json: bool):
    """Rename an environment."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        result = backend.environment_rename(environment_id, name)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps({"renamed": result, "environmentId": environment_id, "name": name}, indent=2))
        return

    if result:
        skin.success(f"Environment {environment_id} renamed to '{name}'.")
    else:
        skin.warning("Rename returned false — check Railway dashboard.")
