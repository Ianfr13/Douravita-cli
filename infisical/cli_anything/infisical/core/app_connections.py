"""Read-only app-connections commands for Infisical CLI."""

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
# Client (read-only)
# ---------------------------------------------------------------------------


class AppConnectionsClient:
    """Read-only client for app connections."""

    def __init__(self, backend: InfisicalBackend):
        self.backend = backend

    def list(
        self, app: str | None = None, connection_name: str | None = None
    ) -> list[dict]:
        return self.backend.list_app_connections(
            app=app, connection_name=connection_name
        )

    def options(self) -> list[dict]:
        return self.backend.list_app_connection_options()


# ---------------------------------------------------------------------------
# Click group
# ---------------------------------------------------------------------------


@click.group("app-connections")
def app_connections_group() -> None:
    """List app connections and supported apps (read-only)."""


@app_connections_group.command("list")
@click.option("--app", default=None, help="Filter by app (e.g. aws, github).")
@click.option("--connection-name", "connection_name", default=None,
              help="Filter by connection name.")
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def ac_list(
    click_ctx: click.Context,
    app: str | None,
    connection_name: str | None,
    output_json: bool,
) -> None:
    """List app connections."""
    ctx = click_ctx.obj
    _require_token(ctx)
    use_json = output_json or ctx.output_json
    try:
        client = AppConnectionsClient(ctx.backend())
        result = client.list(app=app, connection_name=connection_name)
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return
    if use_json:
        _print_json(result)
        return
    if not result:
        skin.info("No app connections found.")
        return
    headers = ["ID", "NAME", "APP", "METHOD", "CREATED_AT"]
    rows = []
    for c in result:
        rows.append([
            str(c.get("id", c.get("_id", ""))),
            str(c.get("name", "")),
            str(c.get("app", "")),
            str(c.get("method", "")),
            str(c.get("createdAt", "")),
        ])
    skin.table(headers, rows, max_col_width=60)


@app_connections_group.command("options")
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def ac_options(click_ctx: click.Context, output_json: bool) -> None:
    """List supported app-connection apps."""
    ctx = click_ctx.obj
    _require_token(ctx)
    use_json = output_json or ctx.output_json
    try:
        client = AppConnectionsClient(ctx.backend())
        result = client.options()
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return
    if use_json:
        _print_json(result)
        return
    if not result:
        skin.info("No app-connection options available.")
        return
    for opt in result:
        if isinstance(opt, dict):
            app_name = opt.get("app") or opt.get("name") or ""
            label = opt.get("label") or opt.get("displayName") or ""
            if label and label != app_name:
                click.echo(f"- {app_name} ({label})")
            else:
                click.echo(f"- {app_name}")
        else:
            click.echo(f"- {opt}")


__all__ = ["AppConnectionsClient", "app_connections_group"]
