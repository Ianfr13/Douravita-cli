"""Dynamic secrets + leases commands for Infisical CLI.

The dynamic-secrets API uses ``projectSlug`` and ``environmentSlug`` rather
than IDs. Because we do not always have the slug on hand, the ``--project-slug``
option defaults to ``ctx.workspace_id`` when unset. This is imperfect: if the
project slug differs from its ID, the caller must pass ``--project-slug``
explicitly (or set ``INFISICAL_PROJECT_SLUG``). Similarly, ``--env-slug``
defaults to ``ctx.environment``.
"""

from __future__ import annotations

import json as _json
import os
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
# Shared helpers (copied from the shared pattern)
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


def _require_workspace(ctx: Any) -> None:
    if not ctx.workspace_id:
        skin.error(
            "Workspace ID is required. Set INFISICAL_WORKSPACE_ID or pass "
            "--workspace/-w."
        )
        sys.exit(1)


def _print_json(data: Any) -> None:
    click.echo(_json.dumps(data, indent=2))


def _resolve_slugs(
    ctx: Any, project_slug: str | None, env_slug: str | None
) -> tuple[str, str]:
    """Resolve project_slug/env_slug, falling back to workspace_id/environment."""
    ps = project_slug or os.environ.get("INFISICAL_PROJECT_SLUG") or ctx.workspace_id
    es = env_slug or ctx.environment
    if not ps:
        skin.error(
            "Project slug is required. Set INFISICAL_PROJECT_SLUG or pass "
            "--project-slug."
        )
        sys.exit(1)
    if not es:
        skin.error(
            "Environment slug is required. Set INFISICAL_ENV or pass --env-slug."
        )
        sys.exit(1)
    return ps, es


