"""Secret snapshots: list and rollback."""

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


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------


class SnapshotsClient:
    """High-level client for workspace secret-snapshot operations."""

    def __init__(
        self,
        backend: InfisicalBackend,
        workspace_id: str,
        environment: str | None = None,
    ):
        self.backend = backend
        self.workspace_id = workspace_id
        self.environment = environment

    def list(
        self,
        environment: str | None = None,
        folder_id: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict]:
        return self.backend.list_snapshots(
            workspace_id=self.workspace_id,
            environment=environment or self.environment,
            folder_id=folder_id,
            limit=limit,
            offset=offset,
        )

    def rollback(self, snapshot_id: str) -> dict:
        return self.backend.rollback_snapshot(snapshot_id)


# ---------------------------------------------------------------------------
# snapshots group
# ---------------------------------------------------------------------------


@click.group("snapshots")
def snapshots_group():
    """Manage workspace secret snapshots."""


@snapshots_group.command("list")
@click.option("--env", "env", default=None, help="Environment slug (defaults to context).")
@click.option("--folder-id", "folder_id", default=None, help="Folder ID to filter by.")
@click.option("--limit", default=20, show_default=True, type=int)
@click.option("--offset", default=0, show_default=True, type=int)
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def snapshots_list(
    click_ctx,
    env,
    folder_id,
    limit: int,
    offset: int,
    output_json: bool,
) -> None:
    """List secret snapshots for the workspace/environment."""
    ctx = click_ctx.obj
    _require_token(ctx)
    _require_workspace(ctx)
    environment = env or ctx.environment
    use_json = output_json or ctx.output_json
    try:
        client = SnapshotsClient(ctx.backend(), ctx.workspace_id, environment)
        result = client.list(
            environment=environment,
            folder_id=folder_id,
            limit=limit,
            offset=offset,
        )
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return

    if use_json:
        _print_json(result)
    else:
        if not result:
            skin.info("No snapshots found.")
            return
        headers = ["ID", "ENV", "CREATED_AT", "FOLDER_ID"]
        rows = []
        for s in result:
            sid = s.get("id") or s.get("_id") or ""
            env_val = (
                s.get("environment")
                or (s.get("envSlug") if isinstance(s.get("envSlug"), str) else "")
                or ""
            )
            if isinstance(env_val, dict):
                env_val = env_val.get("slug") or env_val.get("name") or ""
            created = s.get("createdAt") or s.get("created_at") or ""
            fid = s.get("folderId") or s.get("folder_id") or ""
            rows.append([str(sid), str(env_val), str(created), str(fid)])
        skin.table(headers, rows, max_col_width=60)


@snapshots_group.command("rollback")
@click.argument("snapshot_id")
@click.option("--yes", is_flag=True, default=False, help="Confirm rollback.")
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def snapshots_rollback(
    click_ctx, snapshot_id: str, yes: bool, output_json: bool
) -> None:
    """Rollback the workspace to SNAPSHOT_ID (requires --yes)."""
    ctx = click_ctx.obj
    _require_token(ctx)

    if not yes:
        skin.error("Refusing to rollback. Pass --yes to confirm.")
        import sys
        sys.exit(1)

    use_json = output_json or ctx.output_json
    try:
        backend = ctx.backend()
        result = backend.rollback_snapshot(snapshot_id)
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return

    if use_json:
        _print_json(result)
    else:
        skin.success(f"Rolled back to snapshot '{snapshot_id}'.")


__all__ = ["SnapshotsClient", "snapshots_group"]
