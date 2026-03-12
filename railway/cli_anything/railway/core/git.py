"""Git integration commands for cli-anything-railway."""

from __future__ import annotations

import json
import sys

import click

from cli_anything.railway.utils.railway_backend import RailwayBackend, RailwayAPIError


@click.group("git")
def git_group():
    """Manage GitHub/Git repository connections for Railway services."""


@git_group.command("connect")
@click.argument("service_id")
@click.argument("repo")
@click.argument("branch")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def git_connect(
    ctx: click.Context, service_id: str, repo: str, branch: str, as_json: bool
):
    """Connect a GitHub repository to a service.

    REPO should be in the form owner/repo-name.
    """
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        result = backend.git_connect(service_id, repo, branch)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps({"connected": result}, indent=2))
        return

    if result:
        skin.success(f"Service {service_id} connected to {repo}@{branch}.")
    else:
        skin.warning("Connect returned false — check Railway dashboard.")


@git_group.command("disconnect")
@click.argument("service_id")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def git_disconnect(ctx: click.Context, service_id: str, as_json: bool):
    """Disconnect the Git repository from a service."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        result = backend.git_disconnect(service_id)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps({"disconnected": result}, indent=2))
        return

    if result:
        skin.success(f"Service {service_id} disconnected from Git.")
    else:
        skin.warning("Disconnect returned false — check Railway dashboard.")
