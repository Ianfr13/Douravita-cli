#!/usr/bin/env python3
"""Google Tag Manager CLI — Agent-native CLI for GTM API v2.

Provides full access to GTM accounts, containers, workspaces, tags,
triggers, variables, folders, environments, versions, and permissions
via the GTM API v2.

Usage:
    # One-shot commands
    cli-anything-google-tag-manager account list
    cli-anything-google-tag-manager --account-id 12345 container list
    cli-anything-google-tag-manager --json tag list

    # Interactive REPL
    cli-anything-google-tag-manager
"""

import sys
import os
import json
import click
from typing import Optional

from cli_anything.google_tag_manager.core.session import Session
from cli_anything.google_tag_manager.core import accounts as acct_mod
from cli_anything.google_tag_manager.core import containers as cont_mod
from cli_anything.google_tag_manager.core import workspaces as ws_mod
from cli_anything.google_tag_manager.core import tags as tags_mod
from cli_anything.google_tag_manager.core import triggers as trig_mod
from cli_anything.google_tag_manager.core import variables as var_mod
from cli_anything.google_tag_manager.core import folders as folder_mod
from cli_anything.google_tag_manager.core import environments as env_mod
from cli_anything.google_tag_manager.core import versions as ver_mod
from cli_anything.google_tag_manager.core import permissions as perm_mod
from cli_anything.google_tag_manager.utils import gtm_backend as backend
from cli_anything.google_tag_manager.utils.repl_skin import ReplSkin

# ── Global state ─────────────────────────────────────────────────────

_session: Optional[Session] = None
_json_output: bool = False
_service = None  # cached GTM API service

# ── Helpers ───────────────────────────────────────────────────────────


def get_session() -> Session:
    global _session
    if _session is None:
        _session = Session()
    return _session


def get_service(credentials: str = None):
    """Get (or create) the GTM API service, respecting session credentials."""
    global _service
    if _service is None:
        sess = get_session()
        creds_file = credentials or sess.credentials_file
        _service = backend.get_gtm_service(credentials_file=creds_file)
    return _service


def reset_service():
    """Reset cached service (e.g., after auth change)."""
    global _service
    _service = None


def output(data, message: str = ""):
    """Output result — JSON mode or human-readable."""
    if _json_output:
        click.echo(json.dumps(data, indent=2, default=str))
    else:
        if message:
            click.echo(message)
        if isinstance(data, dict):
            _print_dict(data)
        elif isinstance(data, list):
            _print_list(data)
        elif data is not None:
            click.echo(str(data))


def _print_dict(d: dict, indent: int = 0):
    prefix = "  " * indent
    for k, v in d.items():
        if isinstance(v, dict):
            click.echo(f"{prefix}{k}:")
            _print_dict(v, indent + 1)
        elif isinstance(v, list):
            click.echo(f"{prefix}{k}:")
            _print_list(v, indent + 1)
        else:
            click.echo(f"{prefix}{k}: {v}")


def _print_list(items: list, indent: int = 0):
    prefix = "  " * indent
    for i, item in enumerate(items):
        if isinstance(item, dict):
            click.echo(f"{prefix}[{i}]")
            _print_dict(item, indent + 1)
        else:
            click.echo(f"{prefix}- {item}")


def handle_error(e: Exception, exit_on_error: bool = True):
    """Handle an exception with consistent formatting."""
    msg = str(e)
    if _json_output:
        click.echo(json.dumps({"error": msg, "type": type(e).__name__}))
    else:
        click.echo(f"Error: {msg}", err=True)
    if exit_on_error:
        sys.exit(1)


def _resolve_ids(ctx_obj, account_id=None, container_id=None, workspace_id=None):
    """Resolve IDs from args, context object, or session (in that priority order)."""
    sess = get_session()
    aid = account_id or (ctx_obj or {}).get("account_id") or sess.account_id
    cid = container_id or (ctx_obj or {}).get("container_id") or sess.container_id
    wid = workspace_id or (ctx_obj or {}).get("workspace_id") or sess.workspace_id
    return aid, cid, wid


# ── Root CLI ──────────────────────────────────────────────────────────

@click.group(invoke_without_command=True, context_settings={"help_option_names": ["-h", "--help"]})
@click.option("--account-id", envvar="GTM_ACCOUNT_ID", default=None,
              help="GTM Account ID (or set GTM_ACCOUNT_ID env).")
@click.option("--container-id", envvar="GTM_CONTAINER_ID", default=None,
              help="GTM Container ID (or set GTM_CONTAINER_ID env).")
@click.option("--workspace-id", envvar="GTM_WORKSPACE_ID", default=None,
              help="GTM Workspace ID (or set GTM_WORKSPACE_ID env).")
@click.option("--credentials", default=None,
              help="Path to Google credentials JSON file.")
@click.option("--json", "use_json", is_flag=True, default=False,
              help="Output JSON instead of human-readable tables.")
@click.pass_context
def cli(ctx, account_id, container_id, workspace_id, credentials, use_json):
    """Google Tag Manager CLI — Manage GTM via the API v2.

    Provides full access to accounts, containers, workspaces, tags,
    triggers, variables, folders, environments, versions, and permissions.

    Set context via global options or environment variables:

    \b
      GTM_ACCOUNT_ID     — default account ID
      GTM_CONTAINER_ID   — default container ID
      GTM_WORKSPACE_ID   — default workspace ID
      GOOGLE_APPLICATION_CREDENTIALS — path to service account JSON
    """
    global _json_output

    _json_output = use_json
    ctx.ensure_object(dict)
    ctx.obj["account_id"] = account_id
    ctx.obj["container_id"] = container_id
    ctx.obj["workspace_id"] = workspace_id
    ctx.obj["credentials"] = credentials

    # Store IDs in session if provided
    sess = get_session()
    if account_id:
        sess.account_id = account_id
        sess.save()
    if container_id:
        sess.container_id = container_id
        sess.save()
    if workspace_id:
        sess.workspace_id = workspace_id
        sess.save()
    if credentials:
        sess.credentials_file = credentials
        sess.save()
        reset_service()

    if ctx.invoked_subcommand is None:
        ctx.invoke(repl)


# ── REPL ──────────────────────────────────────────────────────────────

@cli.command()
@click.pass_context
def repl(ctx):
    """Enter the interactive REPL mode."""
    skin = ReplSkin("google_tag_manager", version="1.0.0")
    skin.print_banner()

    pt_session = skin.create_prompt_session()

    commands_help = {
        "account list/get/update": "Manage GTM accounts",
        "container list/get/create/update/delete/snippet": "Manage containers",
        "workspace list/get/create/update/delete/status/sync/preview/publish": "Manage workspaces",
        "tag list/get/create/update/delete/revert": "Manage tags",
        "trigger list/get/create/update/delete/revert": "Manage triggers",
        "variable list/get/create/update/delete/revert": "Manage variables",
        "folder list/get/create/update/delete/entities/move": "Manage folders",
        "env list/get/create/update/delete/reauth": "Manage environments",
        "version list/latest": "Browse version history",
        "permission list/get/grant/update/revoke": "Manage user permissions",
        "auth init/test/info": "Manage authentication",
        "help": "Show this help",
        "quit / exit": "Exit the REPL",
    }

    sess = get_session()

    while True:
        try:
            context_str = ""
            if sess.account_id:
                context_str = f"acct:{sess.account_id}"
            if sess.container_id:
                context_str += f" c:{sess.container_id}"
            if sess.workspace_id:
                context_str += f" ws:{sess.workspace_id}"

            line = skin.get_input(pt_session, context=context_str.strip())
        except (EOFError, KeyboardInterrupt):
            skin.print_goodbye()
            break

        if not line:
            continue

        parts = line.split()
        cmd = parts[0].lower()

        if cmd in ("quit", "exit", "q"):
            skin.print_goodbye()
            break
        elif cmd == "help":
            skin.help(commands_help)
        else:
            # Parse and dispatch to Click subcommands
            try:
                args = parts
                # Inject --json if global flag is set
                if _json_output and "--json" not in args:
                    args = ["--json"] + args
                cli.main(args=args, standalone_mode=False,
                         obj=ctx.obj or {})
            except SystemExit:
                pass
            except Exception as e:
                skin.error(str(e))


# ── Auth commands ─────────────────────────────────────────────────────

@cli.group()
def auth():
    """Authentication management."""
    pass


@auth.command("init")
@click.option("--service-account", "-s", default=None,
              help="Path to a service account JSON key file.")
@click.option("--oauth-secrets", "-o", default=None,
              help="Path to an OAuth2 client secrets JSON file (triggers browser flow).")
