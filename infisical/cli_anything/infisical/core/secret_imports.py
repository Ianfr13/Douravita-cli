"""Secret imports operations for Infisical CLI."""

from __future__ import annotations

import click

from cli_anything.infisical.utils.infisical_backend import (
    InfisicalBackend,
    InfisicalAPIError,
)
from cli_anything.infisical.utils.repl_skin import ReplSkin


skin = ReplSkin("infisical", version="1.1.0")


def _handle_api_error(err):
    import json, sys, click
    skin.error(f"API error {err.status_code}:")
    if isinstance(err.body, dict):
        click.echo(json.dumps(err.body, indent=2), err=True)
    else:
        click.echo(str(err.body), err=True)
    sys.exit(1)


def _require_token(ctx):
    if not ctx.token:
        skin.error("Authentication token is required. Set INFISICAL_TOKEN or pass --token.")
        import sys
        sys.exit(1)


def _require_workspace(ctx):
    if not ctx.workspace_id:
        skin.error("Workspace ID is required. Set INFISICAL_WORKSPACE_ID or pass --workspace/-w.")
        import sys
        sys.exit(1)


def _print_json(data):
    import json, click
    click.echo(json.dumps(data, indent=2))


class SecretImportsClient:
    """High-level client for secret-import operations."""

    def __init__(
        self,
        backend: InfisicalBackend,
        workspace_id: str,
        environment: str,
    ):
        self.backend = backend
        self.workspace_id = workspace_id
        self.environment = environment

    def list(self, path: str = "/") -> list[dict]:
        return self.backend.list_secret_imports(
            workspace_id=self.workspace_id,
            environment=self.environment,
            path=path,
        )

    def create(
        self,
        from_env: str,
        from_path: str,
        path: str = "/",
        is_replication: bool = False,
    ) -> dict:
        return self.backend.create_secret_import(
            workspace_id=self.workspace_id,
            environment=self.environment,
            import_environment=from_env,
            import_path=from_path,
            path=path,
            is_replication=is_replication,
        )

    def update(
        self,
        import_id: str,
        from_env: str | None = None,
        from_path: str | None = None,
        path: str = "/",
        position: int | None = None,
    ) -> dict:
        return self.backend.update_secret_import(
            secret_import_id=import_id,
            workspace_id=self.workspace_id,
            environment=self.environment,
            import_environment=from_env,
            import_path=from_path,
            path=path,
            position=position,
        )

    def delete(self, import_id: str, path: str = "/") -> dict:
        return self.backend.delete_secret_import(
            secret_import_id=import_id,
            workspace_id=self.workspace_id,
            environment=self.environment,
            path=path,
        )


# ---------------------------------------------------------------------------
# Click group
# ---------------------------------------------------------------------------


@click.group("imports")
def secret_imports_group() -> None:
    """Manage secret imports between environments/paths."""


@secret_imports_group.command("list")
@click.option("--path", default="/", show_default=True, help="Secret path.")
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def imports_list(click_ctx: click.Context, path: str, output_json: bool) -> None:
    """List secret imports for the current env/path."""
    ctx = click_ctx.obj
    _require_token(ctx)
    _require_workspace(ctx)
    use_json = output_json or ctx.output_json
    try:
        client = SecretImportsClient(
            backend=ctx.backend(),
            workspace_id=ctx.workspace_id,
            environment=ctx.environment,
        )
        result = client.list(path=path)
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return

    if use_json:
        _print_json(result)
    else:
        if not result:
            skin.info("No secret imports found.")
            return
        headers = ["ID", "FROM_ENV", "FROM_PATH", "POSITION"]
        rows = []
        for imp in result:
            iid = imp.get("id") or imp.get("_id", "")
            imp_info = imp.get("import") or {}
            from_env = (
                imp.get("importEnv", {}).get("slug")
                or imp.get("importEnv", {}).get("name")
                or imp_info.get("environment", "")
            )
            from_path = imp.get("importPath") or imp_info.get("path", "")
            position = imp.get("position", imp_info.get("position", ""))
            rows.append([str(iid), str(from_env), str(from_path), str(position)])
        skin.table(headers, rows, max_col_width=60)


@secret_imports_group.command("create")
@click.option("--from-env", "from_env", required=True, help="Source environment.")
@click.option("--from-path", "from_path", required=True, help="Source path.")
@click.option("--path", default="/", show_default=True, help="Destination path.")
@click.option("--replication", is_flag=True, default=False, help="Enable replication.")
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def imports_create(
    click_ctx: click.Context,
    from_env: str,
    from_path: str,
    path: str,
    replication: bool,
    output_json: bool,
) -> None:
    """Create a new secret import."""
    ctx = click_ctx.obj
    _require_token(ctx)
    _require_workspace(ctx)
    use_json = output_json or ctx.output_json
    try:
        client = SecretImportsClient(
            backend=ctx.backend(),
            workspace_id=ctx.workspace_id,
            environment=ctx.environment,
        )
        result = client.create(
            from_env=from_env,
            from_path=from_path,
            path=path,
            is_replication=replication,
        )
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return

    if use_json:
        _print_json(result)
    else:
        iid = result.get("id") or result.get("_id", "")
        skin.success(f"Secret import created (id: {iid}).")


@secret_imports_group.command("update")
@click.argument("import_id")
@click.option("--from-env", "from_env", default=None, help="New source environment.")
@click.option("--from-path", "from_path", default=None, help="New source path.")
@click.option("--path", default="/", show_default=True, help="Destination path.")
@click.option("--position", type=int, default=None, help="New position.")
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def imports_update(
    click_ctx: click.Context,
    import_id: str,
    from_env: str | None,
    from_path: str | None,
    path: str,
    position: int | None,
    output_json: bool,
) -> None:
    """Update an existing secret import."""
    ctx = click_ctx.obj
    _require_token(ctx)
    _require_workspace(ctx)
    if from_env is None and from_path is None and position is None:
        skin.error("At least one of --from-env, --from-path, or --position is required.")
        import sys
        sys.exit(1)
    use_json = output_json or ctx.output_json
    try:
        client = SecretImportsClient(
            backend=ctx.backend(),
            workspace_id=ctx.workspace_id,
            environment=ctx.environment,
        )
        result = client.update(
            import_id=import_id,
            from_env=from_env,
            from_path=from_path,
            path=path,
            position=position,
        )
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return

    if use_json:
        _print_json(result)
    else:
        skin.success(f"Secret import '{import_id}' updated.")


@secret_imports_group.command("delete")
@click.argument("import_id")
@click.option("--path", default="/", show_default=True, help="Destination path.")
@click.option("--yes", is_flag=True, required=True, help="Confirm deletion.")
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def imports_delete(
    click_ctx: click.Context,
    import_id: str,
    path: str,
    yes: bool,
    output_json: bool,
) -> None:
    """Delete a secret import."""
    ctx = click_ctx.obj
    _require_token(ctx)
    _require_workspace(ctx)
    use_json = output_json or ctx.output_json
    try:
        client = SecretImportsClient(
            backend=ctx.backend(),
            workspace_id=ctx.workspace_id,
            environment=ctx.environment,
        )
        result = client.delete(import_id=import_id, path=path)
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return

    if use_json:
        _print_json(result)
    else:
        skin.success(f"Secret import '{import_id}' deleted.")


__all__ = ["SecretImportsClient", "secret_imports_group"]
