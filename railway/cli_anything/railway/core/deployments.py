"""Deployments commands for cli-anything-railway."""

from __future__ import annotations

import json
import sys

import click

from cli_anything.railway.utils.railway_backend import RailwayBackend, RailwayAPIError


@click.group("deployments")
def deployments_group():
    """Manage Railway deployments."""


@deployments_group.command("list")
@click.option("--service", "service_id", required=True, help="Service ID.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def deployments_list(ctx: click.Context, service_id: str, as_json: bool):
    """List deployments for a service."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        deployments = backend.deployments_list(service_id)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps(deployments, indent=2))
        return

    if not deployments:
        skin.info("No deployments found.")
        return

    skin.table(
        ["ID", "Status", "Created", "URL"],
        [
            [
                d.get("id", ""),
                d.get("status", ""),
                (d.get("createdAt") or "")[:19],
                d.get("staticUrl") or "",
            ]
            for d in deployments
        ],
    )


@deployments_group.command("trigger")
@click.argument("service_id")
@click.option("--env", "environment_id", required=True, help="Environment ID.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def deployments_trigger(
    ctx: click.Context, service_id: str, environment_id: str, as_json: bool
):
    """Trigger a new deployment for a service."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        result = backend.deployment_trigger(service_id, environment_id)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps({"triggered": result}, indent=2))
        return

    if result:
        skin.success("Deployment triggered successfully.")
    else:
        skin.warning("Deployment trigger returned false — check Railway dashboard.")


@deployments_group.command("status")
@click.argument("deployment_id")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def deployments_status(ctx: click.Context, deployment_id: str, as_json: bool):
    """Get status/info for a deployment."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        deployment = backend.deployment_status(deployment_id)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps(deployment, indent=2))
        return

    if not deployment:
        skin.error(f"Deployment not found: {deployment_id}")
        sys.exit(1)

    skin.status_block(
        {
            "ID": deployment.get("id", ""),
            "Status": deployment.get("status", ""),
            "Created": (deployment.get("createdAt") or "")[:19],
            "URL": deployment.get("staticUrl") or "",
        },
        title="Deployment",
    )


@deployments_group.command("rollback")
@click.argument("deployment_id")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def deployments_rollback(ctx: click.Context, deployment_id: str, as_json: bool):
    """Rollback to a previous deployment."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        result = backend.deployment_rollback(deployment_id)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps({"rolledBack": result, "deploymentId": deployment_id}, indent=2))
        return

    if result:
        skin.success(f"Rolled back to deployment {deployment_id}.")
    else:
        skin.warning("Rollback returned false — check Railway dashboard.")