@click.option("--readonly", is_flag=True, default=False,
              help="Request read-only access scopes.")
@click.pass_context
def auth_init(ctx, service_account, oauth_secrets, readonly):
    """Set up GTM authentication (service account or OAuth2 browser flow)."""
    try:
        if service_account:
            dest = backend.install_service_account(service_account)
            reset_service()
            msg = f"Service account credentials installed to: {dest}"
            output({"status": "ok", "credentials_file": dest}, message=msg)
        elif oauth_secrets:
            token_path = backend.run_oauth_flow(oauth_secrets, readonly=readonly)
            reset_service()
            msg = f"OAuth2 token saved to: {token_path}"
            output({"status": "ok", "token_file": token_path}, message=msg)
        else:
            click.echo(
                "Provide --service-account or --oauth-secrets.\n\n"
                "  Service account (recommended for agents):\n"
                "    cli-anything-google-tag-manager auth init --service-account sa.json\n\n"
                "  OAuth2 browser flow:\n"
                "    cli-anything-google-tag-manager auth init --oauth-secrets client_secrets.json\n\n"
                "Get credentials at: https://console.cloud.google.com/iam-admin/serviceaccounts"
            )
    except Exception as e:
        handle_error(e)


@auth.command("test")
@click.option("--json", "use_json", is_flag=True, default=False)
@click.pass_context
def auth_test(ctx, use_json):
    """Test authentication by listing GTM accounts."""
    global _json_output
    if use_json:
        _json_output = True
    try:
        svc = get_service()
        accounts = backend.list_accounts(svc)
        count = len(accounts)
        msg = f"Authentication OK. Found {count} GTM account(s)."
        output({"status": "ok", "accounts_found": count}, message=msg)
    except Exception as e:
        handle_error(e)


@auth.command("info")
@click.option("--json", "use_json", is_flag=True, default=False)
@click.pass_context
def auth_info(ctx, use_json):
    """Show current authentication and context information."""
    global _json_output
    if use_json:
        _json_output = True
    sess = get_session()
    creds_file = backend.find_credentials()
    info = {
        "credentials_file": creds_file or "not found",
        "account_id": sess.account_id or "(not set)",
        "container_id": sess.container_id or "(not set)",
        "workspace_id": sess.workspace_id or "(not set)",
        "session_file": sess.session_file,
    }
    output(info, message="Current GTM CLI configuration:")


# ── Account commands ──────────────────────────────────────────────────

@cli.group()
def account():
    """Account operations."""
    pass


@account.command("list")
@click.option("--json", "use_json", is_flag=True, default=False)
@click.pass_context
def account_list(ctx, use_json):
    """List all accessible GTM accounts."""
    global _json_output
    if use_json:
        _json_output = True
    try:
        svc = get_service(ctx.obj.get("credentials") if ctx.obj else None)
        accounts = acct_mod.list_accounts(svc)
        if _json_output:
            output(accounts)
        else:
            skin = ReplSkin("google_tag_manager")
            skin.table(
                acct_mod.ACCOUNT_TABLE_HEADERS,
                [acct_mod.format_account_row(a) for a in accounts]
            )
            click.echo(f"\n  {len(accounts)} account(s) found.")
    except Exception as e:
        handle_error(e)


@account.command("get")
@click.argument("account_id", required=False)
@click.option("--json", "use_json", is_flag=True, default=False)
@click.pass_context
def account_get(ctx, account_id, use_json):
    """Get details for a specific GTM account."""
    global _json_output
    if use_json:
        _json_output = True
    aid, _, _ = _resolve_ids(ctx.obj, account_id=account_id)
    if not aid:
        handle_error(ValueError("account_id is required. Use --account-id or GTM_ACCOUNT_ID."))
        return
    try:
        svc = get_service(ctx.obj.get("credentials") if ctx.obj else None)
        result = acct_mod.get_account(svc, aid)
        output(result)
    except Exception as e:
        handle_error(e)


@account.command("update")
@click.argument("account_id", required=False)
@click.option("--name", "-n", default=None, help="New account display name.")
@click.option("--share-data/--no-share-data", default=None,
              help="Share anonymized data with Google.")
@click.option("--json", "use_json", is_flag=True, default=False)
@click.pass_context
def account_update(ctx, account_id, name, share_data, use_json):
    """Update a GTM account."""
    global _json_output
    if use_json:
        _json_output = True
    aid, _, _ = _resolve_ids(ctx.obj, account_id=account_id)
    if not aid:
        handle_error(ValueError("account_id is required."))
        return
    try:
        svc = get_service(ctx.obj.get("credentials") if ctx.obj else None)
        result = acct_mod.update_account(svc, aid, name=name, share_data=share_data)
        output(result, message="Account updated.")
    except Exception as e:
        handle_error(e)


# ── Container commands ────────────────────────────────────────────────

@cli.group()
def container():
    """Container management."""
    pass


@container.command("list")
@click.argument("account_id", required=False)
@click.option("--json", "use_json", is_flag=True, default=False)
@click.pass_context
def container_list(ctx, account_id, use_json):
    """List all containers in a GTM account."""
    global _json_output
    if use_json:
        _json_output = True
    aid, _, _ = _resolve_ids(ctx.obj, account_id=account_id)
    if not aid:
        handle_error(ValueError("account_id is required."))
        return
    try:
        svc = get_service(ctx.obj.get("credentials") if ctx.obj else None)
        containers = cont_mod.list_containers(svc, aid)
        if _json_output:
            output(containers)
        else:
            skin = ReplSkin("google_tag_manager")
            skin.table(
                cont_mod.CONTAINER_TABLE_HEADERS,
                [cont_mod.format_container_row(c) for c in containers]
            )
            click.echo(f"\n  {len(containers)} container(s) found.")
    except Exception as e:
        handle_error(e)


@container.command("get")
@click.argument("container_id", required=False)
@click.option("--account-id", default=None)
@click.option("--json", "use_json", is_flag=True, default=False)
@click.pass_context
def container_get(ctx, container_id, account_id, use_json):
    """Get a container's details."""
    global _json_output
    if use_json:
        _json_output = True
    aid, cid, _ = _resolve_ids(ctx.obj, account_id=account_id, container_id=container_id)
    if not aid or not cid:
        handle_error(ValueError("account_id and container_id are required."))
        return
    try:
        svc = get_service(ctx.obj.get("credentials") if ctx.obj else None)
        result = cont_mod.get_container(svc, aid, cid)
        output(result)
    except Exception as e:
        handle_error(e)


@container.command("create")
@click.argument("name")
@click.option("--account-id", default=None)
@click.option("--usage-context", "-u", multiple=True, default=["web"],
              help="Usage contexts: web, androidSdk5, iosSdk5, amp, server. Repeatable.")
@click.option("--domain", "-d", multiple=True, help="Domain names. Repeatable.")
@click.option("--notes", default="", help="Container notes.")
@click.option("--json", "use_json", is_flag=True, default=False)
@click.pass_context
def container_create(ctx, name, account_id, usage_context, domain, notes, use_json):
    """Create a new container."""
    global _json_output
    if use_json:
        _json_output = True
    aid, _, _ = _resolve_ids(ctx.obj, account_id=account_id)
    if not aid:
        handle_error(ValueError("account_id is required."))
        return
    try:
        svc = get_service(ctx.obj.get("credentials") if ctx.obj else None)
        result = cont_mod.create_container(
            svc, aid, name, list(usage_context),
            domain_name=list(domain) if domain else None,
            notes=notes,
        )
        output(result, message=f"Container '{name}' created.")
    except Exception as e:
        handle_error(e)


@container.command("update")
@click.argument("container_id", required=False)
@click.option("--account-id", default=None)
@click.option("--name", "-n", default=None, help="New container name.")
@click.option("--domain", "-d", multiple=True)
@click.option("--notes", default=None)
@click.option("--json", "use_json", is_flag=True, default=False)
@click.pass_context
def container_update(ctx, container_id, account_id, name, domain, notes, use_json):
    """Update a container."""
    global _json_output
    if use_json:
        _json_output = True
    aid, cid, _ = _resolve_ids(ctx.obj, account_id=account_id, container_id=container_id)
    if not aid or not cid:
        handle_error(ValueError("account_id and container_id are required."))
        return
    try:
        svc = get_service(ctx.obj.get("credentials") if ctx.obj else None)
        result = cont_mod.update_container(
            svc, aid, cid, name=name,
            domain_name=list(domain) if domain else None,
            notes=notes,
        )
        output(result, message="Container updated.")
    except Exception as e:
        handle_error(e)


