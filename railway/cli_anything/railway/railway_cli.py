"""cli-anything Railway — main CLI entry point.

Entry point: cli-anything-railway
Default behaviour (no sub-command): launch interactive REPL.
"""

from __future__ import annotations

import os
import sys

import click

from cli_anything.railway.utils.repl_skin import ReplSkin
from cli_anything.railway.utils.railway_backend import RailwayBackend, RailwayAPIError
from cli_anything.railway.core.projects import projects_group
from cli_anything.railway.core.services import services_group
from cli_anything.railway.core.deployments import deployments_group
from cli_anything.railway.core.variables import variables_group
from cli_anything.railway.core.environments import environments_group
from cli_anything.railway.core.logs import logs_group
from cli_anything.railway.core.domains import domains_group
from cli_anything.railway.core.volumes import volumes_group
from cli_anything.railway.core.metrics import metrics_group
from cli_anything.railway.core.templates import templates_group
from cli_anything.railway.core.service_config import service_config_group
from cli_anything.railway.core.tcp_proxies import tcp_proxies_group
from cli_anything.railway.core.webhooks import webhooks_group
from cli_anything.railway.core.team import team_group
from cli_anything.railway.core.networking import networking_group
from cli_anything.railway.core.git import git_group
from cli_anything.railway.core.platform import platform_group


# ---------------------------------------------------------------------------
# Root group
# ---------------------------------------------------------------------------

@click.group(invoke_without_command=True)
@click.option(
    "--token",
    envvar="RAILWAY_TOKEN",
    default=None,
    help="Railway API token (defaults to $RAILWAY_TOKEN).",
)
@click.option("--json", "as_json", is_flag=True, hidden=True)
@click.version_option("1.0.0", prog_name="cli-anything-railway")
@click.pass_context
def main(ctx: click.Context, token: str | None, as_json: bool):
    """cli-anything Railway — deploy and manage apps on Railway.

    When called without a sub-command an interactive REPL is started.
    """
    ctx.ensure_object(dict)

    skin = ReplSkin("railway", version="1.0.0")
    ctx.obj["skin"] = skin
    ctx.obj["as_json"] = as_json

    # Build backend lazily — only error when a command actually needs it.
    if token:
        try:
            ctx.obj["backend"] = RailwayBackend(token)
        except RailwayAPIError as exc:
            skin.error(str(exc))
            sys.exit(1)
    else:
        ctx.obj["backend"] = None  # will be built in REPL or fail per-command

    if ctx.invoked_subcommand is None:
        # No sub-command → start REPL
        _run_repl(skin, token)


# ---------------------------------------------------------------------------
# Attach command groups
# ---------------------------------------------------------------------------

main.add_command(projects_group)
main.add_command(services_group)
main.add_command(deployments_group)
main.add_command(variables_group)
main.add_command(environments_group)
main.add_command(logs_group)
main.add_command(domains_group)
main.add_command(volumes_group)
main.add_command(metrics_group)
main.add_command(templates_group)
main.add_command(service_config_group)
main.add_command(tcp_proxies_group)
main.add_command(webhooks_group)
main.add_command(team_group)
main.add_command(networking_group)
main.add_command(git_group)
main.add_command(platform_group)


# ---------------------------------------------------------------------------
# REPL
# ---------------------------------------------------------------------------

