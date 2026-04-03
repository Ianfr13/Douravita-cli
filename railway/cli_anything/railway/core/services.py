"""Services commands for cli-anything-railway."""

from __future__ import annotations

import json
import sys

import click

from cli_anything.railway.utils.railway_backend import RailwayBackend, RailwayAPIError


@click.group("services")
def services_group():
    """Manage Railway services."""


@services_group.command("list")
@click.option("--project", "project_id", required=True, help="Project ID.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def services_list(ctx: click.Context, project_id: str, as_json: bool):
    """List services in a project."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        services = backend.services_list(project_id)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps(services, indent=2))
        return

    if not services:
        skin.info("No services found.")
        return

    skin.table(
        ["ID", "Name", "Created"],
        [
            [
                s.get("id", ""),
                s.get("name", ""),
                (s.get("createdAt") or "")[:19],
            ]
            for s in services
        ],
    )


@services_group.command("info")
@click.argument("service_id")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def services_info(ctx: click.Context, service_id: str, as_json: bool):
    """Get details for a service."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        service = backend.service_info(service_id)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps(service, indent=2))
        return

    if not service:
        skin.error(f"Service not found: {service_id}")
        sys.exit(1)

    skin.status_block(
        {
            "ID": service.get("id", ""),
            "Name": service.get("name", ""),
            "Created": (service.get("createdAt") or "")[:19],
            "Updated": (service.get("updatedAt") or "")[:19],
        },
        title="Service",
    )


@services_group.command("create-cron")
@click.argument("name")
@click.argument("schedule")
@click.option("--project", "project_id", required=True, help="Project ID.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def services_create_cron(
    ctx: click.Context, name: str, schedule: str, project_id: str, as_json: bool
):
    """Create a cron service in a project.

    SCHEDULE should be a cron expression, e.g. "0 * * * *".
    """
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        service = backend.service_create_cron(name, project_id, schedule)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps(service, indent=2))
        return

    skin.success(
        f"Cron service created: {service.get('name')} (id: {service.get('id')}) "
        f"with schedule '{schedule}'."
    )


@services_group.command("create")
@click.argument("name")
@click.option("--project", "project_id", required=True, help="Project ID.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def services_create(ctx: click.Context, name: str, project_id: str, as_json: bool):
    """Create a new service in a project."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        service = backend.service_create(name, project_id)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps(service, indent=2))
        return

    skin.success(f"Service created: {service.get('name')} (id: {service.get('id')})")


@services_group.command("update")
@click.argument("service_id")
@click.option("--name", required=True, help="New service name.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def services_update(ctx: click.Context, service_id: str, name: str, as_json: bool):
    """Rename a service."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        service = backend.service_update(service_id, name=name)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps(service, indent=2))
        return

    skin.success(f"Service updated: {service.get('name')} ({service.get('id')})")


@services_group.command("delete")
@click.argument("service_id")
@click.option("--yes", is_flag=True, help="Skip confirmation.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def services_delete(ctx: click.Context, service_id: str, yes: bool, as_json: bool):
    """Delete a service (irreversible)."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]

    if not yes:
        skin.warning(f"This will permanently delete service {service_id}.")
        if not click.confirm("Continue?"):
            skin.info("Aborted.")
            return

    try:
        result = backend.service_delete(service_id)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps({"deleted": result, "serviceId": service_id}, indent=2))
        return

    if result:
        skin.success(f"Service {service_id} deleted.")
    else:
        skin.warning("Delete returned false — check Railway dashboard.")