@container.command("delete")
@click.argument("container_id", required=False)
@click.option("--account-id", default=None)
@click.option("--force", is_flag=True, default=False, help="Skip confirmation.")
@click.option("--json", "use_json", is_flag=True, default=False)
@click.pass_context
def container_delete(ctx, container_id, account_id, force, use_json):
    """Delete a container."""
    global _json_output
    if use_json:
        _json_output = True
    aid, cid, _ = _resolve_ids(ctx.obj, account_id=account_id, container_id=container_id)
    if not aid or not cid:
        handle_error(ValueError("account_id and container_id are required."))
        return
    if not force and not _json_output:
        click.confirm(f"Delete container {cid}? This cannot be undone.", abort=True)
    try:
        svc = get_service(ctx.obj.get("credentials") if ctx.obj else None)
        result = cont_mod.delete_container(svc, aid, cid)
        output(result, message=f"Container {cid} deleted.")
    except Exception as e:
        handle_error(e)


@container.command("snippet")
@click.argument("container_id", required=False)
@click.option("--account-id", default=None)
@click.option("--json", "use_json", is_flag=True, default=False)
@click.pass_context
def container_snippet(ctx, container_id, account_id, use_json):
    """Get the tagging snippet for a container."""
    global _json_output
    if use_json:
        _json_output = True
    aid, cid, _ = _resolve_ids(ctx.obj, account_id=account_id, container_id=container_id)
    if not aid or not cid:
        handle_error(ValueError("account_id and container_id are required."))
        return
    try:
        svc = get_service(ctx.obj.get("credentials") if ctx.obj else None)
        result = cont_mod.get_snippet(svc, aid, cid)
        output(result)
    except Exception as e:
        handle_error(e)


# ── Workspace commands ────────────────────────────────────────────────

@cli.group()
def workspace():
    """Workspace operations."""
    pass


@workspace.command("list")
@click.option("--account-id", default=None)
@click.option("--container-id", default=None)
@click.option("--json", "use_json", is_flag=True, default=False)
@click.pass_context
def workspace_list(ctx, account_id, container_id, use_json):
    """List all workspaces in a container."""
    global _json_output
    if use_json:
        _json_output = True
    aid, cid, _ = _resolve_ids(ctx.obj, account_id=account_id, container_id=container_id)
    if not aid or not cid:
        handle_error(ValueError("account_id and container_id are required."))
        return
    try:
        svc = get_service(ctx.obj.get("credentials") if ctx.obj else None)
        workspaces = ws_mod.list_workspaces(svc, aid, cid)
        if _json_output:
            output(workspaces)
        else:
            skin = ReplSkin("google_tag_manager")
            skin.table(
                ws_mod.WORKSPACE_TABLE_HEADERS,
                [ws_mod.format_workspace_row(w) for w in workspaces]
            )
            click.echo(f"\n  {len(workspaces)} workspace(s) found.")
    except Exception as e:
        handle_error(e)


@workspace.command("get")
@click.argument("workspace_id", required=False)
@click.option("--account-id", default=None)
@click.option("--container-id", default=None)
@click.option("--json", "use_json", is_flag=True, default=False)
@click.pass_context
def workspace_get(ctx, workspace_id, account_id, container_id, use_json):
    """Get workspace details."""
    global _json_output
    if use_json:
        _json_output = True
    aid, cid, wid = _resolve_ids(ctx.obj, account_id=account_id,
                                  container_id=container_id, workspace_id=workspace_id)
    if not all([aid, cid, wid]):
        handle_error(ValueError("account_id, container_id, and workspace_id are required."))
        return
    try:
        svc = get_service(ctx.obj.get("credentials") if ctx.obj else None)
        result = ws_mod.get_workspace(svc, aid, cid, wid)
        output(result)
    except Exception as e:
        handle_error(e)


@workspace.command("create")
@click.argument("name")
@click.option("--account-id", default=None)
@click.option("--container-id", default=None)
@click.option("--description", "-d", default="")
@click.option("--json", "use_json", is_flag=True, default=False)
@click.pass_context
def workspace_create(ctx, name, account_id, container_id, description, use_json):
    """Create a new workspace."""
    global _json_output
    if use_json:
        _json_output = True
    aid, cid, _ = _resolve_ids(ctx.obj, account_id=account_id, container_id=container_id)
    if not aid or not cid:
        handle_error(ValueError("account_id and container_id are required."))
        return
    try:
        svc = get_service(ctx.obj.get("credentials") if ctx.obj else None)
        result = ws_mod.create_workspace(svc, aid, cid, name, description)
        output(result, message=f"Workspace '{name}' created.")
    except Exception as e:
        handle_error(e)


@workspace.command("update")
@click.argument("workspace_id", required=False)
@click.option("--account-id", default=None)
@click.option("--container-id", default=None)
@click.option("--name", "-n", default=None)
@click.option("--description", "-d", default=None)
@click.option("--json", "use_json", is_flag=True, default=False)
@click.pass_context
def workspace_update(ctx, workspace_id, account_id, container_id, name, description, use_json):
    """Update a workspace."""
    global _json_output
    if use_json:
        _json_output = True
    aid, cid, wid = _resolve_ids(ctx.obj, account_id=account_id,
                                  container_id=container_id, workspace_id=workspace_id)
    if not all([aid, cid, wid]):
        handle_error(ValueError("account_id, container_id, and workspace_id are required."))
        return
    try:
        svc = get_service(ctx.obj.get("credentials") if ctx.obj else None)
        result = ws_mod.update_workspace(svc, aid, cid, wid, name=name, description=description)
        output(result, message="Workspace updated.")
    except Exception as e:
        handle_error(e)


@workspace.command("delete")
@click.argument("workspace_id", required=False)
@click.option("--account-id", default=None)
@click.option("--container-id", default=None)
@click.option("--force", is_flag=True, default=False)
@click.option("--json", "use_json", is_flag=True, default=False)
@click.pass_context
def workspace_delete(ctx, workspace_id, account_id, container_id, force, use_json):
    """Delete a workspace."""
    global _json_output
    if use_json:
        _json_output = True
    aid, cid, wid = _resolve_ids(ctx.obj, account_id=account_id,
                                  container_id=container_id, workspace_id=workspace_id)
    if not all([aid, cid, wid]):
        handle_error(ValueError("account_id, container_id, and workspace_id are required."))
        return
    if not force and not _json_output:
        click.confirm(f"Delete workspace {wid}?", abort=True)
    try:
        svc = get_service(ctx.obj.get("credentials") if ctx.obj else None)
        result = ws_mod.delete_workspace(svc, aid, cid, wid)
        output(result, message=f"Workspace {wid} deleted.")
    except Exception as e:
        handle_error(e)


@workspace.command("status")
@click.argument("workspace_id", required=False)
@click.option("--account-id", default=None)
@click.option("--container-id", default=None)
@click.option("--json", "use_json", is_flag=True, default=False)
@click.pass_context
def workspace_status_cmd(ctx, workspace_id, account_id, container_id, use_json):
    """Show changes and conflicts in a workspace."""
    global _json_output
    if use_json:
        _json_output = True
    aid, cid, wid = _resolve_ids(ctx.obj, account_id=account_id,
                                  container_id=container_id, workspace_id=workspace_id)
    if not all([aid, cid, wid]):
        handle_error(ValueError("account_id, container_id, and workspace_id are required."))
        return
    try:
        svc = get_service(ctx.obj.get("credentials") if ctx.obj else None)
        result = ws_mod.workspace_status(svc, aid, cid, wid)
        output(result)
    except Exception as e:
        handle_error(e)


@workspace.command("sync")
@click.argument("workspace_id", required=False)
@click.option("--account-id", default=None)
@click.option("--container-id", default=None)
@click.option("--json", "use_json", is_flag=True, default=False)
@click.pass_context
def workspace_sync(ctx, workspace_id, account_id, container_id, use_json):
    """Sync workspace with the latest container version."""
    global _json_output
    if use_json:
        _json_output = True
    aid, cid, wid = _resolve_ids(ctx.obj, account_id=account_id,
                                  container_id=container_id, workspace_id=workspace_id)
    if not all([aid, cid, wid]):
        handle_error(ValueError("account_id, container_id, and workspace_id are required."))
        return
    try:
        svc = get_service(ctx.obj.get("credentials") if ctx.obj else None)
        result = ws_mod.sync_workspace(svc, aid, cid, wid)
        output(result, message="Workspace synced.")
    except Exception as e:
        handle_error(e)


