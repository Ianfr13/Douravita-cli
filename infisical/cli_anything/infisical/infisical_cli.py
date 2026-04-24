"""Main CLI entry point for cli-anything-infisical."""

from __future__ import annotations

import json
import os
import sys

import click

from cli_anything.infisical.utils.infisical_backend import (
    InfisicalBackend,
    InfisicalAPIError,
)
from cli_anything.infisical.core.secrets import SecretsClient
from cli_anything.infisical.core.projects import ProjectsClient
from cli_anything.infisical.core.secrets_ext import secrets_ext_group
from cli_anything.infisical.core.folders import folders_group
from cli_anything.infisical.core.environments import environments_group
from cli_anything.infisical.core.projects_ext import projects_ext_group
from cli_anything.infisical.core.snapshots import snapshots_group
from cli_anything.infisical.core.tags import tags_group
from cli_anything.infisical.core.secret_imports import secret_imports_group
from cli_anything.infisical.core.identities import identities_group, auth_group
from cli_anything.infisical.core.audit import audit_group
from cli_anything.infisical.core.dynamic_secrets import dynamic_secrets_group
from cli_anything.infisical.core.groups import groups_group
from cli_anything.infisical.core.app_connections import app_connections_group
from cli_anything.infisical.utils.repl_skin import ReplSkin

# ---------------------------------------------------------------------------
# Default constants
# ---------------------------------------------------------------------------

DEFAULT_URL = "https://sec.douravita.com.br"
DEFAULT_ENV = "dev"

# ---------------------------------------------------------------------------
# Shared context object
# ---------------------------------------------------------------------------


class CliContext:
    """Holds shared configuration for all commands."""

    def __init__(
        self,
        token: str,
        workspace_id: str,
        environment: str,
        base_url: str,
        output_json: bool,
    ):
        self.token = token
        self.workspace_id = workspace_id
        self.environment = environment
        self.base_url = base_url
        self.output_json = output_json

    def backend(self) -> InfisicalBackend:
        return InfisicalBackend(base_url=self.base_url, token=self.token)

    def secrets_client(self) -> SecretsClient:
        return SecretsClient(
            backend=self.backend(),
            workspace_id=self.workspace_id,
            environment=self.environment,
        )

    def projects_client(self) -> ProjectsClient:
        return ProjectsClient(backend=self.backend())


pass_ctx = click.make_pass_decorator(CliContext)

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

skin = ReplSkin("infisical", version="1.0.0")


def _require_token(ctx: CliContext) -> None:
    if not ctx.token:
        skin.error(
            "Authentication token is required. Set INFISICAL_TOKEN env var "
            "or pass --token."
        )
        sys.exit(1)


def _require_workspace(ctx: CliContext) -> None:
    if not ctx.workspace_id:
        skin.error(
            "Workspace ID is required. Set INFISICAL_WORKSPACE_ID env var "
            "or pass --workspace / -w."
        )
        sys.exit(1)


def _handle_api_error(err: InfisicalAPIError) -> None:
    skin.error(f"API error {err.status_code}:")
    if isinstance(err.body, dict):
        click.echo(json.dumps(err.body, indent=2), err=True)
    else:
        click.echo(str(err.body), err=True)
    sys.exit(1)


def _print_json(data: object) -> None:
    click.echo(json.dumps(data, indent=2))


# ---------------------------------------------------------------------------
# Root group
# ---------------------------------------------------------------------------


@click.group(invoke_without_command=True)
@click.option(
    "--token",
    envvar="INFISICAL_TOKEN",
    default="",
    help="Infisical API token (or set INFISICAL_TOKEN).",
)
@click.option(
    "--workspace",
    "-w",
    envvar="INFISICAL_WORKSPACE_ID",
    default="",
    help="Workspace/project ID (or set INFISICAL_WORKSPACE_ID).",
)
@click.option(
    "--env",
    "-e",
    envvar="INFISICAL_ENV",
    default=DEFAULT_ENV,
    show_default=True,
    help="Target environment (or set INFISICAL_ENV).",
)
@click.option(
    "--url",
    envvar="INFISICAL_URL",
    default=DEFAULT_URL,
    show_default=True,
    help="Infisical base URL (or set INFISICAL_URL).",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    default=False,
    help="Output machine-readable JSON.",
)
@click.pass_context
def main(
    click_ctx: click.Context,
    token: str,
    workspace: str,
    env: str,
    url: str,
    output_json: bool,
) -> None:
    """cli-anything-infisical — Infisical secrets manager CLI.

    Run without a subcommand to enter interactive REPL mode.
    """
    cli_ctx = CliContext(
        token=token,
        workspace_id=workspace,
        environment=env,
        base_url=url,
        output_json=output_json,
    )
    click_ctx.obj = cli_ctx

    if click_ctx.invoked_subcommand is None:
        # Enter REPL mode
        _run_repl(cli_ctx)


