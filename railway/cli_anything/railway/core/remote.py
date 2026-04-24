"""Remote & local execution commands for cli-anything-railway.

- ``run <cmd>``   : run a local command with the service's env vars injected
- ``shell``       : open a local subshell with env vars
- ``exec <cmd>``  : run a command inside the deployed container (via WS relay)
- ``ssh``         : open an interactive shell inside the deployed container
- ``ssh keys``    : manage SSH public keys registered with Railway
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import click

from cli_anything.railway.utils.railway_backend import RailwayBackend, RailwayAPIError
from cli_anything.railway.utils import railway_relay


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_service_id(
    backend: RailwayBackend,
    project_id: str,
    service_hint: str | None,
) -> str | None:
    """Accept a service id or name; resolve to id. Returns None if ambiguous."""
    if not service_hint:
        return None
    try:
        services = backend.services_list(project_id)
    except RailwayAPIError:
        return service_hint  # assume caller passed a raw id
    for s in services:
        if s.get("id") == service_hint or s.get("name") == service_hint:
            return s.get("id")
    return service_hint  # fall through, let the API reject it


def _latest_deployment_id(
    backend: RailwayBackend,
    service_id: str,
    environment_id: str,
) -> str | None:
    deps = backend.deployments_list(service_id, environment_id)
    return deps[0].get("id") if deps else None


def _resolved_env(
    backend: RailwayBackend,
    project_id: str,
    environment_id: str,
    service_id: str,
) -> dict[str, str]:
    variables = backend.variables_for_deployment(
        project_id, environment_id, service_id
    )
    if not isinstance(variables, dict):
        return {}
    return {str(k): str(v) for k, v in variables.items()}


# ---------------------------------------------------------------------------
# `run` — local command with injected env
# ---------------------------------------------------------------------------

@click.command("run", context_settings={"ignore_unknown_options": True})
@click.option("--service", "-s", "service_hint", default=None, help="Service ID or name.")
@click.option("--project", "-p", "project_id", default=None, help="Project ID override.")
@click.option("--env-id", "environment_id", default=None, help="Environment ID override.")
@click.option(
    "--extra-env", "extra_env", multiple=True,
    help="Extra KEY=VALUE to append (repeatable).",
)
@click.option("--inherit/--no-inherit", default=True, help="Inherit local env (default: yes).")
@click.option("--print-env", is_flag=True, help="Just print the resolved env and exit.")
@click.argument("args", nargs=-1, required=False)
@click.pass_context
def run_command(
    ctx: click.Context,
    service_hint: str | None,
    project_id: str | None,
    environment_id: str | None,
    extra_env: tuple,
    inherit: bool,
    print_env: bool,
    args: tuple,
):
    """Run a local command with the service's Railway variables injected."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]

    # Required IDs: pull from ctx if not supplied
    proj = project_id or ctx.obj.get("project_id")
    env_id = environment_id or ctx.obj.get("environment_id")
    svc = _resolve_service_id(backend, proj, service_hint) if proj else service_hint

    missing = [n for n, v in (("project", proj), ("environment", env_id), ("service", svc)) if not v]
    if missing and not print_env:
        skin.error(
            f"Missing: {', '.join(missing)}. Pass --project/--env-id/--service or "
            f"set them in the CLI context."
        )
        sys.exit(2)

    try:
        env_dict = _resolved_env(backend, proj, env_id, svc) if (proj and env_id and svc) else {}
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    for pair in extra_env:
        if "=" not in pair:
            skin.error(f"--extra-env expects KEY=VALUE, got: {pair!r}")
            sys.exit(2)
        k, v = pair.split("=", 1)
        env_dict[k] = v

    if print_env:
        for k, v in sorted(env_dict.items()):
            click.echo(f"{k}={v}")
        return

    if not args:
        skin.error("No command to run. Usage: railway run -- <cmd> [args...]")
        sys.exit(2)

    final_env = dict(os.environ) if inherit else {}
    final_env.update(env_dict)

    # os.execvpe would replace the current process, but we want to return the
    # exit code cleanly from within the Click runner.
    try:
        result = subprocess.run(list(args), env=final_env)
    except FileNotFoundError:
        skin.error(f"Command not found: {args[0]}")
        sys.exit(127)
    except KeyboardInterrupt:
        sys.exit(130)
    sys.exit(result.returncode)


# ---------------------------------------------------------------------------
# `shell` — local subshell with injected env
# ---------------------------------------------------------------------------