@workspace.command("preview")
@click.argument("workspace_id", required=False)
@click.option("--account-id", default=None)
@click.option("--container-id", default=None)
@click.option("--json", "use_json", is_flag=True, default=False)
@click.pass_context
def workspace_preview(ctx, workspace_id, account_id, container_id, use_json):
    """Create a quick preview of a workspace."""
    global _json_output
    if use_json:
        _json_output = True
    aid, cid, wid = _resolve_ids(ctx.obj, account_id=account_id,
                                  container_id=container_id, workspace_id=workspace_id)
    if not all([aid, cid, wid]):
        handle_error(ValueError("account_id, container_id, and workspace_id are required."))
        return
    try:
        svc = get_service(ctx.obj.get("credentials") if ctx.obj else None)
        result = ws_mod.quick_preview(svc, aid, cid, wid)
        output(result, message="Quick preview created.")
    except Exception as e:
        handle_error(e)


@workspace.command("publish")
@click.argument("workspace_id", required=False)
@click.option("--account-id", default=None)
@click.option("--container-id", default=None)
@click.option("--name", "-n", default="", help="Version name.")
@click.option("--notes", default="", help="Version notes.")
@click.option("--json", "use_json", is_flag=True, default=False)
@click.pass_context
def workspace_publish(ctx, workspace_id, account_id, container_id, name, notes, use_json):
    """Create a new container version from the workspace."""
    global _json_output
    if use_json:
        _json_output = True
    aid, cid, wid = _resolve_ids(ctx.obj, account_id=account_id,
                                  container_id=container_id, workspace_id=workspace_id)
    if not all([aid, cid, wid]):
        handle_error(ValueError("account_id, container_id, and workspace_id are required."))
        return
    try:
        svc = get_service(ctx.obj.get("credentials") if ctx.obj else None)
        result = ws_mod.create_version(svc, aid, cid, wid, name=name, notes=notes)
        output(result, message="Version created from workspace.")
    except Exception as e:
        handle_error(e)


# ── Tag commands ──────────────────────────────────────────────────────

@cli.group()
def tag():
    """Tag management."""
    pass


@tag.command("list")
@click.option("--account-id", default=None)
@click.option("--container-id", default=None)
@click.option("--workspace-id", default=None)
@click.option("--json", "use_json", is_flag=True, default=False)
@click.pass_context
def tag_list(ctx, account_id, container_id, workspace_id, use_json):
    """List all tags in a workspace."""
    global _json_output
    if use_json:
        _json_output = True
    aid, cid, wid = _resolve_ids(ctx.obj, account_id=account_id,
                                  container_id=container_id, workspace_id=workspace_id)
    if not all([aid, cid, wid]):
        handle_error(ValueError("account_id, container_id, and workspace_id are required."))
        return
    try:
        svc = get_service(ctx.obj.get("credentials") if ctx.obj else None)
        tags = tags_mod.list_tags(svc, aid, cid, wid)
        if _json_output:
            output(tags)
        else:
            skin = ReplSkin("google_tag_manager")
            skin.table(
                tags_mod.TAG_TABLE_HEADERS,
                [tags_mod.format_tag_row(t) for t in tags]
            )
            click.echo(f"\n  {len(tags)} tag(s) found.")
    except Exception as e:
        handle_error(e)


@tag.command("get")
@click.argument("tag_id")
@click.option("--account-id", default=None)
@click.option("--container-id", default=None)
@click.option("--workspace-id", default=None)
@click.option("--json", "use_json", is_flag=True, default=False)
@click.pass_context
def tag_get(ctx, tag_id, account_id, container_id, workspace_id, use_json):
    """Get a specific tag by ID."""
    global _json_output
    if use_json:
        _json_output = True
    aid, cid, wid = _resolve_ids(ctx.obj, account_id=account_id,
                                  container_id=container_id, workspace_id=workspace_id)
    if not all([aid, cid, wid]):
        handle_error(ValueError("account_id, container_id, and workspace_id are required."))
        return
    try:
        svc = get_service(ctx.obj.get("credentials") if ctx.obj else None)
        result = tags_mod.get_tag(svc, aid, cid, wid, tag_id)
        output(result)
    except Exception as e:
        handle_error(e)


@tag.command("create")
@click.argument("name")
@click.option("--type", "-t", "tag_type", required=True, help="Tag type (e.g., ua, html, googtag).")
@click.option("--account-id", default=None)
@click.option("--container-id", default=None)
@click.option("--workspace-id", default=None)
@click.option("--trigger", "-T", "trigger_ids", multiple=True, help="Firing trigger ID(s).")
@click.option("--block", "-B", "block_ids", multiple=True, help="Blocking trigger ID(s).")
@click.option("--param", "-p", "params", multiple=True,
              help='Parameter as JSON, e.g. \'{"type":"template","key":"trackingId","value":"UA-123"}\'')
@click.option("--firing-option", default="oncePerEvent",
              type=click.Choice(["oncePerEvent", "oncePerLoad", "unlimited"]))
@click.option("--json", "use_json", is_flag=True, default=False)
@click.pass_context
def tag_create(ctx, name, tag_type, account_id, container_id, workspace_id,
               trigger_ids, block_ids, params, firing_option, use_json):
    """Create a new tag."""
    global _json_output
    if use_json:
        _json_output = True
    aid, cid, wid = _resolve_ids(ctx.obj, account_id=account_id,
                                  container_id=container_id, workspace_id=workspace_id)
    if not all([aid, cid, wid]):
        handle_error(ValueError("account_id, container_id, and workspace_id are required."))
        return
    try:
        parameters = [json.loads(p) for p in params] if params else None
        svc = get_service(ctx.obj.get("credentials") if ctx.obj else None)
        result = tags_mod.create_tag(
            svc, aid, cid, wid, name, tag_type,
            parameters=parameters,
            firing_trigger_ids=list(trigger_ids) if trigger_ids else None,
            blocking_trigger_ids=list(block_ids) if block_ids else None,
            tag_firing_option=firing_option,
        )
        output(result, message=f"Tag '{name}' created.")
    except Exception as e:
        handle_error(e)


@tag.command("update")
@click.argument("tag_id")
@click.option("--account-id", default=None)
@click.option("--container-id", default=None)
@click.option("--workspace-id", default=None)
@click.option("--name", "-n", default=None)
@click.option("--trigger", "-T", "trigger_ids", multiple=True)
@click.option("--param", "-p", "params", multiple=True)
@click.option("--json", "use_json", is_flag=True, default=False)
@click.pass_context
def tag_update(ctx, tag_id, account_id, container_id, workspace_id,
               name, trigger_ids, params, use_json):
    """Update a tag."""
    global _json_output
    if use_json:
        _json_output = True
    aid, cid, wid = _resolve_ids(ctx.obj, account_id=account_id,
                                  container_id=container_id, workspace_id=workspace_id)
    if not all([aid, cid, wid]):
        handle_error(ValueError("account_id, container_id, and workspace_id are required."))
        return
    try:
        parameters = [json.loads(p) for p in params] if params else None
        svc = get_service(ctx.obj.get("credentials") if ctx.obj else None)
        result = tags_mod.update_tag(
            svc, aid, cid, wid, tag_id,
            name=name,
            parameters=parameters,
            firing_trigger_ids=list(trigger_ids) if trigger_ids else None,
        )
        output(result, message="Tag updated.")
    except Exception as e:
        handle_error(e)


@tag.command("delete")
@click.argument("tag_id")
@click.option("--account-id", default=None)
@click.option("--container-id", default=None)
@click.option("--workspace-id", default=None)
@click.option("--force", is_flag=True, default=False)
@click.option("--json", "use_json", is_flag=True, default=False)
@click.pass_context
def tag_delete(ctx, tag_id, account_id, container_id, workspace_id, force, use_json):
    """Delete a tag."""
    global _json_output
    if use_json:
        _json_output = True
    aid, cid, wid = _resolve_ids(ctx.obj, account_id=account_id,
                                  container_id=container_id, workspace_id=workspace_id)
    if not all([aid, cid, wid]):
        handle_error(ValueError("account_id, container_id, and workspace_id are required."))
        return
    if not force and not _json_output:
        click.confirm(f"Delete tag {tag_id}?", abort=True)
    try:
        svc = get_service(ctx.obj.get("credentials") if ctx.obj else None)
        result = tags_mod.delete_tag(svc, aid, cid, wid, tag_id)
        output(result, message=f"Tag {tag_id} deleted.")
    except Exception as e:
        handle_error(e)