# ---------------------------------------------------------------------------
# REPL
# ---------------------------------------------------------------------------


def _run_repl(ctx: CliContext) -> None:
    """Interactive REPL loop."""
    skin.print_banner()

    repl_commands = {
        "secrets list": "List all secrets",
        "secrets get <NAME>": "Get a secret by name",
        "secrets export": "Export secrets as KEY=VALUE",
        "secrets export --json": "Export secrets as JSON",
        "secrets create <NAME> <VALUE>": "Create a new secret",
        "secrets edit <NAME> <VALUE>": "Update an existing secret",
        "projects list": "List all projects",
        "projects create <NAME>": "Create a new project",
        "help": "Show this help",
        "quit / exit": "Exit the REPL",
    }

    session = skin.create_prompt_session()

    while True:
        try:
            raw = skin.get_input(session, context=ctx.environment or "")
        except (EOFError, KeyboardInterrupt):
            skin.print_goodbye()
            break

        line = raw.strip()
        if not line:
            continue

        parts = line.split()
        cmd = parts[0].lower() if parts else ""

        if cmd in ("quit", "exit", "q"):
            skin.print_goodbye()
            break

        if cmd == "help":
            skin.help(repl_commands)
            continue

        # Dispatch to Click commands programmatically
        try:
            main.main(
                args=parts,
                standalone_mode=False,
                obj=ctx,
            )
        except SystemExit:
            pass
        except click.UsageError as exc:
            skin.error(str(exc))
        except Exception as exc:
            skin.error(str(exc))


# ---------------------------------------------------------------------------
# secrets group
# ---------------------------------------------------------------------------


@main.group()
@pass_ctx
def secrets(ctx: CliContext) -> None:
    """Manage secrets for a project/environment."""


@secrets.command("list")
@click.option("--json", "output_json", is_flag=True, default=False)
@pass_ctx
def secrets_list(ctx: CliContext, output_json: bool) -> None:
    """List all secrets (names + values) for the configured project/environment."""
    _require_token(ctx)
    _require_workspace(ctx)
    use_json = output_json or ctx.output_json
    try:
        client = ctx.secrets_client()
        result = client.list()
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return

    if use_json:
        _print_json(result)
    else:
        if not result:
            skin.info("No secrets found.")
            return
        headers = ["NAME", "VALUE"]
        rows = []
        for s in result:
            key = s.get("secretKey") or s.get("key") or s.get("name", "")
            val = s.get("secretValue") or s.get("value", "")
            rows.append([key, val])
        skin.table(headers, rows, max_col_width=60)


@secrets.command("get")
@click.argument("name")
@click.option("--json", "output_json", is_flag=True, default=False)
@pass_ctx
def secrets_get(ctx: CliContext, name: str, output_json: bool) -> None:
    """Get a specific secret by NAME."""
    _require_token(ctx)
    _require_workspace(ctx)
    use_json = output_json or ctx.output_json
    try:
        client = ctx.secrets_client()
        result = client.get(name)
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return

    if use_json:
        _print_json(result)
    else:
        key = result.get("secretKey") or result.get("key") or result.get("name", name)
        val = result.get("secretValue") or result.get("value", "")
        skin.status(key, val)


