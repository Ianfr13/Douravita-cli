"""Folder operations for Infisical CLI."""

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
# Local helpers (duplicated to avoid circular imports with infisical_cli.py)
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


class FoldersClient:
    """High-level client for folder operations."""

    def __init__(
        self,
        backend: InfisicalBackend,
        workspace_id: str,
        environment: str,
    ):
        self.backend = backend
        self.workspace_id = workspace_id
        self.environment = environment

    def list(self, path: str = "/", recursive: bool = False) -> list[dict]:
        return self.backend.list_folders(
            workspace_id=self.workspace_id,
            environment=self.environment,
            path=path,
            recursive=recursive,
        )

    def get(self, folder_id: str) -> dict:
        return self.backend.get_folder(folder_id)

    def create(
        self, name: str, path: str = "/", description: str | None = None
    ) -> dict:
        return self.backend.create_folder(
            workspace_id=self.workspace_id,
            environment=self.environment,
            name=name,
            path=path,
            description=description,
        )

    def rename(
        self, folder_id: str, new_name: str, path: str = "/"
    ) -> dict:
        return self.backend.update_folder(
            folder_id=folder_id,
            workspace_id=self.workspace_id,
            environment=self.environment,
            name=new_name,
            path=path,
        )

    def delete(self, folder_id_or_name: str, path: str = "/") -> dict:
        return self.backend.delete_folder(
            folder_id_or_name=folder_id_or_name,
            workspace_id=self.workspace_id,
            environment=self.environment,
            path=path,
        )


# ---------------------------------------------------------------------------
# Click group
# ---------------------------------------------------------------------------


@click.group("folders")
def folders_group() -> None:
    """Manage folders within a project/environment."""


@folders_group.command("list")
@click.option("--path", default="/", show_default=True, help="Parent folder path.")
@click.option("--recursive", is_flag=True, default=False, help="List recursively.")
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def folders_list(click_ctx, path: str, recursive: bool, output_json: bool) -> None:
    """List folders under PATH."""
    ctx = click_ctx.obj
    _require_token(ctx)
    _require_workspace(ctx)
    use_json = output_json or ctx.output_json
    try:
        client = FoldersClient(
            backend=ctx.backend(),
            workspace_id=ctx.workspace_id,
            environment=ctx.environment,
        )
        result = client.list(path=path, recursive=recursive)
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return

    if use_json:
        _print_json(result)
    else:
        if not result:
            skin.info("No folders found.")
            return
        headers = ["ID", "NAME", "PATH"]
        rows = []
        for f in result:
            fid = f.get("id") or f.get("_id", "")
            name = f.get("name", "")
            fpath = f.get("path", "")
            rows.append([fid, name, fpath])
        skin.table(headers, rows, max_col_width=60)


@folders_group.command("get")
@click.argument("folder_id")
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def folders_get(click_ctx, folder_id: str, output_json: bool) -> None:
    """Get a folder by FOLDER_ID."""
    ctx = click_ctx.obj
    _require_token(ctx)
    use_json = output_json or ctx.output_json
    try:
        client = FoldersClient(
            backend=ctx.backend(),
            workspace_id=ctx.workspace_id,
            environment=ctx.environment,
        )
        result = client.get(folder_id)
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return

    if use_json:
        _print_json(result)
    else:
        skin.status("id", result.get("id") or result.get("_id", ""))
        skin.status("name", result.get("name", ""))
        skin.status("path", result.get("path", ""))


@folders_group.command("create")
@click.argument("name")
@click.option("--path", default="/", show_default=True, help="Parent folder path.")
@click.option("--description", default=None, help="Optional folder description.")
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def folders_create(
    click_ctx, name: str, path: str, description: str | None, output_json: bool
) -> None:
    """Create a folder NAME under PATH."""
    ctx = click_ctx.obj
    _require_token(ctx)
    _require_workspace(ctx)
    use_json = output_json or ctx.output_json
    try:
        client = FoldersClient(
            backend=ctx.backend(),
            workspace_id=ctx.workspace_id,
            environment=ctx.environment,
        )
        result = client.create(name=name, path=path, description=description)
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return

    if use_json:
        _print_json(result)
    else:
        fid = result.get("id") or result.get("_id", "")
        skin.success(f"Folder '{name}' created (id: {fid}).")


@folders_group.command("rename")
@click.argument("folder_id")
@click.argument("new_name")
@click.option("--path", default="/", show_default=True, help="Parent folder path.")
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def folders_rename(
    click_ctx, folder_id: str, new_name: str, path: str, output_json: bool
) -> None:
    """Rename folder FOLDER_ID to NEW_NAME."""
    ctx = click_ctx.obj
    _require_token(ctx)
    _require_workspace(ctx)
    use_json = output_json or ctx.output_json
    try:
        client = FoldersClient(
            backend=ctx.backend(),
            workspace_id=ctx.workspace_id,
            environment=ctx.environment,
        )
        result = client.rename(folder_id=folder_id, new_name=new_name, path=path)
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return

    if use_json:
        _print_json(result)
    else:
        skin.success(f"Folder '{folder_id}' renamed to '{new_name}'.")


@folders_group.command("delete")
@click.argument("folder_id_or_name")
@click.option("--path", default="/", show_default=True, help="Parent folder path.")
@click.option("--yes", is_flag=True, default=False, help="Skip confirmation.")
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def folders_delete(
    click_ctx,
    folder_id_or_name: str,
    path: str,
    yes: bool,
    output_json: bool,
) -> None:
    """Delete folder FOLDER_ID_OR_NAME."""
    ctx = click_ctx.obj
    _require_token(ctx)
    _require_workspace(ctx)
    use_json = output_json or ctx.output_json

    if not yes:
        if not click.confirm(
            f"Delete folder '{folder_id_or_name}' under '{path}'?", default=False
        ):
            skin.info("Aborted.")
            return

    try:
        client = FoldersClient(
            backend=ctx.backend(),
            workspace_id=ctx.workspace_id,
            environment=ctx.environment,
        )
        result = client.delete(folder_id_or_name=folder_id_or_name, path=path)
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return

    if use_json:
        _print_json(result)
    else:
        skin.success(f"Folder '{folder_id_or_name}' deleted.")


__all__ = ["FoldersClient", "folders_group"]
