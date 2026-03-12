"""Templates commands for cli-anything-railway."""

from __future__ import annotations

import json
import sys

import click

from cli_anything.railway.utils.railway_backend import RailwayBackend, RailwayAPIError


@click.group("templates")
def templates_group():
    """Browse and deploy Railway templates."""


@templates_group.command("list")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def templates_list(ctx: click.Context, as_json: bool):
    """List available Railway templates."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        templates = backend.templates_list()
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps(templates, indent=2))
        return

    if not templates:
        skin.info("No templates found.")
        return

    skin.table(
        ["Code", "Name", "Description"],
        [
            [
                t.get("code", ""),
                t.get("name", ""),
                (t.get("description") or "")[:60],
            ]
            for t in templates
        ],
    )


@templates_group.command("deploy")
@click.argument("code")
@click.option("--project", "project_id", required=True, help="Target project ID.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def templates_deploy(
    ctx: click.Context, code: str, project_id: str, as_json: bool
):
    """Deploy a template into a project."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        result = backend.template_deploy(code, project_id)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps(result, indent=2))
        return

    skin.success(
        f"Template '{code}' deployed to project {result.get('projectId', project_id)}."
    )