@tag.command("revert")
@click.argument("tag_id")
@click.option("--account-id", default=None)
@click.option("--container-id", default=None)
@click.option("--workspace-id", default=None)
@click.option("--json", "use_json", is_flag=True, default=False)
@click.pass_context
def tag_revert(ctx, tag_id, account_id, container_id, workspace_id, use_json):
    """Revert changes to a tag."""
    global _json_output
    if use_json:
        _json_output = True
    aid, cid, wid = _resolve_ids(ctx.obj, account_id=account_id,
                                  container_id=container_id, workspace_id=workspace_id)
    if not all([aid, cid, wid]):
        handle_error(ValueError("account_id, container_id, and workspace_id are required."))
        return
    try:
        svc = get_service(ctx.obj.get("credentials") if ctx.obj else None)
        result = tags_mod.revert_tag(svc, aid, cid, wid, tag_id)
        output(result, message=f"Tag {tag_id} reverted.")
    except Exception as e:
        handle_error(e)


# ── Trigger commands ──────────────────────────────────────────────────

@cli.group()
def trigger():
    """Trigger management."""
    pass


def _add_workspace_opts(cmd):
    """Decorator to add workspace options to a command."""
    cmd = click.option("--workspace-id", default=None)(cmd)
    cmd = click.option("--container-id", default=None)(cmd)
    cmd = click.option("--account-id", default=None)(cmd)
    return cmd


@trigger.command("list")
@click.option("--account-id", default=None)
@click.option("--container-id", default=None)
@click.option("--workspace-id", default=None)
@click.option("--json", "use_json", is_flag=True, default=False)
@click.pass_context
def trigger_list(ctx, account_id, container_id, workspace_id, use_json):
    """List all triggers in a workspace."""
    global _json_output
    if use_json:
        _json_output = True
    aid, cid, wid = _resolve_ids(ctx.obj, account_id=account_id,
                                  container_id=container_id, workspace_id=workspace_id)
    if not all([aid, cid, wid]):
        handle_error(ValueError("account_id, container_id, and workspace_id are required."))
        return
    try:
        svc = get_service(ctx.obj.get("credentials") if ctx.obj else None)
        triggers = trig_mod.list_triggers(svc, aid, cid, wid)
        if _json_output:
            output(triggers)
        else:
            skin = ReplSkin("google_tag_manager")
            skin.table(
                trig_mod.TRIGGER_TABLE_HEADERS,
                [trig_mod.format_trigger_row(t) for t in triggers]
            )
            click.echo(f"\n  {len(triggers)} trigger(s) found.")
    except Exception as e:
        handle_error(e)


@trigger.command("get")
@click.argument("trigger_id")
@click.option("--account-id", default=None)
@click.option("--container-id", default=None)
@click.option("--workspace-id", default=None)
@click.option("--json", "use_json", is_flag=True, default=False)
@click.pass_context
def trigger_get(ctx, trigger_id, account_id, container_id, workspace_id, use_json):
    """Get a specific trigger."""
    global _json_output
    if use_json:
        _json_output = True
    aid, cid, wid = _resolve_ids(ctx.obj, account_id=account_id,
                                  container_id=container_id, workspace_id=workspace_id)
    if not all([aid, cid, wid]):
        handle_error(ValueError("account_id, container_id, and workspace_id are required."))
        return
    try:
        svc = get_service(ctx.obj.get("credentials") if ctx.obj else None)
        result = trig_mod.get_trigger(svc, aid, cid, wid, trigger_id)
        output(result)
    except Exception as e:
        handle_error(e)


@trigger.command("create")
@click.argument("name")
@click.option("--type", "-t", "trigger_type", required=True,
              help="Trigger type (e.g., pageview, click, customEvent).")
@click.option("--account-id", default=None)
@click.option("--container-id", default=None)
@click.option("--workspace-id", default=None)
@click.option("--filter", "-f", "filters", multiple=True,
              help="Filter condition as JSON.")
@click.option("--json", "use_json", is_flag=True, default=False)
@click.pass_context
def trigger_create(ctx, name, trigger_type, account_id, container_id, workspace_id,
                   filters, use_json):
    """Create a new trigger."""
    global _json_output
    if use_json:
        _json_output = True
    aid, cid, wid = _resolve_ids(ctx.obj, account_id=account_id,
                                  container_id=container_id, workspace_id=workspace_id)
    if not all([aid, cid, wid]):
        handle_error(ValueError("account_id, container_id, and workspace_id are required."))
        return
    try:
        filter_list = [json.loads(f) for f in filters] if filters else None
        svc = get_service(ctx.obj.get("credentials") if ctx.obj else None)
        result = trig_mod.create_trigger(svc, aid, cid, wid, name, trigger_type,
                                          filters=filter_list)
        output(result, message=f"Trigger '{name}' created.")
    except Exception as e:
        handle_error(e)


@trigger.command("update")
@click.argument("trigger_id")
@click.option("--account-id", default=None)
@click.option("--container-id", default=None)
@click.option("--workspace-id", default=None)
@click.option("--name", "-n", default=None)
@click.option("--json", "use_json", is_flag=True, default=False)
@click.pass_context
def trigger_update(ctx, trigger_id, account_id, container_id, workspace_id, name, use_json):
    """Update a trigger."""
    global _json_output
    if use_json:
        _json_output = True
    aid, cid, wid = _resolve_ids(ctx.obj, account_id=account_id,
                                  container_id=container_id, workspace_id=workspace_id)
    if not all([aid, cid, wid]):
        handle_error(ValueError("account_id, container_id, and workspace_id are required."))
        return
    try:
        svc = get_service(ctx.obj.get("credentials") if ctx.obj else None)
        result = trig_mod.update_trigger(svc, aid, cid, wid, trigger_id, name=name)
        output(result, message="Trigger updated.")
    except Exception as e:
        handle_error(e)


@trigger.command("delete")
@click.argument("trigger_id")
@click.option("--account-id", default=None)
@click.option("--container-id", default=None)
@click.option("--workspace-id", default=None)
@click.option("--force", is_flag=True, default=False)
@click.option("--json", "use_json", is_flag=True, default=False)
@click.pass_context
def trigger_delete(ctx, trigger_id, account_id, container_id, workspace_id, force, use_json):
    """Delete a trigger."""
    global _json_output
    if use_json:
        _json_output = True
    aid, cid, wid = _resolve_ids(ctx.obj, account_id=account_id,
                                  container_id=container_id, workspace_id=workspace_id)
    if not all([aid, cid, wid]):
        handle_error(ValueError("account_id, container_id, and workspace_id are required."))
        return
    if not force and not _json_output:
        click.confirm(f"Delete trigger {trigger_id}?", abort=True)
    try:
        svc = get_service(ctx.obj.get("credentials") if ctx.obj else None)
        result = trig_mod.delete_trigger(svc, aid, cid, wid, trigger_id)
        output(result, message=f"Trigger {trigger_id} deleted.")
    except Exception as e:
        handle_error(e)


@trigger.command("revert")
@click.argument("trigger_id")
@click.option("--account-id", default=None)
@click.option("--container-id", default=None)
@click.option("--workspace-id", default=None)
@click.option("--json", "use_json", is_flag=True, default=False)
@click.pass_context
def trigger_revert(ctx, trigger_id, account_id, container_id, workspace_id, use_json):
    """Revert changes to a trigger."""
    global _json_output
    if use_json:
        _json_output = True
    aid, cid, wid = _resolve_ids(ctx.obj, account_id=account_id,
                                  container_id=container_id, workspace_id=workspace_id)
    if not all([aid, cid, wid]):
        handle_error(ValueError("account_id, container_id, and workspace_id are required."))
        return
    try:
        svc = get_service(ctx.obj.get("credentials") if ctx.obj else None)
        result = trig_mod.revert_trigger(svc, aid, cid, wid, trigger_id)
        output(result, message=f"Trigger {trigger_id} reverted.")
    except Exception as e:
        handle_error(e)


# ── Variable commands ─────────────────────────────────────────────────

@cli.group()
def variable():
    """Variable management."""
    pass


@variable.command("list")
@click.option("--account-id", default=None)
@click.option("--container-id", default=None)
@click.option("--workspace-id", default=None)
@click.option("--json", "use_json", is_flag=True, default=False)
@click.pass_context
def variable_list(ctx, account_id, container_id, workspace_id, use_json):
    """List all variables in a workspace."""
    global _json_output
    if use_json:
        _json_output = True
    aid, cid, wid = _resolve_ids(ctx.obj, account_id=account_id,
                                  container_id=container_id, workspace_id=workspace_id)
    if not all([aid, cid, wid]):
        handle_error(ValueError("account_id, container_id, and workspace_id are required."))
        return
    try:
        svc = get_service(ctx.obj.get("credentials") if ctx.obj else None)
        variables = var_mod.list_variables(svc, aid, cid, wid)
        if _json_output:
            output(variables)
        else:
            skin = ReplSkin("google_tag_manager")
            skin.table(
                var_mod.VARIABLE_TABLE_HEADERS,
                [var_mod.format_variable_row(v) for v in variables]
            )
            click.echo(f"\n  {len(variables)} variable(s) found.")
    except Exception as e:
        handle_error(e)


