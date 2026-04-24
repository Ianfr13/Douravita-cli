"""Identities and universal-auth operations for Infisical CLI."""

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


class IdentitiesClient:
    """High-level client for identities + universal-auth operations."""

    def __init__(self, backend: InfisicalBackend):
        self.backend = backend

    # ----- identities -----
    def list(
        self,
        organization_id: str,
        offset: int = 0,
        limit: int = 100,
        search: str | None = None,
    ) -> list[dict]:
        return self.backend.list_identities(
            organization_id=organization_id,
            offset=offset,
            limit=limit,
            search=search,
        )

    def get(self, identity_id: str) -> dict:
        return self.backend.get_identity(identity_id)

    def create(self, name: str, organization_id: str, role: str = "no-access") -> dict:
        return self.backend.create_identity(
            name=name, organization_id=organization_id, role=role
        )

    def update(
        self,
        identity_id: str,
        name: str | None = None,
        role: str | None = None,
    ) -> dict:
        return self.backend.update_identity(
            identity_id=identity_id, name=name, role=role
        )

    def delete(self, identity_id: str) -> dict:
        return self.backend.delete_identity(identity_id)

    # ----- universal auth -----
    def ua_login(self, client_id: str, client_secret: str) -> dict:
        return self.backend.universal_auth_login(client_id, client_secret)

    def attach_ua(
        self,
        identity_id: str,
        ttl: int | None = None,
        max_ttl: int | None = None,
        num_uses: int | None = None,
    ) -> dict:
        return self.backend.attach_universal_auth(
            identity_id=identity_id,
            access_token_ttl=ttl,
            access_token_max_ttl=max_ttl,
            access_token_num_uses_limit=num_uses,
        )

    def get_ua(self, identity_id: str) -> dict:
        return self.backend.get_universal_auth(identity_id)

    def revoke_ua(self, identity_id: str) -> dict:
        return self.backend.revoke_universal_auth(identity_id)

    def list_client_secrets(self, identity_id: str) -> list[dict]:
        return self.backend.list_client_secrets(identity_id)

    def create_client_secret(
        self,
        identity_id: str,
        description: str = "",
        ttl: int = 0,
        num_uses: int = 0,
    ) -> dict:
        return self.backend.create_client_secret(
            identity_id=identity_id,
            description=description,
            ttl=ttl,
            num_uses_limit=num_uses,
        )

    def revoke_client_secret(
        self, identity_id: str, client_secret_id: str
    ) -> dict:
        return self.backend.revoke_client_secret(
            identity_id=identity_id, client_secret_id=client_secret_id
        )


# ===========================================================================
# Group A: identities
# ===========================================================================


@click.group("identities")
def identities_group() -> None:
    """Manage Infisical identities (machine users)."""


@identities_group.command("list")
@click.option(
    "--org-id",
    "org_id",
    envvar="INFISICAL_ORG_ID",
    required=True,
    help="Organization ID (or set INFISICAL_ORG_ID).",
)
@click.option("--search", default=None, help="Search filter.")
@click.option("--limit", type=int, default=100, show_default=True)
@click.option("--offset", type=int, default=0, show_default=True)
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def identities_list(
    click_ctx: click.Context,
    org_id: str,
    search: str | None,
    limit: int,
    offset: int,
    output_json: bool,
) -> None:
    """List identities for the organization."""
    ctx = click_ctx.obj
    _require_token(ctx)
    use_json = output_json or ctx.output_json
    try:
        client = IdentitiesClient(ctx.backend())
        result = client.list(
            organization_id=org_id, offset=offset, limit=limit, search=search
        )
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return

    if use_json:
        _print_json(result)
    else:
        if not result:
            skin.info("No identities found.")
            return
        headers = ["ID", "NAME", "ROLE"]
        rows = []
        for ident in result:
            iid = ident.get("id") or ident.get("_id", "")
            name = ident.get("name", "")
            role = ident.get("role", "")
            if not role:
                roles = ident.get("customRole") or ident.get("roles") or []
                if isinstance(roles, list) and roles:
                    first = roles[0]
                    if isinstance(first, dict):
                        role = first.get("role") or first.get("slug", "")
            rows.append([str(iid), str(name), str(role)])
        skin.table(headers, rows, max_col_width=60)


