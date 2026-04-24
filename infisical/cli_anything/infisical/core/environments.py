"""Environment operations for Infisical CLI (workspace-scoped)."""

from __future__ import annotations

import json
import sys

import click

from cli_anything.infisical.utils.infisical_backend import (
    InfisicalBackend,
    InfisicalAPIError,
)
from cli_anything.infisical.utils.repl_skin import ReplSkin


skin = ReplSkin("infisical", version="1.1.0")


# ---------------------------------------------------------------------------
# Local helpers
# ---------------------------------------------------------------------------


def _handle_api_error(err: InfisicalAPIError) -> None:
    skin.error(f"API error {err.status_code}:")
    if isinstance(err.body, dict):
        click.echo(json.dumps(err.body, indent=2), err=True)
    else:
        click.echo(str(err.body), err=True)
    sys.exit(1)


def _require_token(ctx) -> None:
    if not ctx.token:
        skin.error(
            "Authentication token is required. Set INFISICAL_TOKEN or pass --token."
        )
        sys.exit(1)


def _require_workspace(ctx) -> None:
    if not ctx.workspace_id:
        skin.error(
            "Workspace ID is required. Set INFISICAL_WORKSPACE_ID or pass --workspace/-w."
        )
        sys.exit(1)


def _print_json(data: object) -> None:
    click.echo(json.dumps(data, indent=2))


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------


class EnvironmentsClient:
    """High-level client for workspace-scoped environment operations."""

    def __init__(self, backend: InfisicalBackend, workspace_id: str):
        self.backend = backend
        self.workspace_id = workspace_id

    def list(self) -> list[dict]:
        return self.backend.list_environments(workspace_id=self.workspace_id)

    def get(self, env_id: str) -> dict:
        return self.backend.get_environment(
            workspace_id=self.workspace_id, env_id=env_id
        )

    def create(self, name: str, slug: str, position: int | None = None) -> dict:
        return self.backend.create_environment(
            workspace_id=self.workspace_id,
            name=name,
            slug=slug,
            position=position,
        )

    def update(
        self,
        env_id: str,
        name: str | None = None,
        slug: str | None = None,
        position: int | None = None,
    ) -> dict:
        return self.backend.update_environment(
            workspace_id=self.workspace_id,
            env_id=env_id,
            name=name,
            slug=slug,
            position=position,
        )

    def delete(self, env_id: str) -> dict:
        return self.backend.delete_environment(
            workspace_id=self.workspace_id, env_id=env_id
        )


# ---------------------------------------------------------------------------
# Click group
# ---------------------------------------------------------------------------


@click.group("environments")
def environments_group() -> None:
    """Manage environments within a project/workspace."""


@environments_group.command("list")
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def environments_list(click_ctx, output_json: bool) -> None:
    """List all environments for the current workspace."""
    ctx = click_ctx.obj
    _require_token(ctx)
    _require_workspace(ctx)
    use_json = output_json or ctx.output_json
    try:
        client = EnvironmentsClient(
            backend=ctx.backend(), workspace_id=ctx.workspace_id
        )
        result = client.list()
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return

    if use_json:
        _print_json(result)
    else:
        if not result:
            skin.info("No environments found.")
            return
        headers = ["ID", "NAME", "SLUG", "POSITION"]
        rows = []
        for e in result:
            eid = e.get("id") or e.get("_id", "")
            name = e.get("name", "")
            slug = e.get("slug", "")
            position = str(e.get("position", ""))
            rows.append([eid, name, slug, position])
        skin.table(headers, rows, max_col_width=60)


@environments_group.command("get")
@click.argument("env_id")
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def environments_get(click_ctx, env_id: str, output_json: bool) -> None:
    """Get environment ENV_ID."""
    ctx = click_ctx.obj
    _require_token(ctx)
    _require_workspace(ctx)
    use_json = output_json or ctx.output_json
    try:
        client = EnvironmentsClient(
            backend=ctx.backend(), workspace_id=ctx.workspace_id
        )
        result = client.get(env_id)
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return

    if use_json:
        _print_json(result)
    else:
        skin.status("id", result.get("id") or result.get("_id", ""))
        skin.status("name", result.get("name", ""))
        skin.status("slug", result.get("slug", ""))
        if "position" in result:
            skin.status("position", str(result.get("position", "")))


@environments_group.command("create")
@click.argument("name")
@click.argument("slug")
@click.option("--position", type=int, default=None, help="Ordering position.")
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def environments_create(
    click_ctx, name: str, slug: str, position: int | None, output_json: bool
) -> None:
    """Create a new environment NAME with SLUG."""
    ctx = click_ctx.obj
    _require_token(ctx)
    _require_workspace(ctx)
    use_json = output_json or ctx.output_json
    try:
        client = EnvironmentsClient(
            backend=ctx.backend(), workspace_id=ctx.workspace_id
        )
        result = client.create(name=name, slug=slug, position=position)
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return

    if use_json:
        _print_json(result)
    else:
        eid = result.get("id") or result.get("_id", "")
        skin.success(f"Environment '{name}' (slug: {slug}) created (id: {eid}).")


@environments_group.command("rename")
@click.argument("env_id")
@click.option("--name", "name", default=None, help="New display name.")
@click.option("--slug", "slug", default=None, help="New slug.")
@click.option("--position", type=int, default=None, help="New position.")
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def environments_rename(
    click_ctx,
    env_id: str,
    name: str | None,
    slug: str | None,
    position: int | None,
    output_json: bool,
) -> None:
    """Update environment ENV_ID (at least one of --name/--slug/--position required)."""
    ctx = click_ctx.obj
    _require_token(ctx)
    _require_workspace(ctx)
    use_json = output_json or ctx.output_json

    if name is None and slug is None and position is None:
        skin.error(
            "At least one of --name, --slug, or --position is required."
        )
        sys.exit(1)

    try:
        client = EnvironmentsClient(
            backend=ctx.backend(), workspace_id=ctx.workspace_id
        )
        result = client.update(
            env_id=env_id, name=name, slug=slug, position=position
        )
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return

    if use_json:
        _print_json(result)
    else:
        skin.success(f"Environment '{env_id}' updated.")


@environments_group.command("delete")
@click.argument("env_id")
@click.option("--yes", is_flag=True, default=False, help="Skip confirmation.")
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def environments_delete(
    click_ctx, env_id: str, yes: bool, output_json: bool
) -> None:
    """Delete environment ENV_ID."""
    ctx = click_ctx.obj
    _require_token(ctx)
    _require_workspace(ctx)
    use_json = output_json or ctx.output_json

    if not yes:
        if not click.confirm(
            f"Delete environment '{env_id}'?", default=False
        ):
            skin.info("Aborted.")
            return

    try:
        client = EnvironmentsClient(
            backend=ctx.backend(), workspace_id=ctx.workspace_id
        )
        result = client.delete(env_id)
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return

    if use_json:
        _print_json(result)
    else:
        skin.success(f"Environment '{env_id}' deleted.")


__all__ = ["EnvironmentsClient", "environments_group"]