@variable.command("get")
@click.argument("variable_id")
@click.option("--account-id", default=None)
@click.option("--container-id", default=None)
@click.option("--workspace-id", default=None)
@click.option("--json", "use_json", is_flag=True, default=False)
@click.pass_context
def variable_get(ctx, variable_id, account_id, container_id, workspace_id, use_json):
    """Get a specific variable."""
    global _json_output
    if use_json:
        _json_output = True
    aid, cid, wid = _resolve_ids(ctx.obj, account_id=account_id,
                                  container_id=container_id, workspace_id=workspace_id)
    if not all([aid, cid, wid]):
        handle_error(ValueError("account_id, container_id, and workspace_id are required."))
        return
    try:
        svc = get_service(ctx.obj.get("credentials") if ctx.obj else None)
        result = var_mod.get_variable(svc, aid, cid, wid, variable_id)
        output(result)
    except Exception as e:
        handle_error(e)


@variable.command("create")
@click.argument("name")
@click.option("--type", "-t", "var_type", required=True,
              help="Variable type (e.g., v, d, k, j, u).")
@click.option("--account-id", default=None)
@click.option("--container-id", default=None)
@click.option("--workspace-id", default=None)
@click.option("--param", "-p", "params", multiple=True,
              help="Parameter as JSON.")
@click.option("--json", "use_json", is_flag=True, default=False)
@click.pass_context
def variable_create(ctx, name, var_type, account_id, container_id, workspace_id,
                    params, use_json):
    """Create a new variable."""
    global _json_output
    if use_json:
        _json_output = True
    aid, cid, wid = _resolve_ids(ctx.obj, account_id=account_id,
                                  container_id=container_id, workspace_id=workspace_id)
    if not all([aid, cid, wid]):
        handle_error(ValueError("account_id, container_id, and workspace_id are required."))
        return
    try:
        parameters = [json.loads(p) for p in params] if params else None
        svc = get_service(ctx.obj.get("credentials") if ctx.obj else None)
        result = var_mod.create_variable(svc, aid, cid, wid, name, var_type,
                                          parameters=parameters)
        output(result, message=f"Variable '{name}' created.")
    except Exception as e:
        handle_error(e)


@variable.command("update")
@click.argument("variable_id")
@click.option("--account-id", default=None)
@click.option("--container-id", default=None)
@click.option("--workspace-id", default=None)
@click.option("--name", "-n", default=None)
@click.option("--param", "-p", "params", multiple=True)
@click.option("--json", "use_json", is_flag=True, default=False)
@click.pass_context
def variable_update(ctx, variable_id, account_id, container_id, workspace_id,
                    name, params, use_json):
    """Update a variable."""
    global _json_output
    if use_json:
        _json_output = True
    aid, cid, wid = _resolve_ids(ctx.obj, account_id=account_id,
                                  container_id=container_id, workspace_id=workspace_id)
    if not all([aid, cid, wid]):
        handle_error(ValueError("account_id, container_id, and workspace_id are required."))
        return
    try:
        parameters = [json.loads(p) for p in params] if params else None
        svc = get_service(ctx.obj.get("credentials") if ctx.obj else None)
        result = var_mod.update_variable(svc, aid, cid, wid, variable_id,
                                          name=name, parameters=parameters)
        output(result, message="Variable updated.")
    except Exception as e:
        handle_error(e)


@variable.command("delete")
@click.argument("variable_id")
@click.option("--account-id", default=None)
@click.option("--container-id", default=None)
@click.option("--workspace-id", default=None)
@click.option("--force", is_flag=True, default=False)
@click.option("--json", "use_json", is_flag=True, default=False)
@click.pass_context
def variable_delete(ctx, variable_id, account_id, container_id, workspace_id, force, use_json):
    """Delete a variable."""
    global _json_output
    if use_json:
        _json_output = True
    aid, cid, wid = _resolve_ids(ctx.obj, account_id=account_id,
                                  container_id=container_id, workspace_id=workspace_id)
    if not all([aid, cid, wid]):
        handle_error(ValueError("account_id, container_id, and workspace_id are required."))
        return
    if not force and not _json_output:
        click.confirm(f"Delete variable {variable_id}?", abort=True)
    try:
        svc = get_service(ctx.obj.get("credentials") if ctx.obj else None)
        result = var_mod.delete_variable(svc, aid, cid, wid, variable_id)
        output(result, message=f"Variable {variable_id} deleted.")
    except Exception as e:
        handle_error(e)


@variable.command("revert")
@click.argument("variable_id")
@click.option("--account-id", default=None)
@click.option("--container-id", default=None)
@click.option("--workspace-id", default=None)
@click.option("--json", "use_json", is_flag=True, default=False)
@click.pass_context
def variable_revert(ctx, variable_id, account_id, container_id, workspace_id, use_json):
    """Revert changes to a variable."""
    global _json_output
    if use_json:
        _json_output = True
    aid, cid, wid = _resolve_ids(ctx.obj, account_id=account_id,
                                  container_id=container_id, workspace_id=workspace_id)
    if not all([aid, cid, wid]):
        handle_error(ValueError("account_id, container_id, and workspace_id are required."))
        return
    try:
        svc = get_service(ctx.obj.get("credentials") if ctx.obj else None)
        result = var_mod.revert_variable(svc, aid, cid, wid, variable_id)
        output(result, message=f"Variable {variable_id} reverted.")
    except Exception as e:
        handle_error(e)


# ── Folder commands ───────────────────────────────────────────────────

@cli.group()
def folder():
    """Folder management."""
    pass


@folder.command("list")
@click.option("--account-id", default=None)
@click.option("--container-id", default=None)
@click.option("--workspace-id", default=None)
@click.option("--json", "use_json", is_flag=True, default=False)
@click.pass_context
def folder_list(ctx, account_id, container_id, workspace_id, use_json):
    """List all folders in a workspace."""
    global _json_output
    if use_json:
        _json_output = True
    aid, cid, wid = _resolve_ids(ctx.obj, account_id=account_id,
                                  container_id=container_id, workspace_id=workspace_id)
    if not all([aid, cid, wid]):
        handle_error(ValueError("account_id, container_id, and workspace_id are required."))
        return
    try:
        svc = get_service(ctx.obj.get("credentials") if ctx.obj else None)
        folders = folder_mod.list_folders(svc, aid, cid, wid)
        if _json_output:
            output(folders)
        else:
            skin = ReplSkin("google_tag_manager")
            skin.table(
                folder_mod.FOLDER_TABLE_HEADERS,
                [folder_mod.format_folder_row(f) for f in folders]
            )
            click.echo(f"\n  {len(folders)} folder(s) found.")
    except Exception as e:
        handle_error(e)


@folder.command("get")
@click.argument("folder_id")
@click.option("--account-id", default=None)
@click.option("--container-id", default=None)
@click.option("--workspace-id", default=None)
@click.option("--json", "use_json", is_flag=True, default=False)
@click.pass_context
def folder_get(ctx, folder_id, account_id, container_id, workspace_id, use_json):
    """Get a specific folder."""
    global _json_output
    if use_json:
        _json_output = True
    aid, cid, wid = _resolve_ids(ctx.obj, account_id=account_id,
                                  container_id=container_id, workspace_id=workspace_id)
    if not all([aid, cid, wid]):
        handle_error(ValueError("account_id, container_id, and workspace_id are required."))
        return
    try:
        svc = get_service(ctx.obj.get("credentials") if ctx.obj else None)
        result = folder_mod.get_folder(svc, aid, cid, wid, folder_id)
        output(result)
    except Exception as e:
        handle_error(e)


@folder.command("create")
@click.argument("name")
@click.option("--account-id", default=None)
@click.option("--container-id", default=None)
@click.option("--workspace-id", default=None)
@click.option("--json", "use_json", is_flag=True, default=False)
@click.pass_context
def folder_create(ctx, name, account_id, container_id, workspace_id, use_json):
    """Create a new folder."""
    global _json_output
    if use_json:
        _json_output = True
    aid, cid, wid = _resolve_ids(ctx.obj, account_id=account_id,
                                  container_id=container_id, workspace_id=workspace_id)
    if not all([aid, cid, wid]):
        handle_error(ValueError("account_id, container_id, and workspace_id are required."))
        return
    try:
        svc = get_service(ctx.obj.get("credentials") if ctx.obj else None)
        result = folder_mod.create_folder(svc, aid, cid, wid, name)
        output(result, message=f"Folder '{name}' created.")
    except Exception as e:
        handle_error(e)


