"""Variables commands for cli-anything-railway."""

from __future__ import annotations

import json
import sys

import click

from cli_anything.railway.utils.railway_backend import RailwayBackend, RailwayAPIError


@click.group("variables")
def variables_group():
    """Manage Railway environment variables."""


@variables_group.command("list")
@click.option("--project", "project_id", required=True, help="Project ID.")
@click.option("--env", "environment_id", required=True, help="Environment ID.")
@click.option("--service", "service_id", default=None, help="Service ID (optional).")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def variables_list(
    ctx: click.Context,
    project_id: str,
    environment_id: str,
    service_id: str | None,
    as_json: bool,
):
    """List environment variables."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        variables = backend.variables_list(project_id, environment_id, service_id)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps(variables, indent=2))
        return

    if not variables:
        skin.info("No variables found.")
        return

    # variables is a dict of name -> value
    if isinstance(variables, dict):
        skin.table(
            ["Key", "Value"],
            [[k, str(v)] for k, v in variables.items()],
        )
    else:
        skin.info(str(variables))


@variables_group.command("set")
@click.argument("key")
@click.argument("value")
@click.option("--project", "project_id", required=True, help="Project ID.")
@click.option("--env", "environment_id", required=True, help="Environment ID.")
@click.option("--service", "service_id", default=None, help="Service ID (optional).")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def variables_set(
    ctx: click.Context,
    key: str,
    value: str,
    project_id: str,
    environment_id: str,
    service_id: str | None,
    as_json: bool,
):
    """Set (upsert) an environment variable."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        result = backend.variable_upsert(
            project_id, environment_id, key, value, service_id
        )
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps({"set": result, "key": key}, indent=2))
        return

    if result:
        skin.success(f"Variable '{key}' set successfully.")
    else:
        skin.warning(f"Variable '{key}' upsert returned false.")


@variables_group.command("delete")
@click.argument("key")
@click.option("--project", "project_id", required=True, help="Project ID.")
@click.option("--env", "environment_id", required=True, help="Environment ID.")
@click.option("--service", "service_id", default=None, help="Service ID (optional).")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def variables_delete(
    ctx: click.Context,
    key: str,
    project_id: str,
    environment_id: str,
    service_id: str | None,
    as_json: bool,
):
    """Delete an environment variable."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        result = backend.variable_delete(project_id, environment_id, key, service_id)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps({"deleted": result, "key": key}, indent=2))
        return

    if result:
        skin.success(f"Variable '{key}' deleted successfully.")
    else:
        skin.warning(f"Variable '{key}' delete returned false.")