_REPL_HELP = {
    # --- Projects ---
    "projects list":                   "List all projects",
    "projects create <NAME>":          "Create a new project",
    "projects info <ID>":              "Show project details",
    "projects update <ID> --name/--description": "Update project name/description",
    "projects delete <ID>":            "Delete a project",
    "projects members <ID>":           "List project members",
    "projects transfer <ID> --workspace": "Transfer project to workspace",
    # --- Services ---
    "services list --project <ID>":    "List services in a project",
    "services info <ID>":              "Show service details",
    "services create <NAME> --project":"Create a new service",
    "services create-cron <N> <SCHED>":"Create a cron service",
    "services update <ID> --name":     "Rename a service",
    "services delete <ID>":            "Delete a service",
    # --- Deployments ---
    "deployments list --service <ID> [--env]": "List deployments for a service",
    "deployments trigger <ID> --env":  "Trigger a deployment",
    "deployments trigger-v2 <ID> --env": "Trigger deploy (returns deploy ID)",
    "deployments status <ID>":         "Show deployment status",
    "deployments rollback <ID>":       "Rollback to a deployment",
    "deployments restart <ID>":        "Restart without rebuild",
    "deployments cancel <ID>":         "Cancel in-progress deployment",
    "deployments stop <SVC> --env":    "Stop active deployment",
    "deployments redeploy <ID>":       "Redeploy an existing deployment",
    "deployments redeploy-latest <SVC> --env": "Redeploy latest for service",
    "deployments remove <ID>":         "Remove deployment from history",
    # --- Variables ---
    "variables list":                  "List environment variables",
    "variables set KEY VALUE":         "Set an environment variable",
    "variables delete KEY":            "Delete an environment variable",
    "variables bulk-set K=V K=V ...":  "Set multiple variables at once",
    "variables resolved --project --env --service": "Show resolved vars at deploy time",
    # --- Environments ---
    "environments list":               "List environments",
    "environments create <NAME>":      "Create an environment",
    "environments delete <ID>":        "Delete an environment",
    "environments rename <ID> <NAME>": "Rename an environment",
    "environments info <ID>":          "Show environment details + deploys",
    "environments staged-changes <ID>":"Show pending variable changes",
    # --- Logs ---
    "logs service <ID> --env <ID>":    "Show recent service logs",
    "logs deployment <ID>":            "Show deployment logs",
    "logs http <ID>":                  "Show HTTP request logs",
    "logs environment --env --project":"Show logs from all services in env",
    # --- Domains ---
    "domains list --service --env":    "List service domains",
    "domains create <D> --service --env": "Add custom domain",
    "domains delete <ID>":             "Delete a custom domain",
    "domains delete-railway <ID>":     "Delete a railway.app domain",
    "domains generate --service --env":"Generate railway.app domain",
    "domains check <DOMAIN>":          "Check if domain is available",
    "domains dns-status <ID> --project":"Show DNS/cert status for domain",
    "domains update <ID> --env --target-port": "Update custom domain port",
    # --- Volumes ---
    "volumes list --project <ID>":     "List volumes",
    "volumes create <NAME>":           "Create a volume",
    "volumes delete <ID>":             "Delete a volume",
    "volumes update <ID> --name":      "Rename a volume",
    "volumes info <INSTANCE_ID>":      "Show volume instance details",
    "volumes set-mount <VOL_ID> <PATH>": "Update volume mount path",
    "volumes backup-list <INST_ID>":   "List volume backups",
    "volumes backup-create <INST_ID>": "Create a volume backup",
    "volumes backup-restore <BK> <INST>": "Restore from backup",
    "volumes backup-delete <BK> <INST>":"Delete a backup",
    # --- Metrics ---
    "metrics service <ID> --env <ID>": "Show service metrics",
    # --- Templates ---
    "templates list":                  "List available templates",
    "templates deploy <CODE>":         "Deploy a template",
    # --- Service Config ---
    "service-config get <ID> --env":   "Show service build/start config",
    "service-config limits <ID> --env":"Show resource allocation limits",
    "service-config set-start-command":"Set start command",
    "service-config set-build-command":"Set build command",
    "service-config set-dockerfile":   "Set Dockerfile path",
    "service-config set-health-check": "Set health check path",
    "service-config set-restart-policy":"Set restart policy",
    "service-config set-root-dir":     "Set root directory",
    # --- TCP Proxies ---
    "tcp-proxies list --service --env":"List TCP proxies",
    "tcp-proxies create --service --env --port": "Create TCP proxy",
    "tcp-proxies delete <ID>":         "Delete TCP proxy",
    # --- Webhooks ---
    "webhooks list --project <ID>":    "List webhooks",
    "webhooks create <URL>":           "Create a webhook",
    "webhooks delete <ID>":            "Delete a webhook",
    # --- Team ---
    "team list":                       "List team members",
    "team invite <EMAIL> --team <ID>": "Invite a team member",
    "team remove <USER_ID> --team <ID>":"Remove a team member",
    # --- Networking ---
    "networking list --env <ID>":      "List private network endpoints",
    # --- Git ---
    "git connect <SVC> <REPO> <BRANCH>":"Connect Git repo to service",
    "git disconnect <SVC>":            "Disconnect Git repo",
    # --- Platform ---
    "platform status":                 "Check Railway platform status",
    "platform regions":                "List available deploy regions",
    "platform me":                     "Show current user info + workspaces",
    # --- REPL ---
    "help":                            "Show this help",
    "quit / exit":                     "Exit the REPL",
}


def _run_repl(skin: ReplSkin, token: str | None):
    """Start the interactive REPL loop."""
    skin.print_banner()

    if not token:
        token = os.environ.get("RAILWAY_TOKEN")

    if not token:
        skin.warning(
            "No token found. Set RAILWAY_TOKEN or pass --token before running commands."
        )

    session = skin.create_prompt_session()

    while True:
        try:
            raw = skin.get_input(session, context="railway")
        except (EOFError, KeyboardInterrupt):
            skin.print_goodbye()
            break

        line = raw.strip()
        if not line:
            continue
        if line in ("quit", "exit", "q"):
            skin.print_goodbye()
            break
        if line in ("help", "?"):
            skin.help(_REPL_HELP)
            continue

        # Re-use click's own parser by constructing argv and invoking main.
        import shlex

        argv = shlex.split(line)

        # Inject --token if we have one and the user hasn't provided it.
        if token and "--token" not in argv:
            argv = ["--token", token] + argv

        try:
            # standalone_mode=False so Click doesn't call sys.exit on success.
            main.main(args=argv, standalone_mode=False, obj={})
        except click.exceptions.UsageError as exc:
            skin.error(str(exc))
        except click.exceptions.Abort:
            pass
        except SystemExit as exc:
            # A non-zero exit from a sub-command — already printed an error.
            if exc.code and exc.code != 0:
                pass
        except Exception as exc:  # noqa: BLE001
            skin.error(f"Unexpected error: {exc}")