@folder.command("update")
@click.argument("folder_id")
@click.argument("name")
@click.option("--account-id", default=None)
@click.option("--container-id", default=None)
@click.option("--workspace-id", default=None)
@click.option("--json", "use_json", is_flag=True, default=False)
@click.pass_context
def folder_update(ctx, folder_id, name, account_id, container_id, workspace_id, use_json):
    """Rename a folder."""
    global _json_output
    if use_json:
        _json_output = True
    aid, cid, wid = _resolve_ids(ctx.obj, account_id=account_id,
                                  container_id=container_id, workspace_id=workspace_id)
    if not all([aid, cid, wid]):
        handle_error(ValueError("account_id, container_id, and workspace_id are required."))
        return
    try:
        svc = get_service(ctx.obj.get("credentials") if ctx.obj else None)
        result = folder_mod.update_folder(svc, aid, cid, wid, folder_id, name)
        output(result, message="Folder updated.")
    except Exception as e:
        handle_error(e)


@folder.command("delete")
@click.argument("folder_id")
@click.option("--account-id", default=None)
@click.option("--container-id", default=None)
@click.option("--workspace-id", default=None)
@click.option("--force", is_flag=True, default=False)
@click.option("--json", "use_json", is_flag=True, default=False)
@click.pass_context
def folder_delete(ctx, folder_id, account_id, container_id, workspace_id, force, use_json):
    """Delete a folder."""
    global _json_output
    if use_json:
        _json_output = True
    aid, cid, wid = _resolve_ids(ctx.obj, account_id=account_id,
                                  container_id=container_id, workspace_id=workspace_id)
    if not all([aid, cid, wid]):
        handle_error(ValueError("account_id, container_id, and workspace_id are required."))
        return
    if not force and not _json_output:
        click.confirm(f"Delete folder {folder_id}?", abort=True)
    try:
        svc = get_service(ctx.obj.get("credentials") if ctx.obj else None)
        result = folder_mod.delete_folder(svc, aid, cid, wid, folder_id)
        output(result, message=f"Folder {folder_id} deleted.")
    except Exception as e:
        handle_error(e)


@folder.command("entities")
@click.argument("folder_id")
@click.option("--account-id", default=None)
@click.option("--container-id", default=None)
@click.option("--workspace-id", default=None)
@click.option("--json", "use_json", is_flag=True, default=False)
@click.pass_context
def folder_entities_cmd(ctx, folder_id, account_id, container_id, workspace_id, use_json):
    """List entities (tags, triggers, variables) in a folder."""
    global _json_output
    if use_json:
        _json_output = True
    aid, cid, wid = _resolve_ids(ctx.obj, account_id=account_id,
                                  container_id=container_id, workspace_id=workspace_id)
    if not all([aid, cid, wid]):
        handle_error(ValueError("account_id, container_id, and workspace_id are required."))
        return
    try:
        svc = get_service(ctx.obj.get("credentials") if ctx.obj else None)
        result = folder_mod.folder_entities(svc, aid, cid, wid, folder_id)
        output(result)
    except Exception as e:
        handle_error(e)


@folder.command("move")
@click.argument("folder_id")
@click.option("--account-id", default=None)
@click.option("--container-id", default=None)
@click.option("--workspace-id", default=None)
@click.option("--tag", "-t", "tag_ids", multiple=True, help="Tag ID(s) to move.")
@click.option("--trigger", "-T", "trigger_ids", multiple=True, help="Trigger ID(s) to move.")
@click.option("--variable", "-v", "variable_ids", multiple=True, help="Variable ID(s) to move.")
@click.option("--json", "use_json", is_flag=True, default=False)
@click.pass_context
def folder_move(ctx, folder_id, account_id, container_id, workspace_id,
                tag_ids, trigger_ids, variable_ids, use_json):
    """Move entities into a folder."""
    global _json_output
    if use_json:
        _json_output = True
    aid, cid, wid = _resolve_ids(ctx.obj, account_id=account_id,
                                  container_id=container_id, workspace_id=workspace_id)
    if not all([aid, cid, wid]):
        handle_error(ValueError("account_id, container_id, and workspace_id are required."))
        return
    try:
        svc = get_service(ctx.obj.get("credentials") if ctx.obj else None)
        result = folder_mod.move_to_folder(
            svc, aid, cid, wid, folder_id,
            tag_ids=list(tag_ids) if tag_ids else None,
            trigger_ids=list(trigger_ids) if trigger_ids else None,
            variable_ids=list(variable_ids) if variable_ids else None,
        )
        output(result, message="Entities moved to folder.")
    except Exception as e:
        handle_error(e)


# ── Environment commands ──────────────────────────────────────────────

@cli.group()
@click.pass_context
def env(ctx):
    """Environment management."""
    pass


@env.command("list")
@click.option("--account-id", default=None)
@click.option("--container-id", default=None)
@click.option("--json", "use_json", is_flag=True, default=False)
@click.pass_context
def env_list(ctx, account_id, container_id, use_json):
    """List all environments for a container."""
    global _json_output
    if use_json:
        _json_output = True
    aid, cid, _ = _resolve_ids(ctx.obj, account_id=account_id, container_id=container_id)
    if not aid or not cid:
        handle_error(ValueError("account_id and container_id are required."))
        return
    try:
        svc = get_service(ctx.obj.get("credentials") if ctx.obj else None)
        envs = env_mod.list_environments(svc, aid, cid)
        if _json_output:
            output(envs)
        else:
            skin = ReplSkin("google_tag_manager")
            skin.table(
                env_mod.ENVIRONMENT_TABLE_HEADERS,
                [env_mod.format_environment_row(e) for e in envs]
            )
            click.echo(f"\n  {len(envs)} environment(s) found.")
    except Exception as e:
        handle_error(e)


@env.command("get")
@click.argument("environment_id")
@click.option("--account-id", default=None)
@click.option("--container-id", default=None)
@click.option("--json", "use_json", is_flag=True, default=False)
@click.pass_context
def env_get(ctx, environment_id, account_id, container_id, use_json):
    """Get a specific environment."""
    global _json_output
    if use_json:
        _json_output = True
    aid, cid, _ = _resolve_ids(ctx.obj, account_id=account_id, container_id=container_id)
    if not aid or not cid:
        handle_error(ValueError("account_id and container_id are required."))
        return
    try:
        svc = get_service(ctx.obj.get("credentials") if ctx.obj else None)
        result = env_mod.get_environment(svc, aid, cid, environment_id)
        output(result)
    except Exception as e:
        handle_error(e)


@env.command("create")
@click.argument("name")
@click.option("--account-id", default=None)
@click.option("--container-id", default=None)
@click.option("--type", "env_type", default="user",
              type=click.Choice(["live", "latest", "user"]))
@click.option("--description", "-d", default="")
@click.option("--url", "-u", default="")
@click.option("--json", "use_json", is_flag=True, default=False)
@click.pass_context
def env_create(ctx, name, account_id, container_id, env_type, description, url, use_json):
    """Create a new environment."""
    global _json_output
    if use_json:
        _json_output = True
    aid, cid, _ = _resolve_ids(ctx.obj, account_id=account_id, container_id=container_id)
    if not aid or not cid:
        handle_error(ValueError("account_id and container_id are required."))
        return
    try:
        svc = get_service(ctx.obj.get("credentials") if ctx.obj else None)
        result = env_mod.create_environment(svc, aid, cid, name, env_type, description, url)
        output(result, message=f"Environment '{name}' created.")
    except Exception as e:
        handle_error(e)


@env.command("update")
@click.argument("environment_id")
@click.option("--account-id", default=None)
@click.option("--container-id", default=None)
@click.option("--name", "-n", default=None)
@click.option("--description", "-d", default=None)
@click.option("--url", "-u", default=None)
@click.option("--json", "use_json", is_flag=True, default=False)
@click.pass_context
def env_update(ctx, environment_id, account_id, container_id, name, description, url, use_json):
    """Update an environment."""
    global _json_output
    if use_json:
        _json_output = True
    aid, cid, _ = _resolve_ids(ctx.obj, account_id=account_id, container_id=container_id)
    if not aid or not cid:
        handle_error(ValueError("account_id and container_id are required."))
        return
    try:
        svc = get_service(ctx.obj.get("credentials") if ctx.obj else None)
        result = env_mod.update_environment(svc, aid, cid, environment_id,
                                             name=name, description=description, url=url)
        output(result, message="Environment updated.")
    except Exception as e:
        handle_error(e)


