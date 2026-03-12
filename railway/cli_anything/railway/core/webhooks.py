"""Webhooks commands for cli-anything-railway."""

from __future__ import annotations

import json
import sys

import click

from cli_anything.railway.utils.railway_backend import RailwayBackend, RailwayAPIError


@click.group("webhooks")
def webhooks_group():
    """Manage Railway project webhooks."""


@webhooks_group.command("list")
@click.option("--project", "project_id", required=True, help="Project ID.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def webhooks_list(ctx: click.Context, project_id: str, as_json: bool):
    """List webhooks for a project."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        webhooks = backend.webhooks_list(project_id)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps(webhooks, indent=2))
        return

    if not webhooks:
        skin.info("No webhooks found.")
        return

    skin.table(
        ["ID", "URL"],
        [[w.get("id", ""), w.get("url", "")] for w in webhooks],
    )


@webhooks_group.command("create")
@click.argument("url")
@click.option("--project", "project_id", required=True, help="Project ID.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def webhooks_create(ctx: click.Context, url: str, project_id: str, as_json: bool):
    """Create a webhook for a project."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        result = backend.webhook_create(url, project_id)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps(result, indent=2))
        return

    skin.success(f"Webhook created: {result.get('url')} (id: {result.get('id')})")


@webhooks_group.command("delete")
@click.argument("webhook_id")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def webhooks_delete(ctx: click.Context, webhook_id: str, as_json: bool):
    """Delete a webhook by ID."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        result = backend.webhook_delete(webhook_id)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps({"deleted": result, "id": webhook_id}, indent=2))
        return

    if result:
        skin.success(f"Webhook {webhook_id} deleted.")
    else:
        skin.warning(f"Webhook delete returned false for {webhook_id}.")
