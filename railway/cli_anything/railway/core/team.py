"""Team / Members commands for cli-anything-railway."""

from __future__ import annotations

import json
import sys

import click

from cli_anything.railway.utils.railway_backend import RailwayBackend, RailwayAPIError

_ROLES = ("ADMIN", "MEMBER")


@click.group("team")
def team_group():
    """Manage Railway team members."""


@team_group.command("list")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def team_list(ctx: click.Context, as_json: bool):
    """List team members across all teams."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        members = backend.team_list()
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps(members, indent=2))
        return

    if not members:
        skin.info("No team members found.")
        return

    skin.table(
        ["Team", "User ID", "Email", "Role"],
        [
            [
                m.get("teamName", ""),
                m.get("id", ""),
                m.get("email", ""),
                m.get("role", ""),
            ]
            for m in members
        ],
    )


@team_group.command("invite")
@click.argument("email")
@click.option("--team", "team_id", required=True, help="Team ID.")
@click.option(
    "--role",
    default="MEMBER",
    show_default=True,
    type=click.Choice(_ROLES, case_sensitive=False),
    help="Role to assign.",
)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def team_invite(
    ctx: click.Context, email: str, team_id: str, role: str, as_json: bool
):
    """Invite a member to a team."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        result = backend.team_invite(team_id, email, role.upper())
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps({"invited": result, "email": email, "role": role}, indent=2))
        return

    if result:
        skin.success(f"Invitation sent to {email} as {role}.")
    else:
        skin.warning(f"Invite returned false for {email}.")


@team_group.command("remove")
@click.argument("user_id")
@click.option("--team", "team_id", required=True, help="Team ID.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def team_remove(ctx: click.Context, user_id: str, team_id: str, as_json: bool):
    """Remove a member from a team."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        result = backend.team_member_remove(team_id, user_id)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps({"removed": result, "userId": user_id}, indent=2))
        return

    if result:
        skin.success(f"User {user_id} removed from team.")
    else:
        skin.warning(f"Remove returned false for user {user_id}.")