@env.command("delete")
@click.argument("environment_id")
@click.option("--account-id", default=None)
@click.option("--container-id", default=None)
@click.option("--force", is_flag=True, default=False)
@click.option("--json", "use_json", is_flag=True, default=False)
@click.pass_context
def env_delete(ctx, environment_id, account_id, container_id, force, use_json):
    """Delete an environment."""
    global _json_output
    if use_json:
        _json_output = True
    aid, cid, _ = _resolve_ids(ctx.obj, account_id=account_id, container_id=container_id)
    if not aid or not cid:
        handle_error(ValueError("account_id and container_id are required."))
        return
    if not force and not _json_output:
        click.confirm(f"Delete environment {environment_id}?", abort=True)
    try:
        svc = get_service(ctx.obj.get("credentials") if ctx.obj else None)
        result = env_mod.delete_environment(svc, aid, cid, environment_id)
        output(result, message=f"Environment {environment_id} deleted.")
    except Exception as e:
        handle_error(e)


@env.command("reauth")
@click.argument("environment_id")
@click.option("--account-id", default=None)
@click.option("--container-id", default=None)
@click.option("--json", "use_json", is_flag=True, default=False)
@click.pass_context
def env_reauth(ctx, environment_id, account_id, container_id, use_json):
    """Reauthorize an environment (regenerate auth code)."""
    global _json_output
    if use_json:
        _json_output = True
    aid, cid, _ = _resolve_ids(ctx.obj, account_id=account_id, container_id=container_id)
    if not aid or not cid:
        handle_error(ValueError("account_id and container_id are required."))
        return
    try:
        svc = get_service(ctx.obj.get("credentials") if ctx.obj else None)
        result = env_mod.reauthorize_environment(svc, aid, cid, environment_id)
        output(result, message="Environment reauthorized.")
    except Exception as e:
        handle_error(e)


# ── Version commands ──────────────────────────────────────────────────

@cli.group()
def version():
    """Version management."""
    pass


@version.command("list")
@click.option("--account-id", default=None)
@click.option("--container-id", default=None)
@click.option("--include-deleted", is_flag=True, default=False)
@click.option("--json", "use_json", is_flag=True, default=False)
@click.pass_context
def version_list(ctx, account_id, container_id, include_deleted, use_json):
    """List all version headers for a container."""
    global _json_output
    if use_json:
        _json_output = True
    aid, cid, _ = _resolve_ids(ctx.obj, account_id=account_id, container_id=container_id)
    if not aid or not cid:
        handle_error(ValueError("account_id and container_id are required."))
        return
    try:
        svc = get_service(ctx.obj.get("credentials") if ctx.obj else None)
        headers = ver_mod.list_version_headers(svc, aid, cid,
                                                include_deleted=include_deleted)
        if _json_output:
            output(headers)
        else:
            skin = ReplSkin("google_tag_manager")
            skin.table(
                ver_mod.VERSION_TABLE_HEADERS,
                [ver_mod.format_version_row(v) for v in headers]
            )
            click.echo(f"\n  {len(headers)} version(s) found.")
    except Exception as e:
        handle_error(e)


@version.command("latest")
@click.option("--account-id", default=None)
@click.option("--container-id", default=None)
@click.option("--json", "use_json", is_flag=True, default=False)
@click.pass_context
def version_latest(ctx, account_id, container_id, use_json):
    """Get the latest version header for a container."""
    global _json_output
    if use_json:
        _json_output = True
    aid, cid, _ = _resolve_ids(ctx.obj, account_id=account_id, container_id=container_id)
    if not aid or not cid:
        handle_error(ValueError("account_id and container_id are required."))
        return
    try:
        svc = get_service(ctx.obj.get("credentials") if ctx.obj else None)
        result = ver_mod.latest_version_header(svc, aid, cid)
        output(result)
    except Exception as e:
        handle_error(e)


# ── Permission commands ───────────────────────────────────────────────

@cli.group()
def permission():
    """User permission management."""
    pass


@permission.command("list")
@click.argument("account_id", required=False)
@click.option("--json", "use_json", is_flag=True, default=False)
@click.pass_context
def permission_list(ctx, account_id, use_json):
    """List all user permissions for a GTM account."""
    global _json_output
    if use_json:
        _json_output = True
    aid, _, _ = _resolve_ids(ctx.obj, account_id=account_id)
    if not aid:
        handle_error(ValueError("account_id is required."))
        return
    try:
        svc = get_service(ctx.obj.get("credentials") if ctx.obj else None)
        perms = perm_mod.list_permissions(svc, aid)
        if _json_output:
            output(perms)
        else:
            skin = ReplSkin("google_tag_manager")
            skin.table(
                perm_mod.PERMISSION_TABLE_HEADERS,
                [perm_mod.format_permission_row(p) for p in perms]
            )
            click.echo(f"\n  {len(perms)} permission(s) found.")
    except Exception as e:
        handle_error(e)


@permission.command("get")
@click.argument("user_permission_id")
@click.option("--account-id", default=None)
@click.option("--json", "use_json", is_flag=True, default=False)
@click.pass_context
def permission_get(ctx, user_permission_id, account_id, use_json):
    """Get a specific user permission."""
    global _json_output
    if use_json:
        _json_output = True
    aid, _, _ = _resolve_ids(ctx.obj, account_id=account_id)
    if not aid:
        handle_error(ValueError("account_id is required."))
        return
    try:
        svc = get_service(ctx.obj.get("credentials") if ctx.obj else None)
        result = perm_mod.get_permission(svc, aid, user_permission_id)
        output(result)
    except Exception as e:
        handle_error(e)


@permission.command("grant")
@click.argument("email")
@click.option("--account-id", default=None)
@click.option("--access", "-a", "account_access", default="user",
              type=click.Choice(["admin", "user", "noAccess"]),
              help="Account-level access.")
@click.option("--container-access", "-c", multiple=True,
              help='Container access as JSON, e.g. \'{"containerId":"123","permission":"edit"}\'')
@click.option("--json", "use_json", is_flag=True, default=False)
@click.pass_context
def permission_grant(ctx, email, account_id, account_access, container_access, use_json):
    """Grant permissions to a user."""
    global _json_output
    if use_json:
        _json_output = True
    aid, _, _ = _resolve_ids(ctx.obj, account_id=account_id)
    if not aid:
        handle_error(ValueError("account_id is required."))
        return
    try:
        ca = [json.loads(c) for c in container_access] if container_access else None
        svc = get_service(ctx.obj.get("credentials") if ctx.obj else None)
        result = perm_mod.create_permission(svc, aid, email, account_access, ca)
        output(result, message=f"Permissions granted to {email}.")
    except Exception as e:
        handle_error(e)


@permission.command("update")
@click.argument("user_permission_id")
@click.option("--account-id", default=None)
@click.option("--access", "-a", "account_access", default=None,
              type=click.Choice(["admin", "user", "noAccess"]))
@click.option("--container-access", "-c", multiple=True)
@click.option("--json", "use_json", is_flag=True, default=False)
@click.pass_context
def permission_update(ctx, user_permission_id, account_id, account_access,
                      container_access, use_json):
    """Update user permissions."""
    global _json_output
    if use_json:
        _json_output = True
    aid, _, _ = _resolve_ids(ctx.obj, account_id=account_id)
    if not aid:
        handle_error(ValueError("account_id is required."))
        return
    try:
        ca = [json.loads(c) for c in container_access] if container_access else None
        svc = get_service(ctx.obj.get("credentials") if ctx.obj else None)
        result = perm_mod.update_permission(svc, aid, user_permission_id,
                                             account_access=account_access,
                                             container_accesses=ca)
        output(result, message="Permissions updated.")
    except Exception as e:
        handle_error(e)


@permission.command("revoke")
@click.argument("user_permission_id")
@click.option("--account-id", default=None)
@click.option("--force", is_flag=True, default=False)
@click.option("--json", "use_json", is_flag=True, default=False)
@click.pass_context
def permission_revoke(ctx, user_permission_id, account_id, force, use_json):
    """Revoke (delete) user permissions."""
    global _json_output
    if use_json:
        _json_output = True
    aid, _, _ = _resolve_ids(ctx.obj, account_id=account_id)
    if not aid:
        handle_error(ValueError("account_id is required."))
        return
    if not force and not _json_output:
        click.confirm(f"Revoke permissions for user {user_permission_id}?", abort=True)
    try:
        svc = get_service(ctx.obj.get("credentials") if ctx.obj else None)
        result = perm_mod.delete_permission(svc, aid, user_permission_id)
        output(result, message=f"Permissions revoked for {user_permission_id}.")
    except Exception as e:
        handle_error(e)


# ── Entry point ───────────────────────────────────────────────────────

def main():
    """Main entry point for the GTM CLI."""
    cli()


if __name__ == "__main__":
    main()