@click.command("shell")
@click.option("--service", "-s", "service_hint", default=None, help="Service ID or name.")
@click.option("--project", "-p", "project_id", default=None)
@click.option("--env-id", "environment_id", default=None)
@click.option("--silent", is_flag=True, help="Suppress the banner.")
@click.pass_context
def shell_command(
    ctx: click.Context,
    service_hint: str | None,
    project_id: str | None,
    environment_id: str | None,
    silent: bool,
):
    """Open a local subshell with the service's Railway variables available."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]

    proj = project_id or ctx.obj.get("project_id")
    env_id = environment_id or ctx.obj.get("environment_id")
    svc = _resolve_service_id(backend, proj, service_hint) if proj else service_hint

    missing = [n for n, v in (("project", proj), ("environment", env_id), ("service", svc)) if not v]
    if missing:
        skin.error(
            f"Missing: {', '.join(missing)}. Pass --project/--env-id/--service."
        )
        sys.exit(2)

    try:
        env_dict = _resolved_env(backend, proj, env_id, svc)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    shell = os.environ.get("SHELL", "/bin/bash")
    final_env = dict(os.environ)
    final_env.update(env_dict)
    final_env["IN_RAILWAY_SHELL"] = "true"

    if not silent:
        skin.info(f"Entering subshell with {len(env_dict)} Railway variables. Type 'exit' to leave.")

    try:
        result = subprocess.run([shell], env=final_env)
    except KeyboardInterrupt:
        sys.exit(130)

    if not silent:
        skin.info("Exited subshell — Railway variables no longer in scope.")
    sys.exit(result.returncode)


# ---------------------------------------------------------------------------
# `exec` — remote one-shot command via WS relay
# ---------------------------------------------------------------------------

@click.command("exec", context_settings={"ignore_unknown_options": True})
@click.option("--service", "-s", "service_hint", required=True, help="Service ID or name.")
@click.option("--project", "-p", "project_id", default=None)
@click.option("--env-id", "environment_id", default=None)
@click.option("--deployment-instance", "deployment_instance_id", default=None,
              help="Target a specific deployment instance (replica).")
@click.argument("cmd_args", nargs=-1, required=True)
@click.pass_context
def exec_command(
    ctx: click.Context,
    service_hint: str,
    project_id: str | None,
    environment_id: str | None,
    deployment_instance_id: str | None,
    cmd_args: tuple,
):
    """Run a command inside the deployed container and print its output."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]

    if not railway_relay.ws_available():
        skin.error("websocket-client not installed. Run: pip install websocket-client")
        sys.exit(1)

    proj = project_id or ctx.obj.get("project_id")
    env_id = environment_id or ctx.obj.get("environment_id")
    svc = _resolve_service_id(backend, proj, service_hint)

    missing = [n for n, v in (("project", proj), ("environment", env_id)) if not v]
    if missing:
        skin.error(f"Missing: {', '.join(missing)}.")
        sys.exit(2)

    cmd = cmd_args[0]
    args = list(cmd_args[1:])

    try:
        code = railway_relay.exec_command(
            token=backend._token,
            project_id=proj,
            service_id=svc,
            environment_id=env_id,
            command=cmd,
            args=args,
            deployment_instance_id=deployment_instance_id,
        )
    except railway_relay.RelayError as exc:
        skin.error(f"Exec failed: {exc}")
        sys.exit(1)
    sys.exit(code)


# ---------------------------------------------------------------------------
# `ssh` — interactive remote shell via WS relay (+ `ssh keys` subgroup)
# ---------------------------------------------------------------------------

@click.group("ssh", invoke_without_command=True)
@click.option("--service", "-s", "service_hint", default=None, help="Service ID or name.")
@click.option("--project", "-p", "project_id", default=None)
@click.option("--env-id", "environment_id", default=None)
@click.option("--deployment-instance", "deployment_instance_id", default=None)
@click.option("--shell-cmd", "shell_cmd", default=None, help="Shell to launch (default: server default).")
@click.pass_context
def ssh_group(
    ctx: click.Context,
    service_hint: str | None,
    project_id: str | None,
    environment_id: str | None,
    deployment_instance_id: str | None,
    shell_cmd: str | None,
):
    """Interactive shell inside the deployed container (or manage SSH keys)."""
    # If a subcommand was invoked (e.g. `ssh keys list`), defer to it.
    if ctx.invoked_subcommand is not None:
        return

    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]

    if not railway_relay.ws_available():
        skin.error("websocket-client not installed. Run: pip install websocket-client")
        sys.exit(1)

    proj = project_id or ctx.obj.get("project_id")
    env_id = environment_id or ctx.obj.get("environment_id")
    svc = _resolve_service_id(backend, proj, service_hint) if service_hint else None

    missing = [n for n, v in (("project", proj), ("environment", env_id), ("service", svc)) if not v]
    if missing:
        skin.error(f"Missing: {', '.join(missing)}. Pass --project/--env-id/--service.")
        sys.exit(2)

    if not sys.stdin.isatty():
        skin.error("ssh requires an interactive terminal (stdin is not a TTY).")
        sys.exit(1)

    try:
        code = railway_relay.interactive_shell(
            token=backend._token,
            project_id=proj,
            service_id=svc,
            environment_id=env_id,
            shell=shell_cmd,
            deployment_instance_id=deployment_instance_id,
        )
    except railway_relay.RelayError as exc:
        skin.error(f"SSH failed: {exc}")
        sys.exit(1)
    sys.exit(code)


