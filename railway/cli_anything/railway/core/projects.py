"""Projects commands for cli-anything-railway."""

from __future__ import annotations

import json
import sys

import click

from cli_anything.railway.utils.railway_backend import RailwayBackend, RailwayAPIError


@click.group("projects")
def projects_group():
    """Manage Railway projects."""


@projects_group.command("list")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def projects_list(ctx: click.Context, as_json: bool):
    """List all projects."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        projects = backend.projects_list()
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps(projects, indent=2))
        return

    if not projects:
        skin.info("No projects found.")
        return

    skin.table(
        ["ID", "Name", "Description", "Created"],
        [
            [
                p.get("id", ""),
                p.get("name", ""),
                (p.get("description") or "")[:40],
                (p.get("createdAt") or "")[:19],
            ]
            for p in projects
        ],
    )


@projects_group.command("create")
@click.argument("name")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def projects_create(ctx: click.Context, name: str, as_json: bool):
    """Create a new project."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        project = backend.project_create(name)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps(project, indent=2))
        return

    skin.success(f"Project created: {project.get('name')} ({project.get('id')})")


@projects_group.command("info")
@click.argument("project_id")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def projects_info(ctx: click.Context, project_id: str, as_json: bool):
    """Get details for a project."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        project = backend.project_info(project_id)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps(project, indent=2))
        return

    if not project:
        skin.error(f"Project not found: {project_id}")
        sys.exit(1)

    skin.status_block(
        {
            "ID": project.get("id", ""),
            "Name": project.get("name", ""),
            "Description": project.get("description") or "",
            "Created": (project.get("createdAt") or "")[:19],
            "Updated": (project.get("updatedAt") or "")[:19],
        },
        title="Project",
    )

    envs = [
        e["node"]
        for e in (project.get("environments") or {}).get("edges", [])
    ]
    if envs:
        skin.section("Environments")
        skin.table(["ID", "Name"], [[e.get("id", ""), e.get("name", "")] for e in envs])

    services = [
        s["node"]
        for s in (project.get("services") or {}).get("edges", [])
    ]
    if services:
        skin.section("Services")
        skin.table(
            ["ID", "Name", "Created"],
            [
                [s.get("id", ""), s.get("name", ""), (s.get("createdAt") or "")[:19]]
                for s in services
            ],
        )


@projects_group.command("update")
@click.argument("project_id")
@click.option("--name", default=None, help="New project name.")
@click.option("--description", default=None, help="New project description.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def projects_update(
    ctx: click.Context,
    project_id: str,
    name: str | None,
    description: str | None,
    as_json: bool,
):
    """Update a project's name or description."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]

    if name is None and description is None:
        skin.error("Provide at least --name or --description.")
        sys.exit(1)

    try:
        project = backend.project_update(project_id, name=name, description=description)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps(project, indent=2))
        return

    skin.success(f"Project updated: {project.get('name')} ({project.get('id')})")


@projects_group.command("delete")
@click.argument("project_id")
@click.option("--yes", is_flag=True, help="Skip confirmation.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def projects_delete(ctx: click.Context, project_id: str, yes: bool, as_json: bool):
    """Delete a project (irreversible)."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]

    if not yes:
        skin.warning(f"This will permanently delete project {project_id}.")
        if not click.confirm("Continue?"):
            skin.info("Aborted.")
            return

    try:
        result = backend.project_delete(project_id)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps({"deleted": result, "projectId": project_id}, indent=2))
        return

    if result:
        skin.success(f"Project {project_id} deleted.")
    else:
        skin.warning("Delete returned false — check Railway dashboard.")


@projects_group.command("members")
@click.argument("project_id")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def projects_members(ctx: click.Context, project_id: str, as_json: bool):
    """List members of a project."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        members = backend.project_members(project_id)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps(members, indent=2))
        return

    if not members:
        skin.info("No members found.")
        return

    skin.table(
        ["Member ID", "Role", "User ID", "Name", "Email"],
        [
            [
                m.get("id", ""),
                m.get("role", ""),
                (m.get("user") or {}).get("id", ""),
                (m.get("user") or {}).get("name", ""),
                (m.get("user") or {}).get("email", ""),
            ]
            for m in members
        ],
    )


@projects_group.command("transfer")
@click.argument("project_id")
@click.option("--workspace", "workspace_id", required=True, help="Target workspace ID.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def projects_transfer(
    ctx: click.Context, project_id: str, workspace_id: str, as_json: bool
):
    """Transfer a project to another workspace."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        result = backend.project_transfer(project_id, workspace_id)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps({"transferred": result, "projectId": project_id}, indent=2))
        return

    if result:
        skin.success(f"Project {project_id} transferred to workspace {workspace_id}.")
    else:
        skin.warning("Transfer returned false — check Railway dashboard.")
