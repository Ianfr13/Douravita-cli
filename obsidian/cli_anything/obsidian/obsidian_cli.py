#!/usr/bin/env python3
"""Obsidian CLI — A command-line interface for your Obsidian vault via Local REST API.

This CLI provides full access to the Obsidian Local REST API plugin for reading,
writing, searching, and managing notes directly from the terminal or AI agents.

Usage:
    # One-shot commands
    cli-anything-obsidian status
    cli-anything-obsidian vault list
    cli-anything-obsidian vault get "Notes/My Note.md"
    cli-anything-obsidian --json search "meeting notes"

    # Interactive REPL
    cli-anything-obsidian

Prerequisites:
    - Obsidian desktop app running
    - obsidian-local-rest-api plugin installed and enabled
    - OBSIDIAN_API_KEY environment variable set (or use --api-key)
"""

import sys
import os
import json
import functools
import click

from cli_anything.obsidian.utils.obsidian_backend import DEFAULT_BASE_URL
from cli_anything.obsidian.core import (
    server as server_mod,
    active as active_mod,
    vault as vault_mod,
    periodic as periodic_mod,
    search as search_mod,
    commands as commands_mod,
    tags as tags_mod,
    ui as ui_mod,
)

# ── Global state ──────────────────────────────────────────────────────────────
_json_output = False
_repl_mode = False
_host = DEFAULT_BASE_URL
_api_key: str | None = None


# ── Output helpers ────────────────────────────────────────────────────────────

def output(data, message: str = ""):
    """Print data in human-readable or JSON format.

    Args:
        data: Data to display (dict, list, or string).
        message: Optional human-readable prefix message.
    """
    if _json_output:
        click.echo(json.dumps(data, indent=2, default=str))
    else:
        if message:
            click.echo(message)
        if isinstance(data, dict):
            _print_dict(data)
        elif isinstance(data, list):
            _print_list(data)
        else:
            click.echo(str(data))


def _print_dict(d: dict, indent: int = 0):
    """Recursively print a dict as indented key: value lines."""
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
    """Recursively print a list with index markers."""
    prefix = "  " * indent
    for i, item in enumerate(items):
        if isinstance(item, dict):
            click.echo(f"{prefix}[{i}]")
            _print_dict(item, indent + 1)
        else:
            click.echo(f"{prefix}- {item}")


