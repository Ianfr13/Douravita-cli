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
