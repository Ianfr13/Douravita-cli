"""Audit log operations for Infisical CLI."""

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


def _truncate(text: str, width: int) -> str:
    if text is None:
        return ""
    s = str(text)
    if len(s) <= width:
        return s
    return s[: max(0, width - 1)] + "…"


class AuditClient:
    """High-level client for audit-log exports."""

    def __init__(self, backend: InfisicalBackend):
        self.backend = backend

    def export(
        self,
        organization_id: str,
        project_id: str | None = None,
        event_type: str | None = None,
        actor: str | None = None,
        user_agent_type: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[dict]:
        return self.backend.export_audit_logs(
            organization_id=organization_id,
            project_id=project_id,
            event_type=event_type,
            actor=actor,
            user_agent_type=user_agent_type,
            start_date=start_date,
            end_date=end_date,
            offset=offset,
            limit=limit,
        )


# ---------------------------------------------------------------------------
# Click group
# ---------------------------------------------------------------------------


@click.group("audit")
def audit_group() -> None:
    """Export and inspect audit logs."""


@audit_group.command("export")
@click.option(
    "--org-id",
    "org_id",
    envvar="INFISICAL_ORG_ID",
    required=True,
    help="Organization ID (or set INFISICAL_ORG_ID).",
)
@click.option("--project", "project_id", default=None, help="Scope to a project ID.")
@click.option("--event-type", "event_type", default=None, help="Filter by event type.")
@click.option("--actor", default=None, help="Filter by actor.")
@click.option(
    "--user-agent-type",
    "user_agent_type",
    type=click.Choice(["web", "cli", "k8-operator", "terraform"]),
    default=None,
    help="Filter by user-agent type.",
)
@click.option("--start-date", "start_date", default=None, help="ISO start date.")
@click.option("--end-date", "end_date", default=None, help="ISO end date.")
@click.option("--limit", type=int, default=20, show_default=True)
@click.option("--offset", type=int, default=0, show_default=True)
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def audit_export(
    click_ctx: click.Context,
    org_id: str,
    project_id: str | None,
    event_type: str | None,
    actor: str | None,
    user_agent_type: str | None,
    start_date: str | None,
    end_date: str | None,
    limit: int,
    offset: int,
    output_json: bool,
) -> None:
    """Export audit logs for an organization."""
    ctx = click_ctx.obj
    _require_token(ctx)
    use_json = output_json or ctx.output_json
    try:
        client = AuditClient(ctx.backend())
        result = client.export(
            organization_id=org_id,
            project_id=project_id,
            event_type=event_type,
            actor=actor,
            user_agent_type=user_agent_type,
            start_date=start_date,
            end_date=end_date,
            offset=offset,
            limit=limit,
        )
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return

    if use_json:
        _print_json(result)
        return

    if not result:
        skin.info("No audit logs found.")
        return

    headers = ["TIMESTAMP", "ACTOR", "EVENT_TYPE", "IP"]
    rows = []
    for log in result:
        ts = log.get("createdAt") or log.get("timestamp", "")
        actor_obj = log.get("actor") or {}
        if isinstance(actor_obj, dict):
            meta = actor_obj.get("metadata") or {}
            actor_name = (
                meta.get("email")
                or meta.get("username")
                or meta.get("name")
                or actor_obj.get("type", "")
            )
        else:
            actor_name = str(actor_obj)
        event = log.get("event") or {}
        event_type_val = (
            event.get("type") if isinstance(event, dict) else str(event)
        ) or log.get("eventType", "")
        ip = log.get("ipAddress") or log.get("ip", "")
        rows.append(
            [
                _truncate(ts, 25),
                _truncate(actor_name, 30),
                _truncate(event_type_val, 30),
                _truncate(ip, 20),
            ]
        )
    skin.table(headers, rows, max_col_width=60)


__all__ = ["AuditClient", "audit_group"]
