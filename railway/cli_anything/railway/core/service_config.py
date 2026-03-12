"""Service configuration commands for cli-anything-railway."""

from __future__ import annotations

import json
import sys

import click

from cli_anything.railway.utils.railway_backend import RailwayBackend, RailwayAPIError

_RESTART_POLICIES = ("ALWAYS", "ON_FAILURE", "NEVER")


@click.group("service-config")
def service_config_group():
    """Get and update Railway service instance configuration."""


@service_config_group.command("get")
@click.argument("service_id")
@click.option("--env", "environment_id", required=True, help="Environment ID.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def service_config_get(
    ctx: click.Context, service_id: str, environment_id: str, as_json: bool
):
    """Show build/start configuration for a service instance."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        cfg = backend.service_instance_get(service_id, environment_id)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps(cfg, indent=2))
        return

    if not cfg:
        skin.info("No configuration found.")
        return

    skin.status_block(
        {
            "Start command":   cfg.get("startCommand") or "",
            "Build command":   cfg.get("buildCommand") or "",
            "Dockerfile":      cfg.get("dockerfilePath") or "",
            "Health check":    cfg.get("healthcheckPath") or "",
            "Restart policy":  cfg.get("restartPolicyType") or "",
            "Root directory":  cfg.get("rootDirectory") or "",
        },
        title="Service Configuration",
    )


def _update(ctx: click.Context, service_id: str, environment_id: str, patch: dict, as_json: bool):
    """Helper: call serviceInstanceUpdate and print result."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        ok = backend.service_instance_update(service_id, environment_id, patch)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps({"updated": ok}, indent=2))
        return

    if ok:
        skin.success("Service configuration updated.")
    else:
        skin.warning("Update returned false — check Railway dashboard.")


@service_config_group.command("set-start-command")
@click.argument("service_id")
@click.argument("command")
@click.option("--env", "environment_id", required=True, help="Environment ID.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def set_start_command(
    ctx: click.Context, service_id: str, command: str, environment_id: str, as_json: bool
):
    """Set the start command for a service."""
    _update(ctx, service_id, environment_id, {"startCommand": command}, as_json)


@service_config_group.command("set-build-command")
@click.argument("service_id")
@click.argument("command")
@click.option("--env", "environment_id", required=True, help="Environment ID.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def set_build_command(
    ctx: click.Context, service_id: str, command: str, environment_id: str, as_json: bool
):
    """Set the build command for a service."""
    _update(ctx, service_id, environment_id, {"buildCommand": command}, as_json)


@service_config_group.command("set-dockerfile")
@click.argument("service_id")
@click.argument("path")
@click.option("--env", "environment_id", required=True, help="Environment ID.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def set_dockerfile(
    ctx: click.Context, service_id: str, path: str, environment_id: str, as_json: bool
):
    """Set the Dockerfile path for a service."""
    _update(ctx, service_id, environment_id, {"dockerfilePath": path}, as_json)


@service_config_group.command("set-health-check")
@click.argument("service_id")
@click.argument("path")
@click.option("--env", "environment_id", required=True, help="Environment ID.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def set_health_check(
    ctx: click.Context, service_id: str, path: str, environment_id: str, as_json: bool
):
    """Set the health check path for a service."""
    _update(ctx, service_id, environment_id, {"healthcheckPath": path}, as_json)


@service_config_group.command("set-restart-policy")
@click.argument("service_id")
@click.argument("policy", type=click.Choice(_RESTART_POLICIES, case_sensitive=False))
@click.option("--env", "environment_id", required=True, help="Environment ID.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def set_restart_policy(
    ctx: click.Context, service_id: str, policy: str, environment_id: str, as_json: bool
):
    """Set restart policy (ALWAYS, ON_FAILURE, NEVER)."""
    _update(
        ctx, service_id, environment_id,
        {"restartPolicyType": policy.upper()}, as_json,
    )


@service_config_group.command("set-root-dir")
@click.argument("service_id")
@click.argument("directory")
@click.option("--env", "environment_id", required=True, help="Environment ID.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def set_root_dir(
    ctx: click.Context, service_id: str, directory: str, environment_id: str, as_json: bool
):
    """Set the root directory for a service."""
    _update(ctx, service_id, environment_id, {"rootDirectory": directory}, as_json)