def handle_error(func):
    """Decorator for consistent error handling across all CLI commands."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except RuntimeError as e:
            if _json_output:
                click.echo(json.dumps({"error": str(e), "type": "runtime_error"}))
            else:
                click.echo(f"Error: {e}", err=True)
            if not _repl_mode:
                sys.exit(1)
        except (ValueError, IndexError) as e:
            if _json_output:
                click.echo(json.dumps({"error": str(e), "type": type(e).__name__}))
            else:
                click.echo(f"Error: {e}", err=True)
            if not _repl_mode:
                sys.exit(1)
    return wrapper


# ── Main CLI Group ────────────────────────────────────────────────────────────

@click.group(invoke_without_command=True)
@click.option("--json", "use_json", is_flag=True, help="Output as JSON (for agents)")
@click.option("--host", type=str, default=None,
              help=f"Obsidian REST API URL (default: {DEFAULT_BASE_URL})")
@click.option("--api-key", "api_key", type=str, default=None, envvar="OBSIDIAN_API_KEY",
              help="Bearer token (or set OBSIDIAN_API_KEY env var)")
@click.pass_context
def cli(ctx, use_json, host, api_key):
    """Obsidian CLI — Read and write your vault via the Local REST API.

    Run without a subcommand to enter interactive REPL mode.

    Authentication:
        Set OBSIDIAN_API_KEY environment variable or use --api-key.
        Your key is in Obsidian Settings → Local REST API.
    """
    global _json_output, _host, _api_key
    _json_output = use_json
    if host:
        _host = host
    if api_key:
        _api_key = api_key

    if ctx.invoked_subcommand is None:
        ctx.invoke(repl)


# ── Status Command ────────────────────────────────────────────────────────────

@cli.command("status")
@handle_error
def cmd_status():
    """Check if Obsidian REST API plugin is running (no auth required)."""
    result = server_mod.status(_host)
    if _json_output:
        output(result)
    else:
        ok = result.get("ok", False)
        svc = result.get("service", "Obsidian Local REST API")
        auth = result.get("authenticated", False)
        versions = result.get("versions", {})
        status_str = "✓ running" if ok else "✗ not responding"
        click.echo(f"Status:        {status_str}")
        click.echo(f"Service:       {svc}")
        click.echo(f"Authenticated: {auth}")
        if versions:
            for k, v in versions.items():
                click.echo(f"Version [{k}]: {v}")


# ── Active File Commands ──────────────────────────────────────────────────────

@cli.group("active")
def active():
    """Operations on the currently open file in Obsidian."""
    pass


@active.command("get")
@click.option("--format", "fmt",
              type=click.Choice(["markdown", "json", "map"]),
              default="markdown", show_default=True,
              help="Output format: raw markdown, parsed JSON note, or document map.")
@handle_error
def active_get(fmt):
    """Get the content of the currently active (open) note."""
    result = active_mod.get(_host, _api_key, fmt=fmt)
    if _json_output or fmt != "markdown":
        output(result)
    else:
        # Print raw markdown content directly
        content = result.get("content", result) if isinstance(result, dict) else result
        click.echo(content)


@active.command("append")
@click.argument("content")
@handle_error
def active_append(content):
    """Append CONTENT to the active file.

    CONTENT is the markdown text to append.
    Use '-' to read from stdin: echo '# New Section' | cli-anything-obsidian active append -
    """
    if content == "-":
        content = sys.stdin.read()
    result = active_mod.append(_host, _api_key, content)
    output(result, "Appended to active file.")


@active.command("put")
@click.argument("content")
@handle_error
def active_put(content):
    """Replace the entire active file with CONTENT.

    CONTENT is the new markdown content.
    Use '-' to read from stdin.
    """
    if content == "-":
        content = sys.stdin.read()
    result = active_mod.put(_host, _api_key, content)
    output(result, "Active file replaced.")


@active.command("patch")
@click.argument("content")
@click.option("--op", "operation",
              type=click.Choice(["append", "prepend", "replace"]),
              required=True, help="Patch operation type.")
@click.option("--type", "target_type",
              type=click.Choice(["heading", "block", "frontmatter"]),
              required=True, help="Target type to patch.")
@click.option("--target", required=True,
              help="Heading name, block ref (^abc123), or frontmatter key.")
@click.option("--delimiter", default="::", show_default=True,
              help="Separator for nested headings (e.g. 'Section::Subsection').")
@click.option("--trim/--no-trim", default=False,
              help="Trim whitespace around the target.")
@click.option("--create/--no-create", default=False,
              help="Create the target section if it does not exist.")
@handle_error
def active_patch(content, operation, target_type, target, delimiter, trim, create):
    """Partially update the active file at a specific HEADING, BLOCK, or FRONTMATTER key.

    CONTENT is the text to insert. Use '-' to read from stdin.

    Examples:
        # Append under a heading
        cli-anything-obsidian active patch "- new item" --op append --type heading --target "Tasks"

        # Replace a frontmatter field
        cli-anything-obsidian active patch "done" --op replace --type frontmatter --target "status"

        # Prepend to a block
        cli-anything-obsidian active patch "note: " --op prepend --type block --target "^abc123"
    """
    if content == "-":
        content = sys.stdin.read()
    result = active_mod.patch(
        _host, _api_key, content,
        operation=operation, target_type=target_type, target=target,
        delimiter=delimiter, trim_whitespace=trim, create_if_missing=create,
    )
    output(result, f"Active file patched ({operation} at {target_type}: {target}).")


@active.command("delete")
@click.confirmation_option(prompt="Delete the active file?")
@handle_error
def active_delete():
    """Delete the currently active file from the vault."""
    result = active_mod.delete(_host, _api_key)
    output(result, "Active file deleted.")


# ── Vault Commands ────────────────────────────────────────────────────────────

@cli.group("vault")
def vault():
    """Read, write, and manage files in your vault."""
    pass


@vault.command("list")
@click.argument("path", default="")
@handle_error
def vault_list(path):
    """List vault root or a specific directory.

    PATH is the directory path relative to vault root (optional).
    Trailing slash is not required.

    Examples:
        cli-anything-obsidian vault list
        cli-anything-obsidian vault list "Projects"
        cli-anything-obsidian vault list "Daily Notes/2026"
    """
    result = vault_mod.list_dir(_host, _api_key, path)
    if _json_output:
        output(result)
    else:
        files = result.get("files", result) if isinstance(result, dict) else result
        if not files:
            click.echo("(empty directory)")
            return
        for f in files:
            click.echo(f"  {f}")


@vault.command("get")
@click.argument("file")
@click.option("--format", "fmt",
              type=click.Choice(["markdown", "json", "map"]),
              default="markdown", show_default=True,
              help="Output format: raw markdown, parsed JSON note, or document map.")
@handle_error
def vault_get(file, fmt):
    """Get the content of a vault file.

    FILE is the path relative to vault root (e.g., 'Notes/My Note.md').

    Examples:
        cli-anything-obsidian vault get "Notes/My Note.md"
        cli-anything-obsidian --json vault get "Notes/My Note.md" --format json
    """
    result = vault_mod.get(_host, _api_key, file, fmt=fmt)
    if _json_output or fmt != "markdown":
        output(result)
    else:
        content = result.get("content", result) if isinstance(result, dict) else result
        click.echo(content)


@vault.command("append")
@click.argument("file")
@click.argument("content")
@handle_error
def vault_append(file, content):
    """Append CONTENT to a vault FILE (creates the file if it doesn't exist).

    FILE: path relative to vault root.
    CONTENT: markdown text to append. Use '-' to read from stdin.

    Example:
        cli-anything-obsidian vault append "Notes/Log.md" "## 2026-03-22\\n- Meeting done"
    """
    if content == "-":
        content = sys.stdin.read()
    result = vault_mod.append(_host, _api_key, file, content)
    output(result, f"Appended to: {file}")


@vault.command("put")
@click.argument("file")
@click.argument("content")
@handle_error
def vault_put(file, content):
    """Create or replace a vault FILE with CONTENT.

    FILE: path relative to vault root.
    CONTENT: full file content. Use '-' to read from stdin.

    Example:
        cli-anything-obsidian vault put "Notes/New Note.md" "# Title\\n\\nContent here."
    """
    if content == "-":
        content = sys.stdin.read()
    result = vault_mod.put(_host, _api_key, file, content)
    output(result, f"Written: {file}")


@vault.command("patch")
@click.argument("file")
@click.argument("content")
@click.option("--op", "operation",
              type=click.Choice(["append", "prepend", "replace"]),
              required=True, help="Patch operation type.")
@click.option("--type", "target_type",
              type=click.Choice(["heading", "block", "frontmatter"]),
              required=True, help="Target type to patch.")
@click.option("--target", required=True,
              help="Heading name, block ref (^abc123), or frontmatter key.")
@click.option("--delimiter", default="::", show_default=True,
              help="Separator for nested headings.")
@click.option("--trim/--no-trim", default=False,
              help="Trim whitespace around the target.")
@click.option("--create/--no-create", default=False,
              help="Create the target section if it does not exist.")
@handle_error
def vault_patch(file, content, operation, target_type, target,
                delimiter, trim, create):
    """Partially update a vault FILE at a specific section.

    FILE: path relative to vault root.
    CONTENT: text to insert. Use '-' to read from stdin.

    Examples:
        # Add a task under the 'Tasks' heading
        cli-anything-obsidian vault patch "Notes/Project.md" "- [ ] Review PR" \\
          --op append --type heading --target "Tasks"

        # Update a frontmatter field
        cli-anything-obsidian vault patch "Notes/Project.md" "in-progress" \\
          --op replace --type frontmatter --target "status"
    """
    if content == "-":
        content = sys.stdin.read()
    result = vault_mod.patch(
        _host, _api_key, file, content,
        operation=operation, target_type=target_type, target=target,
        delimiter=delimiter, trim_whitespace=trim, create_if_missing=create,
    )
    output(result, f"Patched: {file} ({operation} at {target_type}: {target})")


@vault.command("delete")
@click.argument("file")
@click.confirmation_option(prompt="Delete this file from the vault?")
@handle_error
def vault_delete(file):
    """Delete a vault FILE.

    FILE: path relative to vault root.
    """
    result = vault_mod.delete(_host, _api_key, file)
    output(result, f"Deleted: {file}")


# ── Periodic Note Commands ────────────────────────────────────────────────────

@cli.group("periodic")
def periodic():
    """Read and write periodic notes (daily, weekly, monthly, quarterly, yearly)."""
    pass


@periodic.command("get")
@click.argument("period",
                type=click.Choice(["daily", "weekly", "monthly", "quarterly", "yearly"]))
@click.option("--date", default=None, metavar="YYYY-MM-DD",
              help="Specific date (default: current period).")
@click.option("--format", "fmt",
              type=click.Choice(["markdown", "json", "map"]),
              default="markdown", show_default=True)
@handle_error
def periodic_get(period, date, fmt):
    """Get a periodic note's content.

    PERIOD: daily | weekly | monthly | quarterly | yearly

    Examples:
        cli-anything-obsidian periodic get daily
        cli-anything-obsidian periodic get daily --date 2026-03-01
        cli-anything-obsidian periodic get weekly --format json
    """
    result = periodic_mod.get(_host, _api_key, period, date=date, fmt=fmt)
    if _json_output or fmt != "markdown":
        output(result)
    else:
        content = result.get("content", result) if isinstance(result, dict) else result
        click.echo(content)


@periodic.command("append")
@click.argument("period",
                type=click.Choice(["daily", "weekly", "monthly", "quarterly", "yearly"]))
@click.argument("content")
@click.option("--date", default=None, metavar="YYYY-MM-DD",
              help="Specific date (default: current period).")
@handle_error
def periodic_append(period, content, date):
    """Append CONTENT to a periodic note (creates it if it doesn't exist).

    PERIOD: daily | weekly | monthly | quarterly | yearly
    CONTENT: markdown text. Use '-' to read from stdin.

    Example:
        cli-anything-obsidian periodic append daily "- [x] Reviewed PRs"
    """
    if content == "-":
        content = sys.stdin.read()
    result = periodic_mod.append(_host, _api_key, period, content, date=date)
    label = f"{period} ({date})" if date else period
    output(result, f"Appended to {label} note.")


@periodic.command("put")
@click.argument("period",
                type=click.Choice(["daily", "weekly", "monthly", "quarterly", "yearly"]))
@click.argument("content")
@click.option("--date", default=None, metavar="YYYY-MM-DD",
              help="Specific date (default: current period).")
@handle_error
def periodic_put(period, content, date):
    """Replace the content of a periodic note.

    PERIOD: daily | weekly | monthly | quarterly | yearly
    CONTENT: full new content. Use '-' to read from stdin.
    """
    if content == "-":
        content = sys.stdin.read()
    result = periodic_mod.put(_host, _api_key, period, content, date=date)
    label = f"{period} ({date})" if date else period
    output(result, f"{label} note replaced.")


@periodic.command("patch")
@click.argument("period",
                type=click.Choice(["daily", "weekly", "monthly", "quarterly", "yearly"]))
@click.argument("content")
@click.option("--op", "operation",
              type=click.Choice(["append", "prepend", "replace"]),
              required=True, help="Patch operation type.")
@click.option("--type", "target_type",
              type=click.Choice(["heading", "block", "frontmatter"]),
              required=True, help="Target type to patch.")
@click.option("--target", required=True,
              help="Heading name, block ref, or frontmatter key.")
@click.option("--date", default=None, metavar="YYYY-MM-DD",
              help="Specific date (default: current period).")
@click.option("--delimiter", default="::", show_default=True,
              help="Separator for nested headings (e.g. 'Section::Subsection').")
@click.option("--trim/--no-trim", default=False,
              help="Trim whitespace around the target.")
@click.option("--create/--no-create", default=False,
              help="Create the target section if it does not exist.")
@handle_error
def periodic_patch(period, content, operation, target_type, target, date,
                   delimiter, trim, create):
    """Partially update a periodic note.

    PERIOD: daily | weekly | monthly | quarterly | yearly
    CONTENT: text to insert. Use '-' to read from stdin.
    """
    if content == "-":
        content = sys.stdin.read()
    result = periodic_mod.patch(
        _host, _api_key, period, content,
        operation=operation, target_type=target_type, target=target,
        date=date, delimiter=delimiter, trim_whitespace=trim,
        create_if_missing=create,
    )
    label = f"{period} ({date})" if date else period
    output(result, f"Patched {label} note ({operation} at {target_type}: {target}).")


@periodic.command("delete")
@click.argument("period",
                type=click.Choice(["daily", "weekly", "monthly", "quarterly", "yearly"]))
@click.option("--date", default=None, metavar="YYYY-MM-DD",
              help="Specific date (default: current period).")
@click.confirmation_option(prompt="Delete this periodic note?")
@handle_error
def periodic_delete(period, date):
    """Delete a periodic note."""
    result = periodic_mod.delete(_host, _api_key, period, date=date)
    label = f"{period} ({date})" if date else period
    output(result, f"Deleted {label} note.")


# ── Search Commands ───────────────────────────────────────────────────────────

@cli.group("search")
def search():
    """Search your vault with simple text, Dataview DQL, or JsonLogic."""
    pass


@search.command("simple")
@click.argument("query")
@click.option("--context", "context_length", type=int, default=100, show_default=True,
              help="Characters of context around each match.")
@handle_error
def search_simple(query, context_length):
    """Simple fuzzy full-text search across the vault.

    QUERY: search term.

    Example:
        cli-anything-obsidian search simple "meeting notes"
        cli-anything-obsidian --json search simple "project" --context 200
    """
    results = search_mod.simple(_host, _api_key, query, context_length=context_length)
    if _json_output:
        output(results)
    else:
        if not results:
            click.echo("No results found.")
            return
        click.echo(f"Found {len(results)} file(s):\n")
        for item in results:
            score = item.get("score", 0)
            filename = item.get("filename", "")
            click.echo(f"  [{score:.3f}] {filename}")
            for m in item.get("matches", []):
                ctx = m.get("context", "").replace("\n", " ").strip()
                click.echo(f"    … {ctx} …")
            click.echo()


@search.command("dql")
@click.argument("query")
@handle_error
def search_dql(query):
    """Search with a Dataview DQL TABLE query.

    Requires the Dataview plugin to be installed in Obsidian.

    QUERY: a Dataview DQL TABLE query string.

    Example:
        cli-anything-obsidian search dql 'TABLE file.name FROM "Projects"'
        cli-anything-obsidian --json search dql 'TABLE status FROM "Tasks" WHERE status = "open"'
    """
    results = search_mod.dql(_host, _api_key, query)
    if _json_output:
        output(results)
    else:
        if not results:
            click.echo("No results.")
            return
        click.echo(f"Found {len(results)} result(s):")
        for item in results:
            fn = item.get("filename", "")
            res = item.get("result", "")
            click.echo(f"  {fn}: {res}")


@search.command("jsonlogic")
@click.argument("logic")
@handle_error
def search_jsonlogic(logic):
    """Search with a JsonLogic expression.

    LOGIC: JSON string with JsonLogic operators.
    Supports: standard JsonLogic + 'glob' (file patterns) + 'regexp'.

    Example:
        cli-anything-obsidian search jsonlogic '{"glob": ["*.md", {"var": "path"}]}'
        cli-anything-obsidian --json search jsonlogic '{"==": [{"var": "frontmatter.status"}, "done"]}'
    """
    results = search_mod.jsonlogic(_host, _api_key, logic)
    if _json_output:
        output(results)
    else:
        if not results:
            click.echo("No results.")
            return
        click.echo(f"Found {len(results)} result(s):")
        for item in results:
            fn = item.get("filename", "")
            res = item.get("result", "")
            click.echo(f"  {fn}: {res}")


# ── Commands Group ────────────────────────────────────────────────────────────

@cli.group("commands")
def commands():
    """List and execute Obsidian commands."""
    pass


@commands.command("list")
@click.option("--filter", "filter_str", default="", help="Filter commands by name substring.")
@handle_error
def commands_list(filter_str):
    """List all available Obsidian commands.

    Example:
        cli-anything-obsidian commands list
        cli-anything-obsidian commands list --filter "editor"
        cli-anything-obsidian --json commands list
    """
    cmds = commands_mod.list_commands(_host, _api_key)
    if filter_str:
        cmds = [c for c in cmds if filter_str.lower() in c.get("name", "").lower()
                or filter_str.lower() in c.get("id", "").lower()]
    if _json_output:
        output(cmds)
    else:
        if not cmds:
            click.echo("No commands found.")
            return
        click.echo(f"{'ID':<50} {'NAME'}")
        click.echo("─" * 80)
        for c in cmds:
            cid = c.get("id", "")
            cname = c.get("name", "")
            click.echo(f"{cid:<50} {cname}")


@commands.command("run")
@click.argument("command_id")
@handle_error
def commands_run(command_id):
    """Execute an Obsidian command by its ID.

    COMMAND_ID: the command identifier (e.g., 'editor:toggle-bold').
    Use 'commands list' to see all available IDs.

    Example:
        cli-anything-obsidian commands run "editor:toggle-bold"
        cli-anything-obsidian commands run "obsidian-git:pull"
    """
    result = commands_mod.run_command(_host, _api_key, command_id)
    output(result, f"Command executed: {command_id}")


# ── Tags Command ──────────────────────────────────────────────────────────────

@cli.command("tags")
@click.option("--filter", "filter_str", default="", help="Filter tags by name substring.")
@click.option("--min-count", type=int, default=0, show_default=True,
              help="Show only tags with at least this many uses.")
@handle_error
def cmd_tags(filter_str, min_count):
    """List all tags in the vault with usage counts.

    Tags are returned without the '#' prefix.

    Example:
        cli-anything-obsidian tags
        cli-anything-obsidian tags --filter "project" --min-count 2
        cli-anything-obsidian --json tags
    """
    tag_list = tags_mod.list_tags(_host, _api_key)
    if filter_str:
        tag_list = [t for t in tag_list if filter_str.lower() in t.get("name", "").lower()]
    if min_count > 0:
        tag_list = [t for t in tag_list if t.get("count", 0) >= min_count]
    if _json_output:
        output(tag_list)
    else:
        if not tag_list:
            click.echo("No tags found.")
            return
        click.echo(f"{'TAG':<50} {'COUNT'}")
        click.echo("─" * 60)
        for t in tag_list:
            name = t.get("name", "")
            count = t.get("count", 0)
            click.echo(f"  #{name:<48} {count}")


# ── Open Command ──────────────────────────────────────────────────────────────

@cli.command("open")
@click.argument("file")
@click.option("--new-leaf", is_flag=True, help="Open in a new tab/leaf.")
@handle_error
def cmd_open(file, new_leaf):
    """Open a FILE in the Obsidian UI.

    FILE: path relative to vault root.

    Example:
        cli-anything-obsidian open "Notes/My Note.md"
        cli-anything-obsidian open "Projects/Work.md" --new-leaf
    """
    result = ui_mod.open_file(_host, _api_key, file, new_leaf=new_leaf)
    output(result, f"Opened in Obsidian: {file}")


# ── REPL ──────────────────────────────────────────────────────────────────────

@cli.command()
@handle_error
def repl():
    """Start an interactive REPL session for your Obsidian vault."""
    from cli_anything.obsidian.utils.repl_skin import ReplSkin

    global _repl_mode
    _repl_mode = True

    skin = ReplSkin("obsidian", version="1.0.0")
    skin.print_banner()

    pt_session = skin.create_prompt_session()

    _repl_commands = {
        "status":          "Check Obsidian REST API status",
        "active":          "get | append | put | patch | delete",
        "vault":           "list | get | append | put | patch | delete",
        "periodic":        "get | append | put | patch | delete",
        "search":          "simple | dql | jsonlogic",
        "commands":        "list | run",
        "tags":            "List all vault tags with counts",
        "open":            "Open a file in Obsidian UI",
        "help":            "Show this help",
        "quit":            "Exit REPL",
    }

    while True:
        try:
            line = skin.get_input(pt_session, project_name="vault", modified=False)
            if not line:
                continue
            if line.lower() in ("quit", "exit", "q"):
                skin.print_goodbye()
                break
            if line.lower() == "help":
                skin.help(_repl_commands)
                continue

            args = line.split()
            try:
                cli.main(args, standalone_mode=False)
            except SystemExit:
                pass
            except click.exceptions.UsageError as e:
                skin.warning(f"Usage error: {e}")
            except Exception as e:
                skin.error(f"{e}")

        except (EOFError, KeyboardInterrupt):
            skin.print_goodbye()
            break

    _repl_mode = False


# ── Entry Point ───────────────────────────────────────────────────────────────

def main():
    cli()


if __name__ == "__main__":
    main()
