"""Domains commands for cli-anything-railway."""

from __future__ import annotations

import json
import sys

import click

from cli_anything.railway.utils.railway_backend import RailwayBackend, RailwayAPIError


@click.group("domains")
def domains_group():
    """Manage Railway service domains."""


@domains_group.command("list")
@click.option("--service", "service_id", required=True, help="Service ID.")
@click.option("--env", "environment_id", required=True, help="Environment ID.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def domains_list(
    ctx: click.Context, service_id: str, environment_id: str, as_json: bool
):
    """List domains for a service."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        domains = backend.domains_list(service_id, environment_id)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps(domains, indent=2))
        return

    if not domains:
        skin.info("No domains found.")
        return

    skin.table(
        ["ID", "Domain", "Type", "Created"],
        [
            [
                d.get("id", ""),
                d.get("domain", ""),
                d.get("type", ""),
                (d.get("createdAt") or "")[:19],
            ]
            for d in domains
        ],
    )


@domains_group.command("create")
@click.argument("domain")
@click.option("--service", "service_id", required=True, help="Service ID.")
@click.option("--env", "environment_id", required=True, help="Environment ID.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def domains_create(
    ctx: click.Context,
    domain: str,
    service_id: str,
    environment_id: str,
    as_json: bool,
):
    """Add a custom domain to a service."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        result = backend.custom_domain_create(domain, service_id, environment_id)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps(result, indent=2))
        return

    skin.success(f"Custom domain added: {result.get('domain')} (id: {result.get('id')})")


@domains_group.command("delete")
@click.argument("domain_id")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def domains_delete(ctx: click.Context, domain_id: str, as_json: bool):
    """Delete a custom domain by ID."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        result = backend.custom_domain_delete(domain_id)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps({"deleted": result, "id": domain_id}, indent=2))
        return

    if result:
        skin.success(f"Domain {domain_id} deleted.")
    else:
        skin.warning(f"Domain delete returned false for {domain_id}.")


@domains_group.command("generate")
@click.option("--service", "service_id", required=True, help="Service ID.")
@click.option("--env", "environment_id", required=True, help="Environment ID.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def domains_generate(
    ctx: click.Context, service_id: str, environment_id: str, as_json: bool
):
    """Generate a railway.app domain for a service."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        result = backend.service_domain_create(service_id, environment_id)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps(result, indent=2))
        return

    skin.success(
        f"Railway domain generated: {result.get('domain')} (id: {result.get('id')})"
    )