def _load_provider_json(value: str) -> dict:
    """Load provider config from a file path or inline JSON string."""
    if value and os.path.isfile(value):
        with open(value, "r", encoding="utf-8") as fh:
            return _json.load(fh)
    try:
        return _json.loads(value)
    except Exception as exc:
        skin.error(f"Invalid --provider-json (not a file and not valid JSON): {exc}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------


class DynamicSecretsClient:
    """High-level client for dynamic secrets + leases."""

    def __init__(
        self,
        backend: InfisicalBackend,
        project_slug: str,
        environment_slug: str,
        path: str = "/",
    ):
        self.backend = backend
        self.project_slug = project_slug
        self.environment_slug = environment_slug
        self.path = path

    # Dynamic secrets

    def list(self) -> list[dict]:
        return self.backend.list_dynamic_secrets(
            self.project_slug, self.environment_slug, self.path
        )

    def get(self, name: str) -> dict:
        return self.backend.get_dynamic_secret(
            name, self.project_slug, self.environment_slug, self.path
        )

    def create(
        self,
        name: str,
        provider: dict,
        default_ttl: str,
        max_ttl: str | None = None,
    ) -> dict:
        return self.backend.create_dynamic_secret(
            name=name,
            project_slug=self.project_slug,
            environment_slug=self.environment_slug,
            provider=provider,
            default_ttl=default_ttl,
            path=self.path,
            max_ttl=max_ttl,
        )

    def update(
        self,
        name: str,
        new_name: str | None = None,
        default_ttl: str | None = None,
        max_ttl: str | None = None,
    ) -> dict:
        return self.backend.update_dynamic_secret(
            name=name,
            project_slug=self.project_slug,
            environment_slug=self.environment_slug,
            path=self.path,
            new_name=new_name,
            default_ttl=default_ttl,
            max_ttl=max_ttl,
        )

    def delete(self, name: str, force: bool = False) -> dict:
        return self.backend.delete_dynamic_secret(
            name=name,
            project_slug=self.project_slug,
            environment_slug=self.environment_slug,
            path=self.path,
            force=force,
        )

    # Leases

    def list_leases(self, name: str) -> list[dict]:
        return self.backend.list_dynamic_secret_leases(
            name, self.project_slug, self.environment_slug, self.path
        )

    def create_lease(self, name: str, ttl: str | None = None) -> dict:
        return self.backend.create_dynamic_secret_lease(
            dynamic_secret_name=name,
            project_slug=self.project_slug,
            environment_slug=self.environment_slug,
            path=self.path,
            ttl=ttl,
        )

    def get_lease(self, lease_id: str) -> dict:
        return self.backend.get_dynamic_secret_lease(lease_id)

    def renew_lease(self, lease_id: str, ttl: str | None = None) -> dict:
        return self.backend.renew_dynamic_secret_lease(
            lease_id=lease_id,
            project_slug=self.project_slug,
            environment_slug=self.environment_slug,
            path=self.path,
            ttl=ttl,
        )

    def delete_lease(self, lease_id: str, force: bool = False) -> dict:
        return self.backend.delete_dynamic_secret_lease(
            lease_id=lease_id,
            project_slug=self.project_slug,
            environment_slug=self.environment_slug,
            path=self.path,
            force=force,
        )


# ---------------------------------------------------------------------------
# Click group
# ---------------------------------------------------------------------------


@click.group("dynamic-secrets")
def dynamic_secrets_group() -> None:
    """Manage dynamic secrets and their leases."""


# --- list ------------------------------------------------------------------


@dynamic_secrets_group.command("list")
@click.option("--project-slug", "project_slug", default=None,
              envvar="INFISICAL_PROJECT_SLUG",
              help="Project slug (defaults to workspace ID if unset).")
@click.option("--env-slug", "env_slug", default=None,
              help="Environment slug (defaults to --env).")
@click.option("--path", default="/", show_default=True, help="Secret path.")
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def ds_list(
    click_ctx: click.Context,
    project_slug: str | None,
    env_slug: str | None,
    path: str,
    output_json: bool,
) -> None:
    """List dynamic secrets at PATH."""
    ctx = click_ctx.obj
    _require_token(ctx)
    ps, es = _resolve_slugs(ctx, project_slug, env_slug)
    use_json = output_json or ctx.output_json
    try:
        client = DynamicSecretsClient(ctx.backend(), ps, es, path)
        result = client.list()
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return

    if use_json:
        _print_json(result)
        return
    if not result:
        skin.info("No dynamic secrets found.")
        return
    headers = ["ID", "NAME", "STATUS", "DEFAULT_TTL", "MAX_TTL"]
    rows = []
    for d in result:
        rows.append([
            str(d.get("id", d.get("_id", ""))),
            str(d.get("name", "")),
            str(d.get("status", "")),
            str(d.get("defaultTTL", "")),
            str(d.get("maxTTL", "")),
        ])
    skin.table(headers, rows, max_col_width=60)


# --- get -------------------------------------------------------------------


@dynamic_secrets_group.command("get")
@click.argument("name")
@click.option("--project-slug", "project_slug", default=None,
              envvar="INFISICAL_PROJECT_SLUG")
@click.option("--env-slug", "env_slug", default=None)
@click.option("--path", default="/", show_default=True)
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def ds_get(
    click_ctx: click.Context,
    name: str,
    project_slug: str | None,
    env_slug: str | None,
    path: str,
    output_json: bool,
) -> None:
    """Get a dynamic secret by NAME."""
    ctx = click_ctx.obj
    _require_token(ctx)
    ps, es = _resolve_slugs(ctx, project_slug, env_slug)
    try:
        client = DynamicSecretsClient(ctx.backend(), ps, es, path)
        result = client.get(name)
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return
    _print_json(result)


# --- create ----------------------------------------------------------------


@dynamic_secrets_group.command("create")
@click.argument("name")
@click.option("--provider-json", "provider_json", required=True,
              help="Path to JSON file or inline JSON string with provider config.")
@click.option("--default-ttl", "default_ttl", required=True,
              help="Default TTL for leases (e.g. 1h).")
@click.option("--max-ttl", "max_ttl", default=None, help="Max TTL (e.g. 24h).")
@click.option("--project-slug", "project_slug", default=None,
              envvar="INFISICAL_PROJECT_SLUG")
@click.option("--env-slug", "env_slug", default=None)
@click.option("--path", default="/", show_default=True)
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def ds_create(
    click_ctx: click.Context,
    name: str,
    provider_json: str,
    default_ttl: str,
    max_ttl: str | None,
    project_slug: str | None,
    env_slug: str | None,
    path: str,
    output_json: bool,
) -> None:
    """Create a new dynamic secret NAME."""
    ctx = click_ctx.obj
    _require_token(ctx)
    ps, es = _resolve_slugs(ctx, project_slug, env_slug)
    provider = _load_provider_json(provider_json)
    use_json = output_json or ctx.output_json
    try:
        client = DynamicSecretsClient(ctx.backend(), ps, es, path)
        result = client.create(name, provider, default_ttl, max_ttl)
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return
    if use_json:
        _print_json(result)
    else:
        skin.success(f"Dynamic secret '{name}' created.")


# --- update ----------------------------------------------------------------


@dynamic_secrets_group.command("update")
@click.argument("name")
@click.option("--new-name", "new_name", default=None)
@click.option("--default-ttl", "default_ttl", default=None)
@click.option("--max-ttl", "max_ttl", default=None)
@click.option("--project-slug", "project_slug", default=None,
              envvar="INFISICAL_PROJECT_SLUG")
@click.option("--env-slug", "env_slug", default=None)
@click.option("--path", default="/", show_default=True)
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def ds_update(
    click_ctx: click.Context,
    name: str,
    new_name: str | None,
    default_ttl: str | None,
    max_ttl: str | None,
    project_slug: str | None,
    env_slug: str | None,
    path: str,
    output_json: bool,
) -> None:
    """Update a dynamic secret NAME (at least one change)."""
    ctx = click_ctx.obj
    _require_token(ctx)
    if new_name is None and default_ttl is None and max_ttl is None:
        skin.error(
            "At least one of --new-name, --default-ttl, --max-ttl is required."
        )
        sys.exit(1)
    ps, es = _resolve_slugs(ctx, project_slug, env_slug)
    use_json = output_json or ctx.output_json
    try:
        client = DynamicSecretsClient(ctx.backend(), ps, es, path)
        result = client.update(name, new_name, default_ttl, max_ttl)
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return
    if use_json:
        _print_json(result)
    else:
        skin.success(f"Dynamic secret '{name}' updated.")


# --- delete ----------------------------------------------------------------


@dynamic_secrets_group.command("delete")
@click.argument("name")
@click.option("--force", is_flag=True, default=False,
              help="Force deletion (skip lease revocation checks).")
@click.option("--yes", is_flag=True, required=True,
              help="Required to confirm deletion.")
@click.option("--project-slug", "project_slug", default=None,
              envvar="INFISICAL_PROJECT_SLUG")
@click.option("--env-slug", "env_slug", default=None)
@click.option("--path", default="/", show_default=True)
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def ds_delete(
    click_ctx: click.Context,
    name: str,
    force: bool,
    yes: bool,
    project_slug: str | None,
    env_slug: str | None,
    path: str,
    output_json: bool,
) -> None:
    """Delete dynamic secret NAME."""
    ctx = click_ctx.obj
    _require_token(ctx)
    ps, es = _resolve_slugs(ctx, project_slug, env_slug)
    use_json = output_json or ctx.output_json
    try:
        client = DynamicSecretsClient(ctx.backend(), ps, es, path)
        result = client.delete(name, force=force)
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return
    if use_json:
        _print_json(result)
    else:
        skin.success(f"Dynamic secret '{name}' deleted.")


# ---------------------------------------------------------------------------
# Nested leases group
# ---------------------------------------------------------------------------


@dynamic_secrets_group.group("leases")
def leases_group() -> None:
    """Manage leases of a dynamic secret."""


@leases_group.command("list")
@click.argument("name")
@click.option("--project-slug", "project_slug", default=None,
              envvar="INFISICAL_PROJECT_SLUG")
@click.option("--env-slug", "env_slug", default=None)
@click.option("--path", default="/", show_default=True)
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def leases_list(
    click_ctx: click.Context,
    name: str,
    project_slug: str | None,
    env_slug: str | None,
    path: str,
    output_json: bool,
) -> None:
    """List leases for dynamic secret NAME."""
    ctx = click_ctx.obj
    _require_token(ctx)
    ps, es = _resolve_slugs(ctx, project_slug, env_slug)
    use_json = output_json or ctx.output_json
    try:
        client = DynamicSecretsClient(ctx.backend(), ps, es, path)
        result = client.list_leases(name)
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return
    if use_json:
        _print_json(result)
        return
    if not result:
        skin.info("No leases found.")
        return
    headers = ["ID", "STATUS", "EXPIRES_AT", "CREATED_AT"]
    rows = []
    for l in result:
        rows.append([
            str(l.get("id", l.get("_id", ""))),
            str(l.get("status", "")),
            str(l.get("expireAt", l.get("expiresAt", ""))),
            str(l.get("createdAt", "")),
        ])
    skin.table(headers, rows, max_col_width=60)


@leases_group.command("create")
@click.argument("name")
@click.option("--ttl", default=None, help="Lease TTL (e.g. 1h).")
@click.option("--project-slug", "project_slug", default=None,
              envvar="INFISICAL_PROJECT_SLUG")
@click.option("--env-slug", "env_slug", default=None)
@click.option("--path", default="/", show_default=True)
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def leases_create(
    click_ctx: click.Context,
    name: str,
    ttl: str | None,
    project_slug: str | None,
    env_slug: str | None,
    path: str,
    output_json: bool,
) -> None:
    """Create a lease for dynamic secret NAME. Prints credentials."""
    ctx = click_ctx.obj
    _require_token(ctx)
    ps, es = _resolve_slugs(ctx, project_slug, env_slug)
    use_json = output_json or ctx.output_json
    try:
        client = DynamicSecretsClient(ctx.backend(), ps, es, path)
        result = client.create_lease(name, ttl=ttl)
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return
    if use_json:
        _print_json(result)
        return

    lease = result.get("lease") if isinstance(result, dict) else None
    data = result.get("data") if isinstance(result, dict) else None
    lease_id = (lease or {}).get("id", (lease or {}).get("_id", ""))
    skin.success(f"Lease created (id: {lease_id}).")
    skin.warning("One-shot credentials — store them now, they won't be shown again:")
    click.echo(_json.dumps(data if data is not None else result, indent=2))


@leases_group.command("get")
@click.argument("lease_id")
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def leases_get(
    click_ctx: click.Context, lease_id: str, output_json: bool
) -> None:
    """Get a lease by LEASE_ID."""
    ctx = click_ctx.obj
    _require_token(ctx)
    try:
        # get_dynamic_secret_lease does not need slugs
        result = ctx.backend().get_dynamic_secret_lease(lease_id)
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return
    _print_json(result)


@leases_group.command("renew")
@click.argument("lease_id")
@click.option("--ttl", default=None, help="New TTL (e.g. 1h).")
@click.option("--project-slug", "project_slug", default=None,
              envvar="INFISICAL_PROJECT_SLUG")
@click.option("--env-slug", "env_slug", default=None)
@click.option("--path", default="/", show_default=True)
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def leases_renew(
    click_ctx: click.Context,
    lease_id: str,
    ttl: str | None,
    project_slug: str | None,
    env_slug: str | None,
    path: str,
    output_json: bool,
) -> None:
    """Renew a lease by LEASE_ID."""
    ctx = click_ctx.obj
    _require_token(ctx)
    ps, es = _resolve_slugs(ctx, project_slug, env_slug)
    use_json = output_json or ctx.output_json
    try:
        client = DynamicSecretsClient(ctx.backend(), ps, es, path)
        result = client.renew_lease(lease_id, ttl=ttl)
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return
    if use_json:
        _print_json(result)
    else:
        skin.success(f"Lease '{lease_id}' renewed.")


@leases_group.command("delete")
@click.argument("lease_id")
@click.option("--force", is_flag=True, default=False)
@click.option("--yes", is_flag=True, required=True,
              help="Required to confirm deletion.")
@click.option("--project-slug", "project_slug", default=None,
              envvar="INFISICAL_PROJECT_SLUG")
@click.option("--env-slug", "env_slug", default=None)
@click.option("--path", default="/", show_default=True)
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def leases_delete(
    click_ctx: click.Context,
    lease_id: str,
    force: bool,
    yes: bool,
    project_slug: str | None,
    env_slug: str | None,
    path: str,
    output_json: bool,
) -> None:
    """Delete lease LEASE_ID."""
    ctx = click_ctx.obj
    _require_token(ctx)
    ps, es = _resolve_slugs(ctx, project_slug, env_slug)
    use_json = output_json or ctx.output_json
    try:
        client = DynamicSecretsClient(ctx.backend(), ps, es, path)
        result = client.delete_lease(lease_id, force=force)
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return
    if use_json:
        _print_json(result)
    else:
        skin.success(f"Lease '{lease_id}' deleted.")


__all__ = ["DynamicSecretsClient", "dynamic_secrets_group"]
