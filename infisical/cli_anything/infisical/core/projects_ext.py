"""Extended project (workspace) operations: info, update, delete, memberships.

This module extends the base ProjectsClient helpers with Click command groups
for the `projects-x` namespace. It does not overwrite the existing
ProjectsClient class in core/projects.py.
"""

from __future__ import annotations

import click

from cli_anything.infisical.utils.infisical_backend import (
    InfisicalBackend,
    InfisicalAPIError,
)
from cli_anything.infisical.utils.repl_skin import ReplSkin


skin = ReplSkin("infisical", version="1.1.0")


# ---------------------------------------------------------------------------
# Helpers (duplicated to avoid circular imports with infisical_cli.py)
# ---------------------------------------------------------------------------


def _handle_api_error(err):
    import json, sys
    skin.error(f"API error {err.status_code}:")
    if isinstance(err.body, dict):
        click.echo(json.dumps(err.body, indent=2), err=True)
    else:
        click.echo(str(err.body), err=True)
    sys.exit(1)


def _require_token(ctx):
    if not ctx.token:
        skin.error(
            "Authentication token is required. Set INFISICAL_TOKEN or pass --token."
        )
        import sys
        sys.exit(1)


def _require_workspace(ctx):
    if not ctx.workspace_id:
        skin.error(
            "Workspace ID is required. Set INFISICAL_WORKSPACE_ID or pass --workspace/-w."
        )
        import sys
        sys.exit(1)


def _print_json(data):
    import json
    click.echo(json.dumps(data, indent=2))


def _resolve_project(ctx, project: str) -> str:
    """Return the effective project/workspace id (flag takes precedence)."""
    if project:
        return project
    _require_workspace(ctx)
    return ctx.workspace_id


# ---------------------------------------------------------------------------
# projects-x group
# ---------------------------------------------------------------------------


@click.group("projects-x")
def projects_ext_group():
    """Extended project (workspace) operations."""


# --- info ------------------------------------------------------------------


@projects_ext_group.command("info")
@click.option("--project", default="", help="Project/workspace ID (overrides context).")
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def projects_info(click_ctx, project: str, output_json: bool) -> None:
    """Show full details for a project/workspace."""
    ctx = click_ctx.obj
    _require_token(ctx)
    workspace_id = _resolve_project(ctx, project)
    use_json = output_json or ctx.output_json
    try:
        backend = ctx.backend()
        result = backend.get_workspace(workspace_id)
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return

    if use_json:
        _print_json(result)
    else:
        headers = ["FIELD", "VALUE"]
        rows = []
        for k in ("id", "_id", "name", "slug", "description", "autoCapitalization",
                  "organization", "orgId", "createdAt", "updatedAt"):
            if k in result:
                rows.append([k, str(result.get(k, ""))])
        if not rows:
            rows = [[k, str(v)] for k, v in result.items()]
        skin.table(headers, rows, max_col_width=60)


# --- update ----------------------------------------------------------------


@projects_ext_group.command("update")
@click.option("--project", default="", help="Project/workspace ID (overrides context).")
@click.option("--name", default=None, help="New project name.")
@click.option("--description", default=None, help="New project description.")
@click.option(
    "--auto-capitalization/--no-auto-capitalization",
    "auto_capitalization",
    default=None,
    help="Toggle secret auto-capitalization.",
)
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def projects_update(
    click_ctx,
    project: str,
    name,
    description,
    auto_capitalization,
    output_json: bool,
) -> None:
    """Update project name, description, or auto-capitalization setting."""
    ctx = click_ctx.obj
    _require_token(ctx)
    workspace_id = _resolve_project(ctx, project)

    if name is None and description is None and auto_capitalization is None:
        skin.error(
            "At least one field is required: --name, --description, "
            "or --auto-capitalization/--no-auto-capitalization."
        )
        import sys
        sys.exit(1)

    use_json = output_json or ctx.output_json
    try:
        backend = ctx.backend()
        result = backend.update_workspace(
            workspace_id=workspace_id,
            name=name,
            description=description,
            auto_capitalization=auto_capitalization,
        )
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return

    if use_json:
        _print_json(result)
    else:
        skin.success(f"Project '{workspace_id}' updated.")


# --- delete ----------------------------------------------------------------


@projects_ext_group.command("delete")
@click.option("--project", default="", help="Project/workspace ID (overrides context).")
@click.option("--yes", is_flag=True, default=False, help="Confirm deletion.")
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def projects_delete(
    click_ctx, project: str, yes: bool, output_json: bool
) -> None:
    """Delete a project/workspace (requires --yes)."""
    ctx = click_ctx.obj
    _require_token(ctx)
    workspace_id = _resolve_project(ctx, project)

    if not yes:
        skin.error("Refusing to delete project. Pass --yes to confirm.")
        import sys
        sys.exit(1)

    use_json = output_json or ctx.output_json
    try:
        backend = ctx.backend()
        result = backend.delete_workspace(workspace_id)
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return

    if use_json:
        _print_json(result)
    else:
        skin.success(f"Project '{workspace_id}' deleted.")