# ---- ssh keys subgroup -----------------------------------------------------

@ssh_group.group("keys")
def ssh_keys_group():
    """Manage SSH public keys registered with Railway."""


@ssh_keys_group.command("list")
@click.option("--json", "as_json", is_flag=True)
@click.pass_context
def ssh_keys_list(ctx: click.Context, as_json: bool):
    """List SSH keys registered on your account."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        keys = backend.ssh_keys_list()
    except RailwayAPIError as exc:
        skin.error(str(exc)); sys.exit(1)
    if as_json:
        click.echo(json.dumps(keys, indent=2)); return
    if not keys:
        skin.info("No SSH keys registered."); return
    skin.section("Registered SSH keys")
    skin.table(
        ["ID", "Name", "Fingerprint", "Created"],
        [
            [
                k.get("id", "")[:36],
                k.get("name", ""),
                k.get("fingerprint", ""),
                (k.get("createdAt") or "")[:19],
            ]
            for k in keys
        ],
    )


@ssh_keys_group.command("add")
@click.option("--key", "key_path", default=None,
              help="Path to a public key file (e.g. ~/.ssh/id_ed25519.pub). "
                   "Defaults to auto-detecting the first *.pub in ~/.ssh/.")
@click.option("--name", default=None, help="Label (defaults to filename).")
@click.option("--json", "as_json", is_flag=True)
@click.pass_context
def ssh_keys_add(ctx: click.Context, key_path: str | None, name: str | None, as_json: bool):
    """Register a public SSH key with Railway."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]

    if not key_path:
        ssh_dir = Path.home() / ".ssh"
        candidates = sorted(ssh_dir.glob("*.pub")) if ssh_dir.exists() else []
        if not candidates:
            skin.error("No public keys found in ~/.ssh/. Pass --key <path>.")
            sys.exit(2)
        key_path = str(candidates[0])

    p = Path(key_path).expanduser()
    if not p.exists():
        skin.error(f"File not found: {p}")
        sys.exit(2)
    content = p.read_text().strip()
    if not content.startswith(("ssh-", "ecdsa-", "sk-")):
        skin.error(f"{p} does not look like a public key.")
        sys.exit(2)

    label = name or p.stem
    try:
        result = backend.ssh_key_create(label, content)
    except RailwayAPIError as exc:
        skin.error(str(exc)); sys.exit(1)
    if as_json:
        click.echo(json.dumps(result, indent=2))
    else:
        skin.success(f"Registered '{label}' ({result.get('fingerprint','')}).")


@ssh_keys_group.command("remove")
@click.argument("key_id")
@click.option("--json", "as_json", is_flag=True)
@click.pass_context
def ssh_keys_remove(ctx: click.Context, key_id: str, as_json: bool):
    """Remove a registered SSH key by ID."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        ok = backend.ssh_key_delete(key_id)
    except RailwayAPIError as exc:
        skin.error(str(exc)); sys.exit(1)
    if as_json:
        click.echo(json.dumps({"deleted": ok}))
    elif ok:
        skin.success(f"Deleted SSH key {key_id}.")
    else:
        skin.error("Delete returned false.")
        sys.exit(1)


@ssh_keys_group.command("github")
@click.option("--json", "as_json", is_flag=True)
@click.pass_context
def ssh_keys_github(ctx: click.Context, as_json: bool):
    """List SSH keys from your linked GitHub account."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        keys = backend.github_ssh_keys()
    except RailwayAPIError as exc:
        skin.error(str(exc)); sys.exit(1)
    if as_json:
        click.echo(json.dumps(keys, indent=2)); return
    if not keys:
        skin.info("No GitHub SSH keys found."); return
    skin.section("GitHub SSH keys")
    skin.table(
        ["ID", "Title", "Key prefix"],
        [[str(k.get("id", "")), k.get("title", ""), (k.get("key") or "")[:40] + "…"] for k in keys],
    )


__all__ = [
    "run_command",
    "shell_command",
    "exec_command",
    "ssh_group",
]
