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

Environment variables:
    OBSIDIAN_API_KEY  — Bearer token for authentication
    OBSIDIAN_HOST     — REST API URL (default: https://127.0.0.1:27124)
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
    dataview as dataview_mod,
    templater as templater_mod,
    foldernotes as foldernotes_mod,
    charts as charts_mod,
)

# ── Global state ──────────────────────────────────────────────────────────────
_json_output = False
_repl_mode = False
_host = DEFAULT_BASE_URL
_api_key: str | None = None


# ── Content resolution helper ────────────────────────────────────────────────

def _resolve_content(content: str | None) -> str:
    """Resolve CONTENT argument: explicit value, '-' for stdin, or auto-stdin.

    This fixes bugs where content starting with '-' or '---' was parsed as
    a CLI flag.  Usage patterns:
        vault put FILE "normal content"           # direct
        vault put FILE -                          # explicit stdin
        echo "---\\nfm\\n---" | vault put FILE    # auto-stdin (content=None)
        vault put FILE -- "- [ ] task"            # -- separator

    Args:
        content: Raw content argument from Click (may be None if omitted).

    Returns:
        Resolved content string.

    Raises:
        click.UsageError: If no content is available from any source.
    """
    if content is not None and content != "-":
        return content
    if content == "-" or (content is None and not sys.stdin.isatty()):
        data = sys.stdin.read()
        if not data:
            raise click.UsageError("No content received from stdin.")
        return data
    raise click.UsageError(
        "CONTENT is required. Provide it as an argument, via stdin with '-', "
        "or pipe input.  For content starting with '-', use: -- \"- content\""
    )


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
@click.option("--host", type=str, default=None, envvar="OBSIDIAN_HOST",
              help=f"Obsidian REST API URL (env: OBSIDIAN_HOST, default: {DEFAULT_BASE_URL})")
@click.option("--api-key", "api_key", type=str, default=None, envvar="OBSIDIAN_API_KEY",
              help="Bearer token (or set OBSIDIAN_API_KEY env var)")
