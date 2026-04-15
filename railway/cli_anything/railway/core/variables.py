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


@variables_group.command("bulk-set")
@click.argument("pairs", nargs=-1, required=True)
@click.option("--project", "project_id", required=True, help="Project ID.")
@click.option("--env", "environment_id", required=True, help="Environment ID.")
@click.option("--service", "service_id", default=None, help="Service ID (optional).")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def variables_bulk_set(
    ctx: click.Context,
    pairs: tuple[str, ...],
    project_id: str,
    environment_id: str,
    service_id: str | None,
    as_json: bool,
):
    """Set multiple variables at once.

    PAIRS are KEY=VALUE arguments, e.g.: variables bulk-set FOO=bar BAZ=qux
    """
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]

    variables: dict[str, str] = {}
    for pair in pairs:
        if "=" not in pair:
            skin.error(f"Invalid pair '{pair}' — expected KEY=VALUE format.")
            sys.exit(1)
        key, value = pair.split("=", 1)
        variables[key] = value

    try:
        result = backend.variable_collection_upsert(
            project_id, environment_id, variables, service_id
        )
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps({"set": result, "count": len(variables), "keys": list(variables.keys())}, indent=2))
        return

    if result:
        skin.success(f"{len(variables)} variable(s) set successfully: {', '.join(variables.keys())}")
    else:
        skin.warning("Bulk upsert returned false.")


@variables_group.command("resolved")
@click.option("--project", "project_id", required=True, help="Project ID.")
@click.option("--env", "environment_id", required=True, help="Environment ID.")
@click.option("--service", "service_id", required=True, help="Service ID.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def variables_resolved(
    ctx: click.Context,
    project_id: str,
    environment_id: str,
    service_id: str,
    as_json: bool,
):
    """Show fully resolved variables as they appear at deploy time."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        variables = backend.variables_resolved(project_id, environment_id, service_id)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps(variables, indent=2))
        return

    if not variables:
        skin.info("No resolved variables found.")
        return

    if isinstance(variables, dict):
        skin.table(
            ["Key", "Resolved Value"],
            [[k, str(v)] for k, v in variables.items()],
        )
    else:
        skin.info(str(variables))