# ---------------------------------------------------------------------------
# members subgroup
# ---------------------------------------------------------------------------


@projects_ext_group.group("members", invoke_without_command=True)
@click.option("--project", default="", help="Project/workspace ID (overrides context).")
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def members_group(click_ctx, project: str, output_json: bool) -> None:
    """Manage project memberships (users + machine identities)."""
    # Stash flags on the Click context for subcommands / default list.
    click_ctx.ensure_object(object)
    click_ctx.meta["members_project"] = project
    click_ctx.meta["members_json"] = output_json

    if click_ctx.invoked_subcommand is None:
        click_ctx.invoke(members_list, project=project, output_json=output_json)


def _render_members_table(memberships):
    headers = ["MEMBERSHIP_ID", "USER_EMAIL", "ROLE"]
    rows = []
    for m in memberships:
        mid = m.get("id") or m.get("_id") or ""
        user = m.get("user") or {}
        identity = m.get("identity") or {}
        email = (
            user.get("email")
            or user.get("username")
            or user.get("firstName")
            or identity.get("name")
            or m.get("email")
            or m.get("username")
            or ""
        )
        # Role can live on membership or in a nested roles array.
        role = m.get("role") or ""
        if not role:
            roles = m.get("roles") or []
            if roles and isinstance(roles, list):
                role = roles[0].get("role", "") if isinstance(roles[0], dict) else str(roles[0])
        rows.append([str(mid), str(email), str(role)])
    skin.table(headers, rows, max_col_width=60)


@members_group.command("list")
@click.option("--project", default="", help="Project/workspace ID (overrides context).")
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def members_list(click_ctx, project: str, output_json: bool) -> None:
    """List project members (users + identities)."""
    ctx = click_ctx.obj
    _require_token(ctx)
    workspace_id = _resolve_project(ctx, project)
    use_json = output_json or ctx.output_json
    try:
        backend = ctx.backend()
        result = backend.list_workspace_memberships(workspace_id)
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return

    if use_json:
        _print_json(result)
    else:
        if not result:
            skin.info("No members found.")
            return
        _render_members_table(result)


@members_group.command("set-role")
@click.argument("membership_id")
@click.argument("role")
@click.option("--project", default="", help="Project/workspace ID (overrides context).")
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def members_set_role(
    click_ctx,
    membership_id: str,
    role: str,
    project: str,
    output_json: bool,
) -> None:
    """Set the ROLE on MEMBERSHIP_ID."""
    ctx = click_ctx.obj
    _require_token(ctx)
    workspace_id = _resolve_project(ctx, project)
    use_json = output_json or ctx.output_json
    try:
        backend = ctx.backend()
        result = backend.update_membership_role(
            workspace_id=workspace_id,
            membership_id=membership_id,
            role=role,
        )
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return

    if use_json:
        _print_json(result)
    else:
        skin.success(f"Membership '{membership_id}' role set to '{role}'.")


@members_group.command("remove")
@click.option("--project", default="", help="Project/workspace ID (overrides context).")
@click.option("--email", "emails", multiple=True, help="Email(s) to remove.")
@click.option("--username", "usernames", multiple=True, help="Username(s) to remove.")
@click.option("--yes", is_flag=True, default=False, help="Confirm removal.")
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def members_remove(
    click_ctx,
    project: str,
    emails,
    usernames,
    yes: bool,
    output_json: bool,
) -> None:
    """Remove member(s) from a project by --email or --username."""
    ctx = click_ctx.obj
    _require_token(ctx)
    workspace_id = _resolve_project(ctx, project)

    email_list = list(emails) if emails else []
    username_list = list(usernames) if usernames else []
    if not email_list and not username_list:
        skin.error(
            "At least one --email or --username is required to remove members."
        )
        import sys
        sys.exit(1)

    if not yes:
        skin.error("Refusing to remove members. Pass --yes to confirm.")
        import sys
        sys.exit(1)

    use_json = output_json or ctx.output_json
    try:
        backend = ctx.backend()
        result = backend.delete_workspace_membership(
            project_id=workspace_id,
            emails=email_list or None,
            usernames=username_list or None,
        )
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return

    if use_json:
        _print_json(result)
    else:
        targets = ", ".join(email_list + username_list)
        skin.success(f"Removed member(s): {targets}.")


__all__ = ["projects_ext_group"]
