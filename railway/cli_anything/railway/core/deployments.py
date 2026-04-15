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
@click.option("--env", "environment_id", default=None, help="Environment ID (optional filter).")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def deployments_list(ctx: click.Context, service_id: str, environment_id: str | None, as_json: bool):
    """List deployments for a service."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        deployments = backend.deployments_list(service_id, environment_id)
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


@deployments_group.command("restart")
@click.argument("deployment_id")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def deployments_restart(ctx: click.Context, deployment_id: str, as_json: bool):
    """Restart a deployment without rebuilding."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        result = backend.deployment_restart(deployment_id)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps({"restarted": result, "deploymentId": deployment_id}, indent=2))
        return

    if result:
        skin.success(f"Deployment {deployment_id} restarted.")
    else:
        skin.warning("Restart returned false — check Railway dashboard.")


@deployments_group.command("cancel")
@click.argument("deployment_id")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def deployments_cancel(ctx: click.Context, deployment_id: str, as_json: bool):
    """Cancel an in-progress deployment."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        result = backend.deployment_cancel(deployment_id)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps({"cancelled": result, "deploymentId": deployment_id}, indent=2))
        return

    if result:
        skin.success(f"Deployment {deployment_id} cancelled.")
    else:
        skin.warning("Cancel returned false — deployment may have already completed.")


@deployments_group.command("stop")
@click.argument("service_id")
@click.option("--env", "environment_id", required=True, help="Environment ID.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def deployments_stop(
    ctx: click.Context, service_id: str, environment_id: str, as_json: bool
):
    """Stop the active deployment for a service in an environment."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        result = backend.deployment_stop(service_id, environment_id)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps({"stopped": result, "serviceId": service_id}, indent=2))
        return

    if result:
        skin.success(f"Deployment stopped for service {service_id}.")
    else:
        skin.warning("Stop returned false — check Railway dashboard.")


@deployments_group.command("trigger-v2")
@click.argument("service_id")
@click.option("--env", "environment_id", required=True, help="Environment ID.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def deployments_trigger_v2(
    ctx: click.Context, service_id: str, environment_id: str, as_json: bool
):
    """Trigger a deployment and return the deployment ID."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        result = backend.deployment_trigger_v2(service_id, environment_id)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps(result, indent=2))
        return

    dep_id = result.get("id", "")
    status = result.get("status", "")
    skin.success(f"Deployment triggered: {dep_id} (status: {status})")


@deployments_group.command("redeploy")
@click.argument("deployment_id")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def deployments_redeploy(ctx: click.Context, deployment_id: str, as_json: bool):
    """Redeploy an existing deployment."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        result = backend.deployment_redeploy(deployment_id)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps(result, indent=2))
        return

    new_id = result.get("id", "")
    status = result.get("status", "")
    if new_id:
        skin.success(f"Deployment redeployed: {new_id} (status: {status})")
    else:
        skin.warning("Redeploy returned empty — check Railway dashboard.")


@deployments_group.command("redeploy-latest")
@click.argument("service_id")
@click.option("--env", "environment_id", required=True, help="Environment ID.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def deployments_redeploy_latest(
    ctx: click.Context, service_id: str, environment_id: str, as_json: bool
):
    """Redeploy the latest deployment for a service."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        result = backend.service_instance_redeploy(service_id, environment_id)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps({"redeployed": result, "serviceId": service_id}, indent=2))
        return

    if result:
        skin.success(f"Latest deployment redeployed for service {service_id}.")
    else:
        skin.warning("Redeploy returned false — check Railway dashboard.")


@deployments_group.command("remove")
@click.argument("deployment_id")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def deployments_remove(ctx: click.Context, deployment_id: str, as_json: bool):
    """Remove a deployment from history."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        result = backend.deployment_remove(deployment_id)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps({"removed": result, "deploymentId": deployment_id}, indent=2))
        return

    if result:
        skin.success(f"Deployment {deployment_id} removed from history.")
    else:
        skin.warning("Remove returned false — check Railway dashboard.")
