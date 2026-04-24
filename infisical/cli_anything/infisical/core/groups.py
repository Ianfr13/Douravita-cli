"""Groups + group-users commands for Infisical CLI."""

from __future__ import annotations

import json as _json
import sys
from typing import Any

import click

from cli_anything.infisical.utils.infisical_backend import (
    InfisicalBackend,
    InfisicalAPIError,
)
from cli_anything.infisical.utils.repl_skin import ReplSkin

skin = ReplSkin("infisical", version="1.1.0")


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _handle_api_error(err: InfisicalAPIError) -> None:
    skin.error(f"API error {err.status_code}:")
    if isinstance(err.body, dict):
        click.echo(_json.dumps(err.body, indent=2), err=True)
    else:
        click.echo(str(err.body), err=True)
    sys.exit(1)


def _require_token(ctx: Any) -> None:
    if not ctx.token:
        skin.error(
            "Authentication token is required. Set INFISICAL_TOKEN or pass --token."
        )
        sys.exit(1)


def _print_json(data: Any) -> None:
    click.echo(_json.dumps(data, indent=2))


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------


class GroupsClient:
    """High-level client for org-level groups."""

    def __init__(self, backend: InfisicalBackend):
        self.backend = backend

    def list(self, organization_id: str, offset: int = 0, limit: int = 100):
        return self.backend.list_groups(organization_id, offset=offset, limit=limit)

    def get(self, group_id: str):
        return self.backend.get_group(group_id)

    def create(
        self, name: str, slug: str, organization_id: str, role: str = "no-access"
    ):
        return self.backend.create_group(name, slug, organization_id, role=role)

    def update(
        self,
        group_id: str,
        name: str | None = None,
        slug: str | None = None,
        role: str | None = None,
    ):
        return self.backend.update_group(
            group_id, name=name, slug=slug, role=role
        )

    def delete(self, group_id: str):
        return self.backend.delete_group(group_id)

    def list_users(
        self,
        group_id: str,
        offset: int = 0,
        limit: int = 100,
        username: str | None = None,
        filter: str | None = None,
    ):
        return self.backend.list_group_users(
            group_id, offset=offset, limit=limit,
            username=username, filter=filter,
        )

    def add_user(self, group_id: str, username: str):
        return self.backend.add_user_to_group(group_id, username)

    def remove_user(self, group_id: str, username: str):
        return self.backend.remove_user_from_group(group_id, username)


# ---------------------------------------------------------------------------
# Click group
# ---------------------------------------------------------------------------


@click.group("groups")
def groups_group() -> None:
    """Manage organization groups and their members."""


@groups_group.command("list")
@click.option("--org-id", "org_id", required=True,
              envvar="INFISICAL_ORG_ID",
              help="Organization ID (or set INFISICAL_ORG_ID).")
@click.option("--limit", type=int, default=100, show_default=True)
@click.option("--offset", type=int, default=0, show_default=True)
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def groups_list(
    click_ctx: click.Context,
    org_id: str,
    limit: int,
    offset: int,
    output_json: bool,
) -> None:
    """List groups in an organization."""
    ctx = click_ctx.obj
    _require_token(ctx)
    use_json = output_json or ctx.output_json
    try:
        client = GroupsClient(ctx.backend())
        result = client.list(org_id, offset=offset, limit=limit)
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return
    if use_json:
        _print_json(result)
        return
    if not result:
        skin.info("No groups found.")
        return
    headers = ["ID", "NAME", "SLUG", "ROLE"]
    rows = []
    for g in result:
        rows.append([
            str(g.get("id", g.get("_id", ""))),
            str(g.get("name", "")),
            str(g.get("slug", "")),
            str(g.get("role", "")),
        ])
    skin.table(headers, rows, max_col_width=60)


@groups_group.command("get")
@click.argument("group_id")
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def groups_get(
    click_ctx: click.Context, group_id: str, output_json: bool
) -> None:
    """Get a group by GROUP_ID."""
    ctx = click_ctx.obj
    _require_token(ctx)
    try:
        client = GroupsClient(ctx.backend())
        result = client.get(group_id)
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return
    _print_json(result)


@groups_group.command("create")
@click.argument("name")
@click.argument("slug")
@click.option("--org-id", "org_id", required=True, envvar="INFISICAL_ORG_ID")
@click.option("--role", default="no-access", show_default=True)
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def groups_create(
    click_ctx: click.Context,
    name: str,
    slug: str,
    org_id: str,
    role: str,
    output_json: bool,
) -> None:
    """Create a group with NAME and SLUG."""
    ctx = click_ctx.obj
    _require_token(ctx)
    use_json = output_json or ctx.output_json
    try:
        client = GroupsClient(ctx.backend())
        result = client.create(name, slug, org_id, role=role)
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return
    if use_json:
        _print_json(result)
    else:
        gid = result.get("id") or result.get("_id", "") if isinstance(result, dict) else ""
        skin.success(f"Group '{name}' created (id: {gid}).")


