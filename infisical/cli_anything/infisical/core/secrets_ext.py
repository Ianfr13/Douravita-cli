"""Extended secrets operations for Infisical CLI.

Provides delete / move / rename / bulk / tag / history / rollback operations
that extend the baseline ``secrets`` group defined in ``infisical_cli.py``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from cli_anything.infisical.core.secrets import SecretsClient
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


def _parse_dotenv(text: str) -> list[tuple[str, str]]:
    """Parse a .env-style file into (key, value) tuples.

    Strips comments and blank lines. Removes optional surrounding quotes on values.
    """
    pairs: list[tuple[str, str]] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        if key:
            pairs.append((key, value))
    return pairs


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------


class SecretsExtClient(SecretsClient):
    """Extended secrets operations (delete/move/rename/bulk/tag/history/rollback)."""

    def delete(self, name: str) -> dict:
        return self.backend.delete_secret(
            secret_name=name,
            workspace_id=self.workspace_id,
            environment=self.environment,
            secret_path=self.secret_path,
        )

    def rename(self, old_name: str, new_name: str) -> dict:
        return self.backend.update_secret(
            secret_name=old_name,
            workspace_id=self.workspace_id,
            environment=self.environment,
            secret_path=self.secret_path,
            new_secret_name=new_name,
        )

    def resolve_secret_ids(self, names: list[str]) -> list[str]:
        """Look up secret IDs for a list of secret names in the current env/path."""
        all_secrets = self.backend.list_secrets(
            workspace_id=self.workspace_id,
            environment=self.environment,
            secret_path=self.secret_path,
        )
        wanted = set(names)
        ids: list[str] = []
        missing: list[str] = []
        found_names: set[str] = set()
        for s in all_secrets:
            key = s.get("secretKey") or s.get("key") or s.get("name")
            if key in wanted:
                sid = s.get("id") or s.get("_id")
                if sid:
                    ids.append(sid)
                    found_names.add(key)
        for n in names:
            if n not in found_names:
                missing.append(n)
        if missing:
            raise ValueError(
                f"Could not find secrets by name: {', '.join(missing)}"
            )
        return ids

    def move(
        self,
        names: list[str],
        to_env: str,
        to_path: str,
        should_overwrite: bool = False,
    ) -> dict:
        ids = self.resolve_secret_ids(names)
        return self.backend.move_secrets(
            project_id=self.workspace_id,
            source_environment=self.environment,
            source_secret_path=self.secret_path,
            destination_environment=to_env,
            destination_secret_path=to_path,
            secret_ids=ids,
            should_overwrite=should_overwrite,
        )

    def bulk_create(self, pairs: list[tuple[str, str]]) -> dict:
        return self.backend.bulk_create_secrets(
            workspace_id=self.workspace_id,
            environment=self.environment,
            secret_path=self.secret_path,
            secrets=[
                {"secretKey": k, "secretValue": v} for k, v in pairs
            ],
        )

    def bulk_delete(self, names: list[str]) -> dict:
        return self.backend.bulk_delete_secrets(
            workspace_id=self.workspace_id,
            environment=self.environment,
            secret_path=self.secret_path,
            secrets=[{"secretKey": n} for n in names],
        )

    def tag(self, name: str, project_slug: str, tag_slugs: list[str]) -> dict:
        return self.backend.attach_tags_to_secret(
            secret_name=name,
            project_slug=project_slug,
            environment=self.environment,
            secret_path=self.secret_path,
            tag_slugs=tag_slugs,
        )

    def untag(self, name: str, project_slug: str, tag_slugs: list[str]) -> dict:
        return self.backend.detach_tags_from_secret(
            secret_name=name,
            project_slug=project_slug,
            environment=self.environment,
            secret_path=self.secret_path,
            tag_slugs=tag_slugs,
        )

    def history(self, secret_id: str, limit: int = 20) -> list[dict]:
        return self.backend.list_secret_versions(
            secret_id=secret_id, limit=limit
        )

    def rollback(self, secret_version_id: str) -> dict:
        return self.backend.rollback_secret_version(
            secret_version_id=secret_version_id
        )


def _make_client(ctx) -> SecretsExtClient:
    return SecretsExtClient(
        backend=ctx.backend(),
        workspace_id=ctx.workspace_id,
        environment=ctx.environment,
    )


# ---------------------------------------------------------------------------
# Click group
# ---------------------------------------------------------------------------


@click.group("secrets-x")
def secrets_ext_group() -> None:
    """Extended secrets operations (delete/move/rename/bulk/tag/history)."""


@secrets_ext_group.command("delete")
@click.argument("name")
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def cmd_delete(click_ctx, name: str, output_json: bool) -> None:
    """Delete secret NAME."""
    ctx = click_ctx.obj
    _require_token(ctx)
    _require_workspace(ctx)
    use_json = output_json or ctx.output_json
    try:
        client = _make_client(ctx)
        result = client.delete(name)
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return

    if use_json:
        _print_json(result)
    else:
        skin.success(f"Deleted secret '{name}'.")


@secrets_ext_group.command("move")
@click.argument("names", nargs=-1, required=True)
@click.option("--to-env", "to_env", required=True, help="Destination environment.")
@click.option("--to-path", "to_path", required=True, help="Destination secret path.")
@click.option(
    "--overwrite",
    is_flag=True,
    default=False,
    help="Overwrite existing secrets at destination.",
)
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def cmd_move(
    click_ctx,
    names: tuple[str, ...],
    to_env: str,
    to_path: str,
    overwrite: bool,
    output_json: bool,
) -> None:
    """Move one or more secrets NAMES to --to-env / --to-path."""
    ctx = click_ctx.obj
    _require_token(ctx)
    _require_workspace(ctx)
    use_json = output_json or ctx.output_json
    try:
        client = _make_client(ctx)
        result = client.move(
            names=list(names),
            to_env=to_env,
            to_path=to_path,
            should_overwrite=overwrite,
        )
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return
    except ValueError as err:
        skin.error(str(err))
        sys.exit(1)

    if use_json:
        _print_json(result)
    else:
        skin.success(
            f"Moved {len(names)} secret(s) to env '{to_env}' at '{to_path}'."
        )


@secrets_ext_group.command("rename")
@click.argument("old_name")
@click.argument("new_name")
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def cmd_rename(
    click_ctx, old_name: str, new_name: str, output_json: bool
) -> None:
    """Rename secret OLD_NAME to NEW_NAME."""
    ctx = click_ctx.obj
    _require_token(ctx)
    _require_workspace(ctx)
    use_json = output_json or ctx.output_json
    try:
        client = _make_client(ctx)
        result = client.rename(old_name, new_name)
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return

    if use_json:
        _print_json(result)
    else:
        skin.success(f"Renamed secret '{old_name}' to '{new_name}'.")


@secrets_ext_group.command("bulk-create")
@click.option(
    "--file",
    "file_path",
    required=True,
    type=click.Path(exists=True, dir_okay=False, readable=True),
    help=".env-style file of KEY=VALUE lines.",
)
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def cmd_bulk_create(click_ctx, file_path: str, output_json: bool) -> None:
    """Bulk-create secrets from a .env-style FILE."""
    ctx = click_ctx.obj
    _require_token(ctx)
    _require_workspace(ctx)
    use_json = output_json or ctx.output_json

    try:
        text = Path(file_path).read_text(encoding="utf-8")
    except OSError as exc:
        skin.error(f"Could not read file: {exc}")
        sys.exit(1)

    pairs = _parse_dotenv(text)
    if not pairs:
        skin.error("No KEY=VALUE pairs found in file.")
        sys.exit(1)

    try:
        client = _make_client(ctx)
        result = client.bulk_create(pairs)
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return

    if use_json:
        _print_json(result)
    else:
        skin.success(f"Bulk-created {len(pairs)} secret(s) from '{file_path}'.")


@secrets_ext_group.command("bulk-delete")
@click.argument("names", nargs=-1, required=True)
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def cmd_bulk_delete(
    click_ctx, names: tuple[str, ...], output_json: bool
) -> None:
    """Bulk-delete secrets by NAMES."""
    ctx = click_ctx.obj
    _require_token(ctx)
    _require_workspace(ctx)
    use_json = output_json or ctx.output_json
    try:
        client = _make_client(ctx)
        result = client.bulk_delete(list(names))
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return

    if use_json:
        _print_json(result)
    else:
        skin.success(f"Bulk-deleted {len(names)} secret(s).")


@secrets_ext_group.command("tag")
@click.argument("name")
@click.argument("tag_slugs", nargs=-1, required=True)
@click.option(
    "--project-slug",
    "project_slug",
    required=True,
    help="Project slug (required for tag operations).",
)
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def cmd_tag(
    click_ctx,
    name: str,
    tag_slugs: tuple[str, ...],
    project_slug: str,
    output_json: bool,
) -> None:
    """Attach TAG_SLUGS to secret NAME."""
    ctx = click_ctx.obj
    _require_token(ctx)
    _require_workspace(ctx)
    use_json = output_json or ctx.output_json
    try:
        client = _make_client(ctx)
        result = client.tag(
            name=name, project_slug=project_slug, tag_slugs=list(tag_slugs)
        )
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return

    if use_json:
        _print_json(result)
    else:
        skin.success(
            f"Attached tag(s) {', '.join(tag_slugs)} to secret '{name}'."
        )


@secrets_ext_group.command("untag")
@click.argument("name")
@click.argument("tag_slugs", nargs=-1, required=True)
@click.option(
    "--project-slug",
    "project_slug",
    required=True,
    help="Project slug (required for tag operations).",
)
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def cmd_untag(
    click_ctx,
    name: str,
    tag_slugs: tuple[str, ...],
    project_slug: str,
    output_json: bool,
) -> None:
    """Detach TAG_SLUGS from secret NAME."""
    ctx = click_ctx.obj
    _require_token(ctx)
    _require_workspace(ctx)
    use_json = output_json or ctx.output_json
    try:
        client = _make_client(ctx)
        result = client.untag(
            name=name, project_slug=project_slug, tag_slugs=list(tag_slugs)
        )
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return

    if use_json:
        _print_json(result)
    else:
        skin.success(
            f"Detached tag(s) {', '.join(tag_slugs)} from secret '{name}'."
        )


@secrets_ext_group.command("history")
@click.argument("secret_id")
@click.option("--limit", type=int, default=20, show_default=True, help="Max versions.")
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def cmd_history(
    click_ctx, secret_id: str, limit: int, output_json: bool
) -> None:
    """List version history for SECRET_ID."""
    ctx = click_ctx.obj
    _require_token(ctx)
    use_json = output_json or ctx.output_json
    try:
        client = _make_client(ctx)
        result = client.history(secret_id=secret_id, limit=limit)
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return

    if use_json:
        _print_json(result)
    else:
        if not result:
            skin.info("No versions found.")
            return
        headers = ["VERSION ID", "VERSION", "KEY", "CREATED AT"]
        rows = []
        for v in result:
            vid = v.get("id") or v.get("_id", "")
            ver = str(v.get("version", ""))
            key = v.get("secretKey") or v.get("key", "")
            created = v.get("createdAt", "")
            rows.append([vid, ver, key, created])
        skin.table(headers, rows, max_col_width=60)


@secrets_ext_group.command("rollback")
@click.argument("secret_version_id")
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def cmd_rollback(
    click_ctx, secret_version_id: str, output_json: bool
) -> None:
    """Rollback a secret to SECRET_VERSION_ID."""
    ctx = click_ctx.obj
    _require_token(ctx)
    use_json = output_json or ctx.output_json
    try:
        client = _make_client(ctx)
        result = client.rollback(secret_version_id)
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return

    if use_json:
        _print_json(result)
    else:
        skin.success(f"Rolled back to version '{secret_version_id}'.")


__all__ = ["SecretsExtClient", "secrets_ext_group"]