@identities_group.command("get")
@click.argument("identity_id")
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def identities_get(
    click_ctx: click.Context, identity_id: str, output_json: bool
) -> None:
    """Get identity details by ID."""
    ctx = click_ctx.obj
    _require_token(ctx)
    use_json = output_json or ctx.output_json
    try:
        client = IdentitiesClient(ctx.backend())
        result = client.get(identity_id)
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return

    if use_json or not result:
        _print_json(result)
    else:
        name = result.get("name", "")
        role = result.get("role", "")
        skin.status("ID", str(result.get("id", identity_id)))
        skin.status("NAME", str(name))
        skin.status("ROLE", str(role))


@identities_group.command("create")
@click.argument("name")
@click.option(
    "--org-id",
    "org_id",
    envvar="INFISICAL_ORG_ID",
    required=True,
    help="Organization ID.",
)
@click.option(
    "--role",
    default="no-access",
    show_default=True,
    help="Role: no-access, member, admin, or a custom slug.",
)
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def identities_create(
    click_ctx: click.Context,
    name: str,
    org_id: str,
    role: str,
    output_json: bool,
) -> None:
    """Create a new identity with NAME."""
    ctx = click_ctx.obj
    _require_token(ctx)
    use_json = output_json or ctx.output_json
    try:
        client = IdentitiesClient(ctx.backend())
        result = client.create(name=name, organization_id=org_id, role=role)
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return

    if use_json:
        _print_json(result)
    else:
        iid = result.get("id") or result.get("_id", "")
        skin.success(f"Identity '{name}' created (id: {iid}).")


@identities_group.command("update")
@click.argument("identity_id")
@click.option("--name", default=None, help="New name.")
@click.option("--role", default=None, help="New role.")
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def identities_update(
    click_ctx: click.Context,
    identity_id: str,
    name: str | None,
    role: str | None,
    output_json: bool,
) -> None:
    """Update identity NAME and/or ROLE."""
    ctx = click_ctx.obj
    _require_token(ctx)
    if name is None and role is None:
        skin.error("At least one of --name or --role is required.")
        import sys
        sys.exit(1)
    use_json = output_json or ctx.output_json
    try:
        client = IdentitiesClient(ctx.backend())
        result = client.update(identity_id=identity_id, name=name, role=role)
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return

    if use_json:
        _print_json(result)
    else:
        skin.success(f"Identity '{identity_id}' updated.")


@identities_group.command("delete")
@click.argument("identity_id")
@click.option("--yes", is_flag=True, required=True, help="Confirm deletion.")
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def identities_delete(
    click_ctx: click.Context,
    identity_id: str,
    yes: bool,
    output_json: bool,
) -> None:
    """Delete an identity."""
    ctx = click_ctx.obj
    _require_token(ctx)
    use_json = output_json or ctx.output_json
    try:
        client = IdentitiesClient(ctx.backend())
        result = client.delete(identity_id)
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return

    if use_json:
        _print_json(result)
    else:
        skin.success(f"Identity '{identity_id}' deleted.")


# ===========================================================================
# Group B: auth (universal-auth + client-secrets)
# ===========================================================================


@click.group("auth")
def auth_group() -> None:
    """Universal-auth login and identity auth configuration."""


@auth_group.command("login")
@click.option("--client-id", "client_id", required=True, help="Universal-auth client ID.")
@click.option(
    "--client-secret",
    "client_secret",
    required=True,
    help="Universal-auth client secret.",
)
@click.option("--save", is_flag=True, default=False, help="Print export line for shell.")
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def auth_login(
    click_ctx: click.Context,
    client_id: str,
    client_secret: str,
    save: bool,
    output_json: bool,
) -> None:
    """Exchange client credentials for an access token."""
    ctx = click_ctx.obj
    use_json = output_json or ctx.output_json
    try:
        client = IdentitiesClient(ctx.backend())
        result = client.ua_login(client_id=client_id, client_secret=client_secret)
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return

    token = result.get("accessToken", "")
    if use_json:
        _print_json(result)
    else:
        click.echo(token)
        if save:
            click.echo(f"export INFISICAL_TOKEN={token}")


@auth_group.command("attach-ua")
@click.argument("identity_id")
@click.option("--ttl", type=int, default=None, help="Access token TTL in seconds.")
@click.option("--max-ttl", "max_ttl", type=int, default=None, help="Max TTL in seconds.")
@click.option("--num-uses", "num_uses", type=int, default=None, help="Num uses limit.")
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def auth_attach_ua(
    click_ctx: click.Context,
    identity_id: str,
    ttl: int | None,
    max_ttl: int | None,
    num_uses: int | None,
    output_json: bool,
) -> None:
    """Attach universal-auth to an identity."""
    ctx = click_ctx.obj
    _require_token(ctx)
    use_json = output_json or ctx.output_json
    try:
        client = IdentitiesClient(ctx.backend())
        result = client.attach_ua(
            identity_id=identity_id, ttl=ttl, max_ttl=max_ttl, num_uses=num_uses
        )
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return

    if use_json:
        _print_json(result)
    else:
        skin.success(f"Universal-auth attached to identity '{identity_id}'.")