@groups_group.command("update")
@click.argument("group_id")
@click.option("--name", default=None)
@click.option("--slug", default=None)
@click.option("--role", default=None)
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def groups_update(
    click_ctx: click.Context,
    group_id: str,
    name: str | None,
    slug: str | None,
    role: str | None,
    output_json: bool,
) -> None:
    """Update group GROUP_ID (at least one change)."""
    ctx = click_ctx.obj
    _require_token(ctx)
    if name is None and slug is None and role is None:
        skin.error("At least one of --name, --slug, --role is required.")
        sys.exit(1)
    use_json = output_json or ctx.output_json
    try:
        client = GroupsClient(ctx.backend())
        result = client.update(group_id, name=name, slug=slug, role=role)
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return
    if use_json:
        _print_json(result)
    else:
        skin.success(f"Group '{group_id}' updated.")


@groups_group.command("delete")
@click.argument("group_id")
@click.option("--yes", is_flag=True, required=True,
              help="Required to confirm deletion.")
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def groups_delete(
    click_ctx: click.Context,
    group_id: str,
    yes: bool,
    output_json: bool,
) -> None:
    """Delete group GROUP_ID."""
    ctx = click_ctx.obj
    _require_token(ctx)
    use_json = output_json or ctx.output_json
    try:
        client = GroupsClient(ctx.backend())
        result = client.delete(group_id)
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return
    if use_json:
        _print_json(result)
    else:
        skin.success(f"Group '{group_id}' deleted.")


# ---------------------------------------------------------------------------
# Nested users subgroup
# ---------------------------------------------------------------------------


@groups_group.group("users")
def users_group() -> None:
    """Manage users of a group."""


@users_group.command("list")
@click.argument("group_id")
@click.option("--limit", type=int, default=100, show_default=True)
@click.option("--offset", type=int, default=0, show_default=True)
@click.option("--username", default=None, help="Filter by username.")
@click.option("--filter", "filter_", default=None,
              type=click.Choice(["members", "non-members"]),
              help="Restrict to members or non-members of the group.")
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def users_list(
    click_ctx: click.Context,
    group_id: str,
    limit: int,
    offset: int,
    username: str | None,
    filter_: str | None,
    output_json: bool,
) -> None:
    """List users for GROUP_ID."""
    ctx = click_ctx.obj
    _require_token(ctx)
    use_json = output_json or ctx.output_json
    try:
        client = GroupsClient(ctx.backend())
        result = client.list_users(
            group_id, offset=offset, limit=limit,
            username=username, filter=filter_,
        )
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return
    if use_json:
        _print_json(result)
        return
    if not result:
        skin.info("No users found.")
        return
    headers = ["USERNAME", "EMAIL", "ROLE", "IS_PART_OF_GROUP"]
    rows = []
    for u in result:
        rows.append([
            str(u.get("username", "")),
            str(u.get("email", "")),
            str(u.get("role", "")),
            str(u.get("isPartOfGroup", "")),
        ])
    skin.table(headers, rows, max_col_width=60)


@users_group.command("add")
@click.argument("group_id")
@click.argument("username")
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def users_add(
    click_ctx: click.Context,
    group_id: str,
    username: str,
    output_json: bool,
) -> None:
    """Add USERNAME to GROUP_ID."""
    ctx = click_ctx.obj
    _require_token(ctx)
    use_json = output_json or ctx.output_json
    try:
        client = GroupsClient(ctx.backend())
        result = client.add_user(group_id, username)
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return
    if use_json:
        _print_json(result)
    else:
        skin.success(f"Added '{username}' to group '{group_id}'.")


@users_group.command("remove")
@click.argument("group_id")
@click.argument("username")
@click.option("--yes", is_flag=True, required=True,
              help="Required to confirm removal.")
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def users_remove(
    click_ctx: click.Context,
    group_id: str,
    username: str,
    yes: bool,
    output_json: bool,
) -> None:
    """Remove USERNAME from GROUP_ID."""
    ctx = click_ctx.obj
    _require_token(ctx)
    use_json = output_json or ctx.output_json
    try:
        client = GroupsClient(ctx.backend())
        result = client.remove_user(group_id, username)
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return
    if use_json:
        _print_json(result)
    else:
        skin.success(f"Removed '{username}' from group '{group_id}'.")


__all__ = ["GroupsClient", "groups_group"]