@secrets.command("export")
@click.option("--json", "output_json", is_flag=True, default=False)
@pass_ctx
def secrets_export(ctx: CliContext, output_json: bool) -> None:
    """Export all secrets as KEY=VALUE lines (or JSON with --json)."""
    _require_token(ctx)
    _require_workspace(ctx)
    use_json = output_json or ctx.output_json
    try:
        client = ctx.secrets_client()
        result = client.list()
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return

    if use_json:
        export = {}
        for s in result:
            key = s.get("secretKey") or s.get("key") or s.get("name", "")
            val = s.get("secretValue") or s.get("value", "")
            export[key] = val
        _print_json(export)
    else:
        for s in result:
            key = s.get("secretKey") or s.get("key") or s.get("name", "")
            val = s.get("secretValue") or s.get("value", "")
            click.echo(f"{key}={val}")


@secrets.command("create")
@click.argument("name")
@click.argument("value")
@click.option("--json", "output_json", is_flag=True, default=False)
@pass_ctx
def secrets_create(ctx: CliContext, name: str, value: str, output_json: bool) -> None:
    """Create a new secret with NAME and VALUE."""
    _require_token(ctx)
    _require_workspace(ctx)
    use_json = output_json or ctx.output_json
    try:
        client = ctx.secrets_client()
        result = client.create(name, value)
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return

    if use_json:
        _print_json(result)
    else:
        skin.success(f"Secret '{name}' created.")


@secrets.command("edit")
@click.argument("name")
@click.argument("value")
@click.option("--json", "output_json", is_flag=True, default=False)
@pass_ctx
def secrets_edit(ctx: CliContext, name: str, value: str, output_json: bool) -> None:
    """Update an existing secret with NAME and new VALUE."""
    _require_token(ctx)
    _require_workspace(ctx)
    use_json = output_json or ctx.output_json
    try:
        client = ctx.secrets_client()
        result = client.update(name, value)
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return

    if use_json:
        _print_json(result)
    else:
        skin.success(f"Secret '{name}' updated.")


# ---------------------------------------------------------------------------
# projects group
# ---------------------------------------------------------------------------


@main.group()
@pass_ctx
def projects(ctx: CliContext) -> None:
    """Manage Infisical projects (workspaces)."""


@projects.command("list")
@click.option("--json", "output_json", is_flag=True, default=False)
@pass_ctx
def projects_list(ctx: CliContext, output_json: bool) -> None:
    """List all accessible projects/workspaces."""
    _require_token(ctx)
    use_json = output_json or ctx.output_json
    try:
        client = ctx.projects_client()
        result = client.list()
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return

    if use_json:
        _print_json(result)
    else:
        if not result:
            skin.info("No projects found.")
            return
        headers = ["ID", "NAME", "ORG ID"]
        rows = []
        for p in result:
            pid = p.get("id", p.get("_id", ""))
            name = p.get("name", "")
            org = p.get("organization", p.get("orgId", ""))
            rows.append([pid, name, org])
        skin.table(headers, rows, max_col_width=40)


@projects.command("create")
@click.argument("name")
@click.option(
    "--org-id",
    envvar="INFISICAL_ORG_ID",
    default="",
    help="Organization ID (or set INFISICAL_ORG_ID).",
)
@click.option("--json", "output_json", is_flag=True, default=False)
@pass_ctx
def projects_create(
    ctx: CliContext, name: str, org_id: str, output_json: bool
) -> None:
    """Create a new project/workspace with NAME."""
    _require_token(ctx)
    if not org_id:
        skin.error(
            "Organization ID is required. Set INFISICAL_ORG_ID env var "
            "or pass --org-id."
        )
        sys.exit(1)
    use_json = output_json or ctx.output_json
    try:
        client = ctx.projects_client()
        result = client.create(name, org_id)
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return

    if use_json:
        _print_json(result)
    else:
        pid = result.get("id") or result.get("_id", "")
        skin.success(f"Project '{name}' created (id: {pid}).")


# ---------------------------------------------------------------------------
# Register extended groups from core/*.py modules
# ---------------------------------------------------------------------------

main.add_command(secrets_ext_group)
main.add_command(folders_group)
main.add_command(environments_group)
main.add_command(projects_ext_group)
main.add_command(snapshots_group)
main.add_command(tags_group)
main.add_command(secret_imports_group)
main.add_command(identities_group)
main.add_command(auth_group)
main.add_command(audit_group)
main.add_command(dynamic_secrets_group)
main.add_command(groups_group)
main.add_command(app_connections_group)