@click.pass_context
def cli(ctx, use_json, host, api_key):
    """Obsidian CLI — Read and write your vault via the Local REST API.

    Run without a subcommand to enter interactive REPL mode.

    Authentication:
        Set OBSIDIAN_API_KEY environment variable or use --api-key.
        Your key is in Obsidian Settings → Local REST API.

    Host:
        Set OBSIDIAN_HOST environment variable or use --host.
        Default: https://127.0.0.1:27124
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
    """Check if Obsidian REST API plugin is running.

    Sends API key when available so the 'authenticated' field is accurate.
    """
    result = server_mod.status(_host, api_key=_api_key)
    if _json_output:
        output(result)
    else:
        # API returns {"status": "OK", ...} — NOT {"ok": true}
        status_val = result.get("status", "")
        ok = isinstance(status_val, str) and status_val.upper() == "OK"
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
@click.argument("content", required=False, default=None)
@handle_error
def active_append(content):
    """Append CONTENT to the active file.

    CONTENT: markdown text to append.  Use '-' to read from stdin.
    For content starting with '-', use: -- "- content"

    Examples:
        cli-anything-obsidian active append "New text"
        echo '# New Section' | cli-anything-obsidian active append -
        cli-anything-obsidian active append -- "- [ ] task"
    """
    content = _resolve_content(content)
    result = active_mod.append(_host, _api_key, content)
    output(result, "Appended to active file.")


@active.command("put")
@click.argument("content", required=False, default=None)
@handle_error
def active_put(content):
    """Replace the entire active file with CONTENT.

    CONTENT: new markdown content.  Use '-' to read from stdin.
    For content starting with '-', use: -- "- content"
    """
    content = _resolve_content(content)
    result = active_mod.put(_host, _api_key, content)
    output(result, "Active file replaced.")


@active.command("patch")
@click.argument("content", required=False, default=None)
@click.option("--op", "operation",
              type=click.Choice(["append", "prepend", "replace"]),
              required=True, help="Patch operation type.")
@click.option("--type", "target_type",
              type=click.Choice(["heading", "block", "frontmatter"]),
              required=True, help="Target type to patch.")
@click.option("--target", required=True,
              help="Heading name, block ref (^abc123), or frontmatter key. "
                   "For sub-headings use 'Parent::Child' delimiter.")
@click.option("--delimiter", default="::", show_default=True,
              help="Separator for nested headings (e.g. 'Section::Subsection').")
@click.option("--trim/--no-trim", default=False,
              help="Trim whitespace around the target.")
@click.option("--create/--no-create", default=False,
              help="Create the target section if it does not exist.")
@handle_error
def active_patch(content, operation, target_type, target, delimiter, trim, create):
    """Partially update the active file at a specific HEADING, BLOCK, or FRONTMATTER key.

    CONTENT: text to insert. Use '-' to read from stdin.
    For content starting with '-', use: -- "- content"

    Examples:
        cli-anything-obsidian active patch --op append --type heading --target "Tasks" -- "- new item"
        cli-anything-obsidian active patch "done" --op replace --type frontmatter --target "status"
        echo "note: " | cli-anything-obsidian active patch --op prepend --type block --target "^abc123"
    """
    content = _resolve_content(content)
    if operation == "append" and not content.startswith("\n"):
        content = "\n" + content
    result = active_mod.patch(
        _host, _api_key, content,
        operation=operation, target_type=target_type, target=target,
        delimiter=delimiter, trim_whitespace=trim, create_if_missing=create,
    )
    output(result, f"Active file patched ({operation} at {target_type}: {target}).")


@active.command("delete")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt.")
@handle_error
def active_delete(yes):
    """Delete the currently active file from the vault.

    Use --yes / -y to skip confirmation (required in non-interactive environments).
    """
    if not yes:
        if not sys.stdin.isatty():
            raise click.UsageError(
                "Cannot prompt for confirmation in non-interactive mode. Use --yes."
            )
        click.confirm("Delete the active file?", abort=True)
    result = active_mod.delete(_host, _api_key)
    output(result, "Active file deleted.")


# ── Vault Commands ────────────────────────────────────────────────────────────

@cli.group("vault")
def vault():
    """Read, write, and manage files in your vault."""
    pass


@vault.command("list")
@click.argument("path", default="")
@click.option("--recursive", "-r", is_flag=True,
              help="Recursively list all files in subdirectories.")
@handle_error
def vault_list(path, recursive):
    """List vault root or a specific directory.

    PATH is the directory path relative to vault root (optional).
    Trailing slash is not required.

    Examples:
        cli-anything-obsidian vault list
        cli-anything-obsidian vault list "Projects"
        cli-anything-obsidian vault list -r "Daily Notes"
    """
    if recursive:
        files = vault_mod.list_dir_recursive(_host, _api_key, path)
        if _json_output:
            output(files)
        else:
            if not files:
                click.echo("(empty directory)")
                return
            for f in files:
                click.echo(f"  {f}")
    else:
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
@click.option("--heading", default=None,
              help="Read only a specific heading section (e.g. 'Tasks' or 'Parent::Child').")
@handle_error
def vault_get(file, fmt, heading):
    """Get the content of a vault file.

    FILE is the path relative to vault root (e.g., 'Notes/My Note.md').

    Examples:
        cli-anything-obsidian vault get "Notes/My Note.md"
        cli-anything-obsidian vault get "Notes/My Note.md" --heading "Tasks"
        cli-anything-obsidian --json vault get "Notes/My Note.md" --format json
    """
    if heading:
        result = vault_mod.get_heading(_host, _api_key, file, heading)
    else:
        result = vault_mod.get(_host, _api_key, file, fmt=fmt)
    if _json_output or fmt != "markdown":
        output(result)
    else:
        content = result.get("content", result) if isinstance(result, dict) else result
        click.echo(content)


@vault.command("append")
@click.argument("file")
@click.argument("content", required=False, default=None)
@handle_error
def vault_append(file, content):
    """Append CONTENT to a vault FILE (creates the file if it doesn't exist).

    FILE: path relative to vault root.
    CONTENT: markdown text to append.  Use '-' for stdin.
    For content starting with '-', use: -- "- content"

    Examples:
        cli-anything-obsidian vault append "Notes/Log.md" "## Entry"
        echo "- item" | cli-anything-obsidian vault append "Notes/Log.md"
        cli-anything-obsidian vault append "Notes/Log.md" -- "- [ ] task"
    """
    content = _resolve_content(content)
    result = vault_mod.append(_host, _api_key, file, content)
    output(result, f"Appended to: {file}")


@vault.command("put")
@click.argument("file")
@click.argument("content", required=False, default=None)
@click.option("--no-overwrite", is_flag=True,
              help="Only create — fail if the file already exists.")
@handle_error
def vault_put(file, content, no_overwrite):
    """Create or replace a vault FILE with CONTENT.

    FILE: path relative to vault root.
    CONTENT: full file content.  Use '-' for stdin.
    For content starting with '-' or '---', use: -- "---\\nfrontmatter..."

    Examples:
        cli-anything-obsidian vault put "Notes/New.md" "# Title"
        echo "---\\ntitle: Test\\n---" | cli-anything-obsidian vault put "Notes/New.md"
        cli-anything-obsidian vault put --no-overwrite "Notes/New.md" "# Title"
    """
    content = _resolve_content(content)
    if no_overwrite and vault_mod.exists(_host, _api_key, file):
        raise click.UsageError(f"File already exists: {file}  (use without --no-overwrite to replace)")
    result = vault_mod.put(_host, _api_key, file, content)
    output(result, f"Written: {file}")


@vault.command("patch")
@click.argument("file")
@click.argument("content", required=False, default=None)
@click.option("--op", "operation",
              type=click.Choice(["append", "prepend", "replace"]),
              required=True, help="Patch operation type.")
@click.option("--type", "target_type",
              type=click.Choice(["heading", "block", "frontmatter"]),
              required=True, help="Target type to patch.")
@click.option("--target", required=True,
              help="Heading name, block ref (^abc123), or frontmatter key. "
                   "For sub-headings use 'Parent::Child' delimiter.")
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
    CONTENT: text to insert.  Use '-' for stdin.
    For content starting with '-', use: -- "- content"

    Examples:
        # Add a task under 'Tasks' heading (note -- before dash-content)
        cli-anything-obsidian vault patch "Project.md" --op append --type heading --target "Tasks" -- "- [ ] Review PR"

        # Update a frontmatter field
        cli-anything-obsidian vault patch "Project.md" "in-progress" --op replace --type frontmatter --target "status"

        # Pipe content via stdin
        echo "- [ ] New task" | cli-anything-obsidian vault patch "Project.md" --op append --type heading --target "Tasks"
    """
    content = _resolve_content(content)
    if operation == "append" and not content.startswith("\n"):
        content = "\n" + content
    result = vault_mod.patch(
        _host, _api_key, file, content,
        operation=operation, target_type=target_type, target=target,
        delimiter=delimiter, trim_whitespace=trim, create_if_missing=create,
    )
    output(result, f"Patched: {file} ({operation} at {target_type}: {target})")


@vault.command("delete")
@click.argument("file")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt.")
@handle_error
def vault_delete(file, yes):
    """Delete a vault FILE.

    FILE: path relative to vault root.
    Use --yes / -y to skip confirmation (required in non-interactive environments).
    """
    if not yes:
        if not sys.stdin.isatty():
            raise click.UsageError(
                "Cannot prompt for confirmation in non-interactive mode. Use --yes."
            )
        click.confirm(f"Delete {file} from the vault?", abort=True)
    result = vault_mod.delete(_host, _api_key, file)
    output(result, f"Deleted: {file}")


@vault.command("move")
@click.argument("src")
@click.argument("dst")
@handle_error
def vault_move(src, dst):
    """Move (rename) a vault file from SRC to DST.

    SRC: current path relative to vault root.
    DST: new path relative to vault root.

    Examples:
        cli-anything-obsidian vault move "Notes/old-name.md" "Notes/new-name.md"
        cli-anything-obsidian vault move "Inbox/note.md" "Archive/note.md"
    """
    result = vault_mod.move(_host, _api_key, src, dst)
    output(result, f"Moved: {src} → {dst}")


@vault.command("exists")
@click.argument("file")
@handle_error
def vault_exists(file):
    """Check if a vault FILE exists.

    FILE: path relative to vault root.
    Exit code 0 if exists, 1 if not.

    Examples:
        cli-anything-obsidian vault exists "Notes/My Note.md"
        cli-anything-obsidian vault exists "Notes/My Note.md" && echo "found"
    """
    found = vault_mod.exists(_host, _api_key, file)
    if _json_output:
        output({"exists": found, "file": file})
    else:
        if found:
            click.echo(f"✓ exists: {file}")
        else:
            click.echo(f"✗ not found: {file}")
            sys.exit(1)


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
@click.argument("content", required=False, default=None)
@click.option("--date", default=None, metavar="YYYY-MM-DD",
              help="Specific date (default: current period).")
@handle_error
def periodic_append(period, content, date):
    """Append CONTENT to a periodic note (creates it if it doesn't exist).

    PERIOD: daily | weekly | monthly | quarterly | yearly
    CONTENT: markdown text.  Use '-' for stdin.

    Example:
        cli-anything-obsidian periodic append daily "- [x] Reviewed PRs"
    """
    content = _resolve_content(content)
    result = periodic_mod.append(_host, _api_key, period, content, date=date)
    label = f"{period} ({date})" if date else period
    output(result, f"Appended to {label} note.")


@periodic.command("put")
@click.argument("period",
                type=click.Choice(["daily", "weekly", "monthly", "quarterly", "yearly"]))
@click.argument("content", required=False, default=None)
@click.option("--date", default=None, metavar="YYYY-MM-DD",
              help="Specific date (default: current period).")
@handle_error
def periodic_put(period, content, date):
    """Replace the content of a periodic note.

    PERIOD: daily | weekly | monthly | quarterly | yearly
    CONTENT: full new content.  Use '-' for stdin.
    """
    content = _resolve_content(content)
    result = periodic_mod.put(_host, _api_key, period, content, date=date)
    label = f"{period} ({date})" if date else period
    output(result, f"{label} note replaced.")


@periodic.command("patch")
@click.argument("period",
                type=click.Choice(["daily", "weekly", "monthly", "quarterly", "yearly"]))
@click.argument("content", required=False, default=None)
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
    CONTENT: text to insert.  Use '-' for stdin.
    """
    content = _resolve_content(content)
    if operation == "append" and not content.startswith("\n"):
        content = "\n" + content
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
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt.")
@handle_error
def periodic_delete(period, date, yes):
    """Delete a periodic note.

    Use --yes / -y to skip confirmation (required in non-interactive environments).
    """
    label = f"{period} ({date})" if date else period
    if not yes:
        if not sys.stdin.isatty():
            raise click.UsageError(
                "Cannot prompt for confirmation in non-interactive mode. Use --yes."
            )
        click.confirm(f"Delete {label} note?", abort=True)
    result = periodic_mod.delete(_host, _api_key, period, date=date)
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


# ── Dataview Plugin Commands ──────────────────────────────────────────────────

@cli.group("dataview")
def dataview():
    """Query your vault with Dataview DQL (requires Dataview plugin)."""
    pass


@dataview.command("raw")
@click.argument("dql")
@handle_error
def dataview_raw(dql):
    """Execute a raw DQL query string.

    DQL: complete Dataview query (TABLE, LIST, TASK, or CALENDAR).

    Examples:
        cli-anything-obsidian dataview raw 'TABLE file.name FROM "Projects"'
        cli-anything-obsidian dataview raw 'LIST WHERE status = "rascunho"'
        cli-anything-obsidian --json dataview raw 'TASK FROM "marketing/"'
    """
    results = dataview_mod.raw(_host, _api_key, dql)
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


@dataview.command("table")
@click.argument("fields", default="file.name")
@click.option("--from", "from_folder", default=None,
              help='Source folder or tag (e.g., \'"Projects"\' or \'#tag\').')
@click.option("--where", default=None,
              help='Filter condition (e.g., \'status = "rascunho"\').')
@click.option("--sort", default=None,
              help='Sort clause (e.g., "file.mtime DESC").')
@click.option("--limit", type=int, default=None,
              help="Maximum number of results.")
@handle_error
def dataview_table(fields, from_folder, where, sort, limit):
    """Run a Dataview TABLE query.

    FIELDS: comma-separated fields to display (default: file.name).

    Examples:
        cli-anything-obsidian dataview table "file.name, status"
        cli-anything-obsidian dataview table "file.name, status" --from '"marketing/"' --where 'status = "rascunho"'
        cli-anything-obsidian --json dataview table --from '"briefing/"' --sort "file.mtime DESC" --limit 10
    """
    results = dataview_mod.table(
        _host, _api_key, fields=fields,
        from_folder=from_folder, where=where, sort=sort, limit=limit,
    )
    if _json_output:
        output(results)
    else:
        if not results:
            click.echo("No results.")
            return
        click.echo(f"Found {len(results)} result(s):\n")
        for item in results:
            fn = item.get("filename", "")
            res = item.get("result", {})
            if isinstance(res, dict):
                vals = ", ".join(f"{k}={v}" for k, v in res.items())
                click.echo(f"  {fn}: {vals}")
            else:
                click.echo(f"  {fn}: {res}")


@dataview.command("list")
@click.option("--expr", "expression", default=None,
              help='Expression to display (e.g., "file.name").')
@click.option("--from", "from_folder", default=None,
              help='Source folder or tag.')
@click.option("--where", default=None,
              help='Filter condition.')
@click.option("--sort", default=None,
              help='Sort clause.')
@click.option("--limit", type=int, default=None,
              help="Maximum number of results.")
@handle_error
def dataview_list(expression, from_folder, where, sort, limit):
    """Run a Dataview LIST query.

    Examples:
        cli-anything-obsidian dataview list --from '"marketing/"'
        cli-anything-obsidian dataview list --where 'type = "artigo"' --sort "file.mtime DESC"
        cli-anything-obsidian --json dataview list --from '"briefing/"' --limit 20
    """
    results = dataview_mod.list_query(
        _host, _api_key, expression=expression,
        from_folder=from_folder, where=where, sort=sort, limit=limit,
    )
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
            click.echo(f"  {fn}: {res}" if res else f"  {fn}")


@dataview.command("task")
@click.option("--from", "from_folder", default=None,
              help='Source folder or tag.')
@click.option("--where", default=None,
              help='Filter condition (e.g., "!completed").')
@click.option("--sort", default=None,
              help='Sort clause.')
@click.option("--limit", type=int, default=None,
              help="Maximum number of results.")
@handle_error
def dataview_task(from_folder, where, sort, limit):
    """Run a Dataview TASK query — list tasks from notes.

    Examples:
        cli-anything-obsidian dataview task --from '"marketing/"'
        cli-anything-obsidian dataview task --where "!completed"
        cli-anything-obsidian --json dataview task --from '"briefing/"' --limit 50
    """
    results = dataview_mod.task(
        _host, _api_key,
        from_folder=from_folder, where=where, sort=sort, limit=limit,
    )
    if _json_output:
        output(results)
    else:
        if not results:
            click.echo("No tasks found.")
            return
        click.echo(f"Found {len(results)} file(s) with tasks:")
        for item in results:
            fn = item.get("filename", "")
            tasks = item.get("result", [])
            click.echo(f"\n  {fn}:")
            if isinstance(tasks, list):
                for t in tasks:
                    text = t.get("text", t) if isinstance(t, dict) else str(t)
                    click.echo(f"    {text}")
            else:
                click.echo(f"    {tasks}")


# ── Templater Plugin Commands ────────────────────────────────────────────────

@cli.group("templater")
def templater():
    """Manage and apply Templater templates (requires Templater plugin)."""
    pass


@templater.command("list")
@click.option("--folder", default="Templates",
              help='Templates folder path (default: "Templates").')
@handle_error
def templater_list(folder):
    """List available templates.

    Examples:
        cli-anything-obsidian templater list
        cli-anything-obsidian templater list --folder "my-templates"
        cli-anything-obsidian --json templater list
    """
    templates = templater_mod.list_templates(_host, _api_key, folder=folder)
    if _json_output:
        output(templates)
    else:
        if not templates:
            click.echo(f"No templates found in {folder}/")
            return
        click.echo(f"Templates in {folder}/:\n")
        for t in templates:
            click.echo(f"  {t}")


@templater.command("get")
@click.argument("template")
@handle_error
def templater_get(template):
    """Read a template file's content.

    TEMPLATE: path to the template file relative to vault root.

    Example:
        cli-anything-obsidian templater get "Templates/blog-post.md"
    """
    content = templater_mod.get_template(_host, _api_key, template)
    if _json_output:
        output({"template": template, "content": content})
    else:
        click.echo(content)


@templater.command("create")
@click.argument("dest")
@click.argument("template")
@click.option("--var", "-v", "variables", multiple=True,
              help='Variable substitution as key=value. Repeatable.')
@handle_error
def templater_create(dest, template, variables):
    """Create a new note from a template.

    DEST: destination file path relative to vault root.
    TEMPLATE: template file path relative to vault root.

    Applies simple {{variable}} substitutions. For full Templater processing
    (tp.* functions), run 'templater run' after creation.

    Examples:
        cli-anything-obsidian templater create "briefing/novo-artigo.md" "Templates/blog-post.md"
        cli-anything-obsidian templater create "briefing/vsl.md" "Templates/vsl.md" -v title="Creatina" -v slug="creatina-55"
    """
    var_dict = {}
    for v in variables:
        if "=" in v:
            key, val = v.split("=", 1)
            var_dict[key.strip()] = val.strip()
    result = templater_mod.create_from_template(
        _host, _api_key, dest, template,
        variables=var_dict if var_dict else None,
    )
    output(result, f"Created: {dest} (from {template})")


@templater.command("run")
@handle_error
def templater_run():
    """Run Templater on the currently active file.

    Processes all Templater expressions (tp.* functions, variables) in the
    currently open file in Obsidian.

    Example:
        cli-anything-obsidian templater run
    """
    result = templater_mod.run_on_file(_host, _api_key)
    output(result, "Templater executed on active file.")


@templater.command("insert")
@handle_error
def templater_insert():
    """Open Templater's template picker to insert at cursor.

    Opens the Templater template selection dialog in Obsidian.

    Example:
        cli-anything-obsidian templater insert
    """
    result = templater_mod.insert_template(_host, _api_key)
    output(result, "Templater insert dialog opened.")


# ── Folder Notes Plugin Commands ─────────────────────────────────────────────

@cli.group("foldernotes")
def foldernotes():
    """Manage folder index notes (requires Folder Notes plugin)."""
    pass


@foldernotes.command("get")
@click.argument("folder")
@click.option("--style", type=click.Choice(["inside", "outside"]),
              default="inside", show_default=True,
              help="Naming style: 'inside' = folder/folder.md, 'outside' = folder.md next to folder.")
@handle_error
def foldernotes_get(folder, style):
    """Read a folder note's content.

    FOLDER: folder path relative to vault root.

    Examples:
        cli-anything-obsidian foldernotes get "marketing"
        cli-anything-obsidian foldernotes get "briefing" --style outside
    """
    result = foldernotes_mod.get(_host, _api_key, folder, style=style)
    if _json_output:
        output(result)
    else:
        content = result.get("content", result) if isinstance(result, dict) else result
        click.echo(content)


@foldernotes.command("create")
@click.argument("folder")
@click.option("--title", default=None, help="Custom title (default: folder name).")
@click.option("--style", type=click.Choice(["inside", "outside"]),
              default="inside", show_default=True,
              help="Naming style.")
@click.option("--overwrite", is_flag=True, help="Overwrite existing folder note.")
@handle_error
def foldernotes_create(folder, title, style, overwrite):
    """Create an auto-generated index note for a folder.

    Lists all files in the folder as wiki-links.

    FOLDER: folder path relative to vault root.

    Examples:
        cli-anything-obsidian foldernotes create "marketing"
        cli-anything-obsidian foldernotes create "briefing" --title "Briefings"
        cli-anything-obsidian foldernotes create "canais" --overwrite
    """
    result = foldernotes_mod.create(
        _host, _api_key, folder, title=title, style=style, overwrite=overwrite,
    )
    output(result, f"Folder note created: {result.get('file', folder)}")


@foldernotes.command("refresh")
@click.argument("folder")
@click.option("--title", default=None, help="Custom title.")
@click.option("--style", type=click.Choice(["inside", "outside"]),
              default="inside", show_default=True)
@handle_error
def foldernotes_refresh(folder, title, style):
    """Regenerate a folder note with fresh file listing.

    FOLDER: folder path relative to vault root.

    Example:
        cli-anything-obsidian foldernotes refresh "marketing"
    """
    result = foldernotes_mod.refresh(_host, _api_key, folder, title=title, style=style)
    output(result, f"Folder note refreshed: {result.get('file', folder)}")


@foldernotes.command("list")
@click.argument("root", default="")
@click.option("--style", type=click.Choice(["inside", "outside"]),
              default="inside", show_default=True)
@handle_error
def foldernotes_list(root, style):
    """List folders and whether they have folder notes.

    ROOT: directory to scan (default: vault root).

    Examples:
        cli-anything-obsidian foldernotes list
        cli-anything-obsidian --json foldernotes list "marketing"
    """
    folders = foldernotes_mod.list_folders_with_notes(
        _host, _api_key, root=root, style=style,
    )
    if _json_output:
        output(folders)
    else:
        if not folders:
            click.echo("No folders found.")
            return
        click.echo(f"{'FOLDER':<40} {'NOTE'}")
        click.echo("─" * 55)
        for f in folders:
            status = "✓" if f["has_note"] else "✗"
            click.echo(f"  {status} {f['folder']:<38} {f['note_path']}")


@foldernotes.command("exists")
@click.argument("folder")
@click.option("--style", type=click.Choice(["inside", "outside"]),
              default="inside", show_default=True)
@handle_error
def foldernotes_exists(folder, style):
    """Check if a folder note exists.

    FOLDER: folder path relative to vault root.
    Exit code 0 if exists, 1 if not.

    Example:
        cli-anything-obsidian foldernotes exists "marketing"
    """
    found = foldernotes_mod.exists(_host, _api_key, folder, style=style)
    if _json_output:
        output({"exists": found, "folder": folder})
    else:
        if found:
            click.echo(f"✓ folder note exists: {folder}")
        else:
            click.echo(f"✗ no folder note: {folder}")
            sys.exit(1)


# ── Charts Plugin Commands ───────────────────────────────────────────────────

@cli.group("charts")
def charts():
    """Generate and insert Chart.js charts into notes (requires Obsidian Charts plugin)."""
    pass


@charts.command("generate")
@click.option("--type", "chart_type",
              type=click.Choice(["bar", "line", "pie", "doughnut", "radar", "polarArea"]),
              required=True, help="Chart type.")
@click.option("--labels", required=True,
              help='Comma-separated labels (e.g., "Jan,Fev,Mar").')
@click.option("--data", "data_str", required=True,
              help='Comma-separated values (e.g., "100,200,150"). '
                   'For multiple datasets, use | separator: "100,200|50,80".')
@click.option("--names", default=None,
              help='Comma-separated dataset names (e.g., "Revenue,Cost").')
@click.option("--title", default=None, help="Chart title.")
@click.option("--stacked", is_flag=True, help="Stack bars/lines.")
@click.option("--width", default="80%", help="Chart width (default: 80%%).")
@handle_error
def charts_generate(chart_type, labels, data_str, names, title, stacked, width):
    """Generate a chart codeblock (prints to stdout).

    Copy the output into any Obsidian note to render it.

    Examples:
        cli-anything-obsidian charts generate --type bar --labels "Jan,Fev,Mar" --data "100,200,150"
        cli-anything-obsidian charts generate --type pie --labels "Orgânico,Pago,Email" --data "45,30,25" --title "Tráfego"
        cli-anything-obsidian charts generate --type line --labels "S1,S2,S3,S4" --data "10,20,15,30|5,10,8,20" --names "Vendas,Leads"
    """
    label_list = [l.strip() for l in labels.split(",")]
    raw_datasets = data_str.split("|")
    name_list = [n.strip() for n in names.split(",")] if names else []

    datasets = []
    for i, ds_str in enumerate(raw_datasets):
        values = [float(v.strip()) for v in ds_str.split(",")]
        ds_name = name_list[i] if i < len(name_list) else f"Dataset {i + 1}"
        datasets.append({"label": ds_name, "data": values})

    block = charts_mod.generate_block(
        chart_type, label_list, datasets,
        title=title, stacked=stacked, width=width,
    )
    if _json_output:
        output({"chart_type": chart_type, "block": block})
    else:
        click.echo(block)


@charts.command("insert")
@click.argument("file")
@click.option("--type", "chart_type",
              type=click.Choice(["bar", "line", "pie", "doughnut", "radar", "polarArea"]),
              required=True, help="Chart type.")
@click.option("--labels", required=True,
              help='Comma-separated labels.')
@click.option("--data", "data_str", required=True,
              help='Comma-separated values. Multiple datasets: use | separator.')
@click.option("--names", default=None,
              help='Comma-separated dataset names.')
@click.option("--title", default=None, help="Chart title.")
@click.option("--heading", default=None,
              help="Insert under this heading (default: append to end).")
@click.option("--stacked", is_flag=True, help="Stack bars/lines.")
@handle_error
def charts_insert(file, chart_type, labels, data_str, names, title, heading, stacked):
    """Generate a chart and insert it into a vault file.

    FILE: path relative to vault root.

    Examples:
        cli-anything-obsidian charts insert "reports/q1.md" --type bar --labels "Jan,Fev,Mar" --data "100,200,150" --heading "Métricas"
        cli-anything-obsidian charts insert "dashboard.md" --type pie --labels "Orgânico,Pago" --data "60,40" --title "Tráfego"
    """
    label_list = [l.strip() for l in labels.split(",")]
    raw_datasets = data_str.split("|")
    name_list = [n.strip() for n in names.split(",")] if names else []

    datasets = []
    for i, ds_str in enumerate(raw_datasets):
        values = [float(v.strip()) for v in ds_str.split(",")]
        ds_name = name_list[i] if i < len(name_list) else f"Dataset {i + 1}"
        datasets.append({"label": ds_name, "data": values})

    block = charts_mod.generate_block(
        chart_type, label_list, datasets,
        title=title, stacked=stacked,
    )
    result = charts_mod.insert_chart(_host, _api_key, file, block, heading=heading)
    output(result, f"Chart inserted into: {file}")


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
        "vault":           "list | get | append | put | patch | delete | move | exists",
        "periodic":        "get | append | put | patch | delete",
        "search":          "simple | dql | jsonlogic",
        "dataview":        "raw | table | list | task",
        "templater":       "list | get | create | run | insert",
        "foldernotes":     "get | create | refresh | list | exists",
        "charts":          "generate | insert",
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