@auth_group.command("get-ua")
@click.argument("identity_id")
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def auth_get_ua(
    click_ctx: click.Context, identity_id: str, output_json: bool
) -> None:
    """Get universal-auth config for an identity."""
    ctx = click_ctx.obj
    _require_token(ctx)
    try:
        client = IdentitiesClient(ctx.backend())
        result = client.get_ua(identity_id)
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return

    _print_json(result)


@auth_group.command("revoke-ua")
@click.argument("identity_id")
@click.option("--yes", is_flag=True, required=True, help="Confirm revocation.")
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def auth_revoke_ua(
    click_ctx: click.Context,
    identity_id: str,
    yes: bool,
    output_json: bool,
) -> None:
    """Revoke universal-auth from an identity."""
    ctx = click_ctx.obj
    _require_token(ctx)
    use_json = output_json or ctx.output_json
    try:
        client = IdentitiesClient(ctx.backend())
        result = client.revoke_ua(identity_id)
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return

    if use_json:
        _print_json(result)
    else:
        skin.success(f"Universal-auth revoked from identity '{identity_id}'.")


# ----- nested client-secrets subgroup -----


@auth_group.group("client-secrets")
def auth_client_secrets() -> None:
    """Manage universal-auth client secrets for an identity."""


@auth_client_secrets.command("list")
@click.argument("identity_id")
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def cs_list(
    click_ctx: click.Context, identity_id: str, output_json: bool
) -> None:
    """List client secrets for an identity."""
    ctx = click_ctx.obj
    _require_token(ctx)
    use_json = output_json or ctx.output_json
    try:
        client = IdentitiesClient(ctx.backend())
        result = client.list_client_secrets(identity_id)
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return

    if use_json:
        _print_json(result)
    else:
        if not result:
            skin.info("No client secrets found.")
            return
        headers = ["ID", "DESCRIPTION", "IS_REVOKED", "CREATED_AT"]
        rows = []
        for cs in result:
            cid = cs.get("id") or cs.get("_id", "")
            desc = cs.get("description", "")
            revoked = cs.get("isClientSecretRevoked", cs.get("isRevoked", False))
            created = cs.get("createdAt", "")
            rows.append([str(cid), str(desc), str(revoked), str(created)])
        skin.table(headers, rows, max_col_width=60)


@auth_client_secrets.command("create")
@click.argument("identity_id")
@click.option("--description", default="", help="Optional description.")
@click.option("--ttl", type=int, default=0, show_default=True, help="TTL in seconds (0 = no expiry).")
@click.option(
    "--num-uses",
    "num_uses",
    type=int,
    default=0,
    show_default=True,
    help="Max uses (0 = unlimited).",
)
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def cs_create(
    click_ctx: click.Context,
    identity_id: str,
    description: str,
    ttl: int,
    num_uses: int,
    output_json: bool,
) -> None:
    """Create a new client secret for an identity."""
    ctx = click_ctx.obj
    _require_token(ctx)
    use_json = output_json or ctx.output_json
    try:
        client = IdentitiesClient(ctx.backend())
        result = client.create_client_secret(
            identity_id=identity_id,
            description=description,
            ttl=ttl,
            num_uses=num_uses,
        )
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return

    if use_json:
        _print_json(result)
    else:
        secret = result.get("clientSecret", "")
        skin.warning("This secret will not be shown again. Save it now.")
        click.echo(secret)


@auth_client_secrets.command("revoke")
@click.argument("identity_id")
@click.argument("client_secret_id")
@click.option("--yes", is_flag=True, required=True, help="Confirm revocation.")
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def cs_revoke(
    click_ctx: click.Context,
    identity_id: str,
    client_secret_id: str,
    yes: bool,
    output_json: bool,
) -> None:
    """Revoke a client secret."""
    ctx = click_ctx.obj
    _require_token(ctx)
    use_json = output_json or ctx.output_json
    try:
        client = IdentitiesClient(ctx.backend())
        result = client.revoke_client_secret(
            identity_id=identity_id, client_secret_id=client_secret_id
        )
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return

    if use_json:
        _print_json(result)
    else:
        skin.success(f"Client secret '{client_secret_id}' revoked.")


__all__ = ["IdentitiesClient", "identities_group", "auth_group"]
