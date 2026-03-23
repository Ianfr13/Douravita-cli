"""cli-anything-langfuse — CLI harness for the Langfuse LLM observability platform.

Provides stateful CLI + REPL interface to the Langfuse REST API for
traces, observations, scores, prompts, datasets, sessions, models, and more.
"""

import json
import sys

import click

from cli_anything.langfuse import __version__
from cli_anything.langfuse.utils.config import (
    resolve_credentials,
    set_profile,
    set_active_profile,
    list_profiles,
    delete_profile,
)
from cli_anything.langfuse.utils.langfuse_backend import LangfuseClient, LangfuseAPIError
from cli_anything.langfuse.utils.formatters import (
    output_json,
    output_table,
    format_timestamp,
    format_cost,
    format_latency,
    truncate,
)

# ── Helpers ──────────────────────────────────────────────────────────


def _make_client(ctx) -> LangfuseClient:
    """Build a LangfuseClient from the Click context."""
    creds = resolve_credentials(
        public_key=ctx.obj.get("public_key"),
        secret_key=ctx.obj.get("secret_key"),
        base_url=ctx.obj.get("base_url"),
        profile=ctx.obj.get("profile"),
    )
    return LangfuseClient(
        public_key=creds["public_key"],
        secret_key=creds["secret_key"],
        base_url=creds["base_url"],
    )


def _handle_error(ctx, e: LangfuseAPIError):
    """Handle API errors with consistent formatting."""
    if ctx.obj.get("json_output"):
        output_json({"error": str(e), "status_code": e.status_code})
    else:
        click.echo(f"Error: {e}", err=True)
    sys.exit(1)


def _parse_json_arg(value: str | None) -> dict | list | str | None:
    """Parse a JSON string argument, or return as-is if not valid JSON."""
    if value is None:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


# ── Main CLI Group ───────────────────────────────────────────────────


@click.group(invoke_without_command=True)
@click.option("--json", "json_output", is_flag=True, help="Output as JSON.")
@click.option("--public-key", envvar="LANGFUSE_PUBLIC_KEY", help="Langfuse public key.")
@click.option("--secret-key", envvar="LANGFUSE_SECRET_KEY", help="Langfuse secret key.")
@click.option("--base-url", envvar="LANGFUSE_BASE_URL", help="Langfuse base URL.")
@click.option("--profile", envvar="LANGFUSE_PROFILE", help="Config profile to use.")
@click.version_option(__version__, prog_name="cli-anything-langfuse")
@click.pass_context
def cli(ctx, json_output, public_key, secret_key, base_url, profile):
    """cli-anything-langfuse — CLI for Langfuse LLM observability platform."""
    ctx.ensure_object(dict)
    ctx.obj["json_output"] = json_output
    ctx.obj["public_key"] = public_key
    ctx.obj["secret_key"] = secret_key
    ctx.obj["base_url"] = base_url
    ctx.obj["profile"] = profile

    if ctx.invoked_subcommand is None:
        ctx.invoke(repl)


# ── REPL ─────────────────────────────────────────────────────────────


@cli.command(hidden=True)
@click.pass_context
def repl(ctx):
    """Start the interactive REPL."""
    from cli_anything.langfuse.utils.repl_skin import ReplSkin

    skin = ReplSkin("langfuse", version=__version__)
    skin.print_banner()

    pt_session = skin.create_prompt_session()

    commands_help = {
        "traces list": "List traces",
        "traces get <id>": "Get trace details",
        "observations list": "List observations",
        "observations get <id>": "Get observation details",
        "scores list": "List scores",
        "scores create": "Create a score",
        "prompts list": "List prompts",
        "prompts get <name>": "Get prompt by name",
        "prompts create": "Create a prompt",
        "datasets list": "List datasets",
        "datasets get <name>": "Get dataset details",
        "sessions list": "List sessions",
        "models list": "List models",
        "health": "Check API health",
        "config show": "Show current config",
        "help": "Show this help",
        "quit": "Exit the REPL",
    }

    while True:
        try:
            line = skin.get_input(pt_session, context="langfuse")
        except (EOFError, KeyboardInterrupt):
            skin.print_goodbye()
            break

        if not line:
            continue

        if line in ("quit", "exit", "q"):
            skin.print_goodbye()
            break

        if line == "help":
            skin.help(commands_help)
            continue

        # Parse the REPL line into Click args
        args = line.split()
        # Carry over global flags
        if ctx.obj.get("json_output"):
            args = ["--json"] + args

        try:
            cli.main(args=args, standalone_mode=False, **{"parent": ctx.parent})
        except SystemExit:
            pass
        except click.UsageError as e:
            skin.error(str(e))
        except LangfuseAPIError as e:
            skin.error(str(e))
        except Exception as e:
            skin.error(f"Unexpected error: {e}")


# ══════════════════════════════════════════════════════════════════════
# TRACES
# ══════════════════════════════════════════════════════════════════════


@cli.group()
@click.pass_context
def traces(ctx):
    """Manage traces."""
    pass


@traces.command("list")
@click.option("--limit", default=20, help="Number of results.")
@click.option("--page", default=1, help="Page number.")
@click.option("--name", help="Filter by trace name.")
@click.option("--user-id", help="Filter by user ID.")
@click.option("--session-id", help="Filter by session ID.")
@click.option("--tags", help="Filter by tags (comma-separated).")
@click.option("--from", "from_ts", help="From timestamp (ISO format).")
@click.option("--to", "to_ts", help="To timestamp (ISO format).")
@click.pass_context
def traces_list(ctx, limit, page, name, user_id, session_id, tags, from_ts, to_ts):
    """List traces."""
    from cli_anything.langfuse.core.traces import list_traces

    try:
        client = _make_client(ctx)
        tag_list = tags.split(",") if tags else None
        result = list_traces(
            client, page=page, limit=limit, name=name,
            user_id=user_id, session_id=session_id, tags=tag_list,
            from_timestamp=from_ts, to_timestamp=to_ts,
        )
    except (LangfuseAPIError, ValueError) as e:
        _handle_error(ctx, e) if isinstance(e, LangfuseAPIError) else click.echo(f"Error: {e}", err=True) or sys.exit(1)
        return

    if ctx.obj.get("json_output"):
        output_json(result)
        return

    data = result.get("data", [])
    if not data:
        click.echo("No traces found.")
        return

    headers = ["ID", "Name", "Timestamp", "Latency", "Cost", "Tags"]
    rows = []
    for t in data:
        rows.append([
            t.get("id", "")[:12],
            truncate(t.get("name", "-"), 25),
            format_timestamp(t.get("timestamp")),
            format_latency(t.get("latency")),
            format_cost(t.get("totalCost")),
            ",".join(t.get("tags", []))[:20] or "-",
        ])
    output_table(headers, rows)
    meta = result.get("meta", {})
    total = meta.get("totalItems", meta.get("totalCount", "?"))
    click.echo(f"\nPage {meta.get('page', page)}/{-(-int(total) // limit) if str(total).isdigit() else '?'} ({total} total)")


@traces.command("get")
@click.argument("trace_id")
@click.pass_context
def traces_get(ctx, trace_id):
    """Get a trace by ID."""
    from cli_anything.langfuse.core.traces import get_trace

    try:
        client = _make_client(ctx)
        result = get_trace(client, trace_id)
    except LangfuseAPIError as e:
        _handle_error(ctx, e)
        return

    if ctx.obj.get("json_output"):
        output_json(result)
        return

    click.echo(f"Trace: {result.get('id')}")
    click.echo(f"  Name:      {result.get('name', '-')}")
    click.echo(f"  Timestamp: {format_timestamp(result.get('timestamp'))}")
    click.echo(f"  Session:   {result.get('sessionId', '-')}")
    click.echo(f"  User:      {result.get('userId', '-')}")
    click.echo(f"  Latency:   {format_latency(result.get('latency'))}")
    click.echo(f"  Cost:      {format_cost(result.get('totalCost'))}")
    click.echo(f"  Tags:      {', '.join(result.get('tags', [])) or '-'}")
    click.echo(f"  Input:     {truncate(json.dumps(result.get('input')), 80)}")
    click.echo(f"  Output:    {truncate(json.dumps(result.get('output')), 80)}")

    obs = result.get("observations", [])
    if obs:
        click.echo(f"\n  Observations ({len(obs)}):")
        for o in obs[:10]:
            click.echo(f"    - {o.get('type', '?'):12s} {o.get('name', '-'):25s} {format_latency(o.get('latency'))}")


@traces.command("delete")
@click.argument("trace_id")
@click.option("--yes", is_flag=True, help="Skip confirmation.")
@click.pass_context
def traces_delete(ctx, trace_id, yes):
    """Delete a trace by ID."""
    from cli_anything.langfuse.core.traces import delete_trace

    if not yes:
        click.confirm(f"Delete trace {trace_id}?", abort=True)

    try:
        client = _make_client(ctx)
        result = delete_trace(client, trace_id)
    except LangfuseAPIError as e:
        _handle_error(ctx, e)
        return

    if ctx.obj.get("json_output"):
        output_json({"status": "deleted", "traceId": trace_id})
    else:
        click.echo(f"Trace {trace_id} deleted.")


# ══════════════════════════════════════════════════════════════════════
# OBSERVATIONS
# ══════════════════════════════════════════════════════════════════════


@cli.group()
@click.pass_context
def observations(ctx):
    """Manage observations (spans, generations, events)."""
    pass


@observations.command("list")
@click.option("--limit", default=20, help="Number of results.")
@click.option("--page", default=1, help="Page number.")
@click.option("--trace-id", help="Filter by trace ID.")
@click.option("--name", help="Filter by observation name.")
@click.option("--type", "obs_type", help="Filter by type (SPAN, GENERATION, EVENT).")
@click.option("--from", "from_ts", help="From start time (ISO format).")
@click.option("--to", "to_ts", help="To start time (ISO format).")
@click.pass_context
def observations_list(ctx, limit, page, trace_id, name, obs_type, from_ts, to_ts):
    """List observations."""
    from cli_anything.langfuse.core.observations import list_observations

    try:
        client = _make_client(ctx)
        result = list_observations(
            client, page=page, limit=limit, trace_id=trace_id,
            name=name, obs_type=obs_type,
            from_start_time=from_ts, to_start_time=to_ts,
        )
    except (LangfuseAPIError, ValueError) as e:
        _handle_error(ctx, e) if isinstance(e, LangfuseAPIError) else click.echo(f"Error: {e}", err=True) or sys.exit(1)
        return

    if ctx.obj.get("json_output"):
        output_json(result)
        return

    data = result.get("data", [])
    if not data:
        click.echo("No observations found.")
        return

    headers = ["ID", "Type", "Name", "Model", "Start", "Latency"]
    rows = []
    for o in data:
        rows.append([
            o.get("id", "")[:12],
            o.get("type", "-"),
            truncate(o.get("name", "-"), 20),
            truncate(o.get("model", "-"), 20),
            format_timestamp(o.get("startTime")),
            format_latency(o.get("latency")),
        ])
    output_table(headers, rows)


@observations.command("get")
@click.argument("observation_id")
@click.pass_context
def observations_get(ctx, observation_id):
    """Get an observation by ID."""
    from cli_anything.langfuse.core.observations import get_observation

    try:
        client = _make_client(ctx)
        result = get_observation(client, observation_id)
    except LangfuseAPIError as e:
        _handle_error(ctx, e)
        return

    if ctx.obj.get("json_output"):
        output_json(result)
        return

    click.echo(f"Observation: {result.get('id')}")
    click.echo(f"  Type:      {result.get('type', '-')}")
    click.echo(f"  Name:      {result.get('name', '-')}")
    click.echo(f"  Trace:     {result.get('traceId', '-')}")
    click.echo(f"  Model:     {result.get('model', '-')}")
    click.echo(f"  Start:     {format_timestamp(result.get('startTime'))}")
    click.echo(f"  End:       {format_timestamp(result.get('endTime'))}")
    click.echo(f"  Latency:   {format_latency(result.get('latency'))}")
    click.echo(f"  Level:     {result.get('level', '-')}")
    click.echo(f"  Input:     {truncate(json.dumps(result.get('input')), 80)}")
    click.echo(f"  Output:    {truncate(json.dumps(result.get('output')), 80)}")

    usage = result.get("usageDetails") or result.get("usage")
    if usage:
        click.echo(f"  Usage:     {json.dumps(usage)}")


# ══════════════════════════════════════════════════════════════════════
# SCORES
# ══════════════════════════════════════════════════════════════════════


@cli.group()
@click.pass_context
def scores(ctx):
    """Manage scores and evaluations."""
    pass


@scores.command("list")
@click.option("--limit", default=20, help="Number of results.")
@click.option("--page", default=1, help="Page number.")
@click.option("--name", help="Filter by score name.")
@click.option("--source", help="Filter by source (ANNOTATION, API, EVAL).")
@click.option("--data-type", help="Filter by data type (NUMERIC, BOOLEAN, CATEGORICAL).")
@click.pass_context
def scores_list(ctx, limit, page, name, source, data_type):
    """List scores."""
    from cli_anything.langfuse.core.scores import list_scores

    try:
        client = _make_client(ctx)
        result = list_scores(client, page=page, limit=limit, name=name,
                             source=source, data_type=data_type)
    except (LangfuseAPIError, ValueError) as e:
        _handle_error(ctx, e) if isinstance(e, LangfuseAPIError) else click.echo(f"Error: {e}", err=True) or sys.exit(1)
        return

    if ctx.obj.get("json_output"):
        output_json(result)
        return

    data = result.get("data", [])
    if not data:
        click.echo("No scores found.")
        return

    headers = ["ID", "Name", "Value", "Source", "Trace", "Timestamp"]
    rows = []
    for s in data:
        val = s.get("stringValue") or s.get("value", "-")
        rows.append([
            s.get("id", "")[:12],
            truncate(s.get("name", "-"), 20),
            str(val),
            s.get("source", "-"),
            s.get("traceId", "")[:12],
            format_timestamp(s.get("timestamp")),
        ])
    output_table(headers, rows)


@scores.command("get")
@click.argument("score_id")
@click.pass_context
def scores_get(ctx, score_id):
    """Get a score by ID."""
    from cli_anything.langfuse.core.scores import get_score

    try:
        client = _make_client(ctx)
        result = get_score(client, score_id)
    except LangfuseAPIError as e:
        _handle_error(ctx, e)
        return

    if ctx.obj.get("json_output"):
        output_json(result)
    else:
        click.echo(f"Score: {result.get('id')}")
        click.echo(f"  Name:    {result.get('name', '-')}")
        click.echo(f"  Value:   {result.get('value', '-')}")
        click.echo(f"  Source:  {result.get('source', '-')}")
        click.echo(f"  Trace:   {result.get('traceId', '-')}")
        click.echo(f"  Comment: {result.get('comment', '-')}")


@scores.command("create")
@click.option("--trace-id", required=True, help="Trace ID to score.")
@click.option("--name", required=True, help="Score name.")
@click.option("--value", type=float, help="Numeric score value.")
@click.option("--string-value", help="String/categorical score value.")
@click.option("--observation-id", help="Optional observation ID.")
@click.option("--data-type", help="NUMERIC, BOOLEAN, or CATEGORICAL.")
@click.option("--comment", help="Score comment.")
@click.pass_context
def scores_create(ctx, trace_id, name, value, string_value, observation_id, data_type, comment):
    """Create a score on a trace or observation."""
    from cli_anything.langfuse.core.scores import create_score

    score_value = value if value is not None else string_value

    try:
        client = _make_client(ctx)
        result = create_score(
            client, trace_id=trace_id, name=name, value=score_value,
            observation_id=observation_id, data_type=data_type, comment=comment,
        )
    except LangfuseAPIError as e:
        _handle_error(ctx, e)
        return

    if ctx.obj.get("json_output"):
        output_json(result)
    else:
        click.echo(f"Score created: {result.get('id', 'ok')}")


@scores.command("delete")
@click.argument("score_id")
@click.option("--yes", is_flag=True, help="Skip confirmation.")
@click.pass_context
def scores_delete(ctx, score_id, yes):
    """Delete a score by ID."""
    from cli_anything.langfuse.core.scores import delete_score

    if not yes:
        click.confirm(f"Delete score {score_id}?", abort=True)

    try:
        client = _make_client(ctx)
        result = delete_score(client, score_id)
    except LangfuseAPIError as e:
        _handle_error(ctx, e)
        return

    if ctx.obj.get("json_output"):
        output_json({"status": "deleted", "scoreId": score_id})
    else:
        click.echo(f"Score {score_id} deleted.")


# ── Score Configs ────────────────────────────────────────────────────


@cli.group("score-configs")
@click.pass_context
def score_configs(ctx):
    """Manage score configurations."""
    pass


@score_configs.command("list")
@click.option("--limit", default=20, help="Number of results.")
@click.option("--page", default=1, help="Page number.")
@click.pass_context
def score_configs_list(ctx, limit, page):
    """List score configurations."""
    from cli_anything.langfuse.core.scores import list_score_configs

    try:
        client = _make_client(ctx)
        result = list_score_configs(client, page=page, limit=limit)
    except (LangfuseAPIError, ValueError) as e:
        _handle_error(ctx, e) if isinstance(e, LangfuseAPIError) else click.echo(f"Error: {e}", err=True) or sys.exit(1)
        return

    if ctx.obj.get("json_output"):
        output_json(result)
        return

    data = result.get("data", [])
    if not data:
        click.echo("No score configs found.")
        return

    headers = ["ID", "Name", "Data Type", "Min", "Max", "Archived"]
    rows = []
    for c in data:
        rows.append([
            c.get("id", "")[:12],
            truncate(c.get("name", "-"), 25),
            c.get("dataType", "-"),
            str(c.get("minValue", "-")),
            str(c.get("maxValue", "-")),
            str(c.get("isArchived", False)),
        ])
    output_table(headers, rows)


@score_configs.command("create")
@click.option("--name", required=True, help="Config name.")
@click.option("--data-type", required=True, type=click.Choice(["NUMERIC", "BOOLEAN", "CATEGORICAL"]))
@click.option("--min-value", type=float, help="Minimum value (NUMERIC).")
@click.option("--max-value", type=float, help="Maximum value (NUMERIC).")
@click.option("--description", help="Config description.")
@click.pass_context
def score_configs_create(ctx, name, data_type, min_value, max_value, description):
    """Create a score configuration."""
    from cli_anything.langfuse.core.scores import create_score_config

    try:
        client = _make_client(ctx)
        result = create_score_config(
            client, name=name, data_type=data_type,
            min_value=min_value, max_value=max_value,
            description=description,
        )
    except LangfuseAPIError as e:
        _handle_error(ctx, e)
        return

    if ctx.obj.get("json_output"):
        output_json(result)
    else:
        click.echo(f"Score config created: {result.get('id', 'ok')}")


# ══════════════════════════════════════════════════════════════════════
# PROMPTS
# ══════════════════════════════════════════════════════════════════════


@cli.group()
@click.pass_context
def prompts(ctx):
    """Manage prompt templates."""
    pass


@prompts.command("list")
@click.option("--limit", default=20, help="Number of results.")
@click.option("--page", default=1, help="Page number.")
@click.option("--name", help="Filter by prompt name.")
@click.option("--label", help="Filter by label.")
@click.option("--tag", help="Filter by tag.")
@click.pass_context
def prompts_list(ctx, limit, page, name, label, tag):
    """List prompts."""
    from cli_anything.langfuse.core.prompts import list_prompts

    try:
        client = _make_client(ctx)
        result = list_prompts(client, page=page, limit=limit, name=name,
                              label=label, tag=tag)
    except (LangfuseAPIError, ValueError) as e:
        _handle_error(ctx, e) if isinstance(e, LangfuseAPIError) else click.echo(f"Error: {e}", err=True) or sys.exit(1)
        return

    if ctx.obj.get("json_output"):
        output_json(result)
        return

    data = result.get("data", [])
    if not data:
        click.echo("No prompts found.")
        return

    headers = ["Name", "Version", "Type", "Labels", "Tags", "Created"]
    rows = []
    for p in data:
        rows.append([
            truncate(p.get("name", "-"), 25),
            str(p.get("version", "-")),
            p.get("type", "-"),
            ",".join(p.get("labels", []))[:15] or "-",
            ",".join(p.get("tags", []))[:15] or "-",
            format_timestamp(p.get("createdAt")),
        ])
    output_table(headers, rows)


@prompts.command("get")
@click.argument("prompt_name")
@click.option("--version", type=int, help="Specific version number.")
@click.option("--label", help="Label (e.g., 'production').")
@click.pass_context
def prompts_get(ctx, prompt_name, version, label):
    """Get a prompt by name."""
    from cli_anything.langfuse.core.prompts import get_prompt

    try:
        client = _make_client(ctx)
        result = get_prompt(client, prompt_name, version=version, label=label)
    except LangfuseAPIError as e:
        _handle_error(ctx, e)
        return

    if ctx.obj.get("json_output"):
        output_json(result)
        return

    click.echo(f"Prompt: {result.get('name')}")
    click.echo(f"  Version: {result.get('version')}")
    click.echo(f"  Type:    {result.get('type')}")
    click.echo(f"  Labels:  {', '.join(result.get('labels', [])) or '-'}")
    click.echo(f"  Tags:    {', '.join(result.get('tags', [])) or '-'}")

    prompt_content = result.get("prompt")
    if isinstance(prompt_content, str):
        click.echo(f"\n--- Prompt ---\n{prompt_content}\n---")
    elif isinstance(prompt_content, list):
        click.echo("\n--- Messages ---")
        for msg in prompt_content:
            role = msg.get("role", "?")
            content = msg.get("content", "")
            click.echo(f"  [{role}]: {content}")
        click.echo("---")

    config = result.get("config")
    if config:
        click.echo(f"\n  Config: {json.dumps(config, indent=2)}")


@prompts.command("create")
@click.option("--name", required=True, help="Prompt name.")
@click.option("--prompt", "prompt_text", required=True, help="Prompt text (or JSON array for chat type).")
@click.option("--type", "prompt_type", default="text", type=click.Choice(["text", "chat"]))
@click.option("--labels", help="Labels (comma-separated).")
@click.option("--tags", help="Tags (comma-separated).")
@click.option("--config", "config_json", help="Config JSON string.")
@click.option("--commit-message", help="Commit message for this version.")
@click.pass_context
def prompts_create(ctx, name, prompt_text, prompt_type, labels, tags, config_json, commit_message):
    """Create a new prompt version."""
    from cli_anything.langfuse.core.prompts import create_prompt

    prompt_content = prompt_text
    if prompt_type == "chat":
        prompt_content = _parse_json_arg(prompt_text)
        if isinstance(prompt_content, str):
            click.echo("Error: Chat prompts require a JSON array of messages.", err=True)
            sys.exit(1)

    config = _parse_json_arg(config_json) if config_json else None
    label_list = labels.split(",") if labels else None
    tag_list = tags.split(",") if tags else None

    try:
        client = _make_client(ctx)
        result = create_prompt(
            client, name=name, prompt=prompt_content, prompt_type=prompt_type,
            config=config, labels=label_list, tags=tag_list,
            commit_message=commit_message,
        )
    except LangfuseAPIError as e:
        _handle_error(ctx, e)
        return

    if ctx.obj.get("json_output"):
        output_json(result)
    else:
        click.echo(f"Prompt created: {result.get('name')} v{result.get('version')}")


# ══════════════════════════════════════════════════════════════════════
# DATASETS
# ══════════════════════════════════════════════════════════════════════


@cli.group()
@click.pass_context
def datasets(ctx):
    """Manage datasets for evaluation."""
    pass


@datasets.command("list")
@click.option("--limit", default=20, help="Number of results.")
@click.option("--page", default=1, help="Page number.")
@click.pass_context
def datasets_list(ctx, limit, page):
    """List datasets."""
    from cli_anything.langfuse.core.datasets import list_datasets

    try:
        client = _make_client(ctx)
        result = list_datasets(client, page=page, limit=limit)
    except (LangfuseAPIError, ValueError) as e:
        _handle_error(ctx, e) if isinstance(e, LangfuseAPIError) else click.echo(f"Error: {e}", err=True) or sys.exit(1)
        return

    if ctx.obj.get("json_output"):
        output_json(result)
        return

    data = result.get("data", [])
    if not data:
        click.echo("No datasets found.")
        return

    headers = ["Name", "Description", "Created", "Updated"]
    rows = []
    for d in data:
        rows.append([
            truncate(d.get("name", "-"), 30),
            truncate(d.get("description", "-"), 30),
            format_timestamp(d.get("createdAt")),
            format_timestamp(d.get("updatedAt")),
        ])
    output_table(headers, rows)


@datasets.command("get")
@click.argument("dataset_name")
@click.pass_context
def datasets_get(ctx, dataset_name):
    """Get a dataset by name."""
    from cli_anything.langfuse.core.datasets import get_dataset

    try:
        client = _make_client(ctx)
        result = get_dataset(client, dataset_name)
    except LangfuseAPIError as e:
        _handle_error(ctx, e)
        return

    if ctx.obj.get("json_output"):
        output_json(result)
    else:
        click.echo(f"Dataset: {result.get('name')}")
        click.echo(f"  ID:          {result.get('id')}")
        click.echo(f"  Description: {result.get('description', '-')}")
        click.echo(f"  Created:     {format_timestamp(result.get('createdAt'))}")
        click.echo(f"  Updated:     {format_timestamp(result.get('updatedAt'))}")
        meta = result.get("metadata")
        if meta:
            click.echo(f"  Metadata:    {json.dumps(meta)}")


@datasets.command("create")
@click.option("--name", required=True, help="Dataset name.")
@click.option("--description", help="Dataset description.")
@click.option("--metadata", help="Metadata JSON string.")
@click.pass_context
def datasets_create(ctx, name, description, metadata):
    """Create a new dataset."""
    from cli_anything.langfuse.core.datasets import create_dataset

    meta = _parse_json_arg(metadata) if metadata else None

    try:
        client = _make_client(ctx)
        result = create_dataset(client, name=name, description=description, metadata=meta)
    except LangfuseAPIError as e:
        _handle_error(ctx, e)
        return

    if ctx.obj.get("json_output"):
        output_json(result)
    else:
        click.echo(f"Dataset created: {result.get('name')}")


# ── Dataset Items ────────────────────────────────────────────────────


@cli.group("dataset-items")
@click.pass_context
def dataset_items(ctx):
    """Manage dataset items."""
    pass


@dataset_items.command("list")
@click.option("--dataset", required=True, help="Dataset name.")
@click.option("--limit", default=20, help="Number of results.")
@click.option("--page", default=1, help="Page number.")
@click.pass_context
def dataset_items_list(ctx, dataset, limit, page):
    """List items in a dataset."""
    from cli_anything.langfuse.core.datasets import list_dataset_items

    try:
        client = _make_client(ctx)
        result = list_dataset_items(client, dataset_name=dataset, page=page, limit=limit)
    except (LangfuseAPIError, ValueError) as e:
        _handle_error(ctx, e) if isinstance(e, LangfuseAPIError) else click.echo(f"Error: {e}", err=True) or sys.exit(1)
        return

    if ctx.obj.get("json_output"):
        output_json(result)
        return

    data = result.get("data", [])
    if not data:
        click.echo("No dataset items found.")
        return

    headers = ["ID", "Status", "Input", "Expected Output", "Created"]
    rows = []
    for item in data:
        rows.append([
            item.get("id", "")[:12],
            item.get("status", "-"),
            truncate(json.dumps(item.get("input")), 25),
            truncate(json.dumps(item.get("expectedOutput")), 25),
            format_timestamp(item.get("createdAt")),
        ])
    output_table(headers, rows)


@dataset_items.command("create")
@click.option("--dataset", required=True, help="Dataset name.")
@click.option("--input", "input_data", required=True, help="Input data (JSON string).")
@click.option("--expected-output", help="Expected output (JSON string).")
@click.option("--metadata", help="Metadata (JSON string).")
@click.pass_context
def dataset_items_create(ctx, dataset, input_data, expected_output, metadata):
    """Create a dataset item."""
    from cli_anything.langfuse.core.datasets import create_dataset_item

    parsed_input = _parse_json_arg(input_data)
    parsed_output = _parse_json_arg(expected_output) if expected_output else None
    parsed_meta = _parse_json_arg(metadata) if metadata else None

    try:
        client = _make_client(ctx)
        result = create_dataset_item(
            client, dataset_name=dataset, input_data=parsed_input,
            expected_output=parsed_output, metadata=parsed_meta,
        )
    except LangfuseAPIError as e:
        _handle_error(ctx, e)
        return

    if ctx.obj.get("json_output"):
        output_json(result)
    else:
        click.echo(f"Dataset item created: {result.get('id')}")


@dataset_items.command("delete")
@click.argument("item_id")
@click.option("--yes", is_flag=True, help="Skip confirmation.")
@click.pass_context
def dataset_items_delete(ctx, item_id, yes):
    """Delete a dataset item."""
    from cli_anything.langfuse.core.datasets import delete_dataset_item

    if not yes:
        click.confirm(f"Delete item {item_id}?", abort=True)

    try:
        client = _make_client(ctx)
        result = delete_dataset_item(client, item_id)
    except LangfuseAPIError as e:
        _handle_error(ctx, e)
        return

    if ctx.obj.get("json_output"):
        output_json({"status": "deleted", "itemId": item_id})
    else:
        click.echo(f"Dataset item {item_id} deleted.")


# ── Dataset Runs ─────────────────────────────────────────────────────


@cli.group("dataset-runs")
@click.pass_context
def dataset_runs(ctx):
    """Manage dataset runs."""
    pass


@dataset_runs.command("list")
@click.option("--dataset", required=True, help="Dataset name.")
@click.option("--limit", default=20, help="Number of results.")
@click.option("--page", default=1, help="Page number.")
@click.pass_context
def dataset_runs_list(ctx, dataset, limit, page):
    """List runs for a dataset."""
    from cli_anything.langfuse.core.datasets import list_dataset_runs

    try:
        client = _make_client(ctx)
        result = list_dataset_runs(client, dataset_name=dataset, page=page, limit=limit)
    except (LangfuseAPIError, ValueError) as e:
        _handle_error(ctx, e) if isinstance(e, LangfuseAPIError) else click.echo(f"Error: {e}", err=True) or sys.exit(1)
        return

    if ctx.obj.get("json_output"):
        output_json(result)
        return

    data = result.get("data", [])
    if not data:
        click.echo("No dataset runs found.")
        return

    headers = ["Name", "Description", "Created", "Updated"]
    rows = []
    for r in data:
        rows.append([
            truncate(r.get("name", "-"), 25),
            truncate(r.get("description", "-"), 25),
            format_timestamp(r.get("createdAt")),
            format_timestamp(r.get("updatedAt")),
        ])
    output_table(headers, rows)


@dataset_runs.command("get")
@click.option("--dataset", required=True, help="Dataset name.")
@click.argument("run_name")
@click.pass_context
def dataset_runs_get(ctx, dataset, run_name):
    """Get a dataset run by name."""
    from cli_anything.langfuse.core.datasets import get_dataset_run

    try:
        client = _make_client(ctx)
        result = get_dataset_run(client, dataset, run_name)
    except LangfuseAPIError as e:
        _handle_error(ctx, e)
        return

    if ctx.obj.get("json_output"):
        output_json(result)
    else:
        click.echo(f"Run: {result.get('name')}")
        click.echo(f"  Dataset:     {result.get('datasetName')}")
        click.echo(f"  Description: {result.get('description', '-')}")
        click.echo(f"  Created:     {format_timestamp(result.get('createdAt'))}")
        items = result.get("datasetRunItems", [])
        click.echo(f"  Items:       {len(items)}")


# ══════════════════════════════════════════════════════════════════════
# SESSIONS
# ══════════════════════════════════════════════════════════════════════


@cli.group()
@click.pass_context
def sessions(ctx):
    """Manage sessions."""
    pass


@sessions.command("list")
@click.option("--limit", default=20, help="Number of results.")
@click.option("--page", default=1, help="Page number.")
@click.pass_context
def sessions_list(ctx, limit, page):
    """List sessions."""
    from cli_anything.langfuse.core.sessions import list_sessions

    try:
        client = _make_client(ctx)
        result = list_sessions(client, page=page, limit=limit)
    except (LangfuseAPIError, ValueError) as e:
        _handle_error(ctx, e) if isinstance(e, LangfuseAPIError) else click.echo(f"Error: {e}", err=True) or sys.exit(1)
        return

    if ctx.obj.get("json_output"):
        output_json(result)
        return

    data = result.get("data", [])
    if not data:
        click.echo("No sessions found.")
        return

    headers = ["ID", "Created", "Project"]
    rows = []
    for s in data:
        rows.append([
            s.get("id", "")[:20],
            format_timestamp(s.get("createdAt")),
            s.get("projectId", "")[:12],
        ])
    output_table(headers, rows)


@sessions.command("get")
@click.argument("session_id")
@click.pass_context
def sessions_get(ctx, session_id):
    """Get a session with its traces."""
    from cli_anything.langfuse.core.sessions import get_session

    try:
        client = _make_client(ctx)
        result = get_session(client, session_id)
    except LangfuseAPIError as e:
        _handle_error(ctx, e)
        return

    if ctx.obj.get("json_output"):
        output_json(result)
    else:
        click.echo(f"Session: {result.get('id')}")
        click.echo(f"  Created: {format_timestamp(result.get('createdAt'))}")
        traces = result.get("traces", [])
        click.echo(f"  Traces:  {len(traces)}")
        for t in traces[:10]:
            click.echo(f"    - {t.get('id', '')[:12]}  {t.get('name', '-'):25s}  {format_timestamp(t.get('timestamp'))}")


# ══════════════════════════════════════════════════════════════════════
# MODELS
# ══════════════════════════════════════════════════════════════════════


@cli.group()
@click.pass_context
def models(ctx):
    """Manage model definitions and pricing."""
    pass


@models.command("list")
@click.option("--limit", default=20, help="Number of results.")
@click.option("--page", default=1, help="Page number.")
@click.pass_context
def models_list(ctx, limit, page):
    """List models."""
    from cli_anything.langfuse.core.models import list_models

    try:
        client = _make_client(ctx)
        result = list_models(client, page=page, limit=limit)
    except (LangfuseAPIError, ValueError) as e:
        _handle_error(ctx, e) if isinstance(e, LangfuseAPIError) else click.echo(f"Error: {e}", err=True) or sys.exit(1)
        return

    if ctx.obj.get("json_output"):
        output_json(result)
        return

    data = result.get("data", [])
    if not data:
        click.echo("No models found.")
        return

    headers = ["ID", "Model Name", "Match Pattern", "Unit", "Managed"]
    rows = []
    for m in data:
        rows.append([
            m.get("id", "")[:12],
            truncate(m.get("modelName", "-"), 25),
            truncate(m.get("matchPattern", "-"), 20),
            m.get("unit", "-"),
            str(m.get("isLangfuseManaged", False)),
        ])
    output_table(headers, rows)


@models.command("get")
@click.argument("model_id")
@click.pass_context
def models_get(ctx, model_id):
    """Get a model by ID."""
    from cli_anything.langfuse.core.models import get_model

    try:
        client = _make_client(ctx)
        result = get_model(client, model_id)
    except LangfuseAPIError as e:
        _handle_error(ctx, e)
        return

    if ctx.obj.get("json_output"):
        output_json(result)
    else:
        click.echo(f"Model: {result.get('modelName')}")
        click.echo(f"  ID:            {result.get('id')}")
        click.echo(f"  Match Pattern: {result.get('matchPattern')}")
        click.echo(f"  Unit:          {result.get('unit')}")
        click.echo(f"  Managed:       {result.get('isLangfuseManaged')}")
        click.echo(f"  Input Price:   {result.get('inputPrice', '-')}")
        click.echo(f"  Output Price:  {result.get('outputPrice', '-')}")


@models.command("create")
@click.option("--name", required=True, help="Model name.")
@click.option("--match-pattern", required=True, help="Regex match pattern.")
@click.option("--unit", default="TOKENS", type=click.Choice(["TOKENS", "CHARACTERS", "MILLISECONDS", "SECONDS", "IMAGES", "REQUESTS"]))
@click.option("--input-price", type=float, help="Input price per unit.")
@click.option("--output-price", type=float, help="Output price per unit.")
@click.option("--total-price", type=float, help="Total price per unit.")
@click.pass_context
def models_create(ctx, name, match_pattern, unit, input_price, output_price, total_price):
    """Create a custom model definition."""
    from cli_anything.langfuse.core.models import create_model

    try:
        client = _make_client(ctx)
        result = create_model(
            client, model_name=name, match_pattern=match_pattern,
            unit=unit, input_price=input_price, output_price=output_price,
            total_price=total_price,
        )
    except LangfuseAPIError as e:
        _handle_error(ctx, e)
        return

    if ctx.obj.get("json_output"):
        output_json(result)
    else:
        click.echo(f"Model created: {result.get('id')}")


@models.command("delete")
@click.argument("model_id")
@click.option("--yes", is_flag=True, help="Skip confirmation.")
@click.pass_context
def models_delete(ctx, model_id, yes):
    """Delete a model."""
    from cli_anything.langfuse.core.models import delete_model

    if not yes:
        click.confirm(f"Delete model {model_id}?", abort=True)

    try:
        client = _make_client(ctx)
        result = delete_model(client, model_id)
    except LangfuseAPIError as e:
        _handle_error(ctx, e)
        return

    if ctx.obj.get("json_output"):
        output_json({"status": "deleted", "modelId": model_id})
    else:
        click.echo(f"Model {model_id} deleted.")


# ══════════════════════════════════════════════════════════════════════
# COMMENTS
# ══════════════════════════════════════════════════════════════════════


@cli.group()
@click.pass_context
def comments(ctx):
    """Manage comments on traces, observations, and sessions."""
    pass


@comments.command("list")
@click.option("--limit", default=20, help="Number of results.")
@click.option("--page", default=1, help="Page number.")
@click.option("--object-type", help="Filter by object type (TRACE, OBSERVATION, SESSION, PROMPT).")
@click.option("--object-id", help="Filter by object ID.")
@click.pass_context
def comments_list(ctx, limit, page, object_type, object_id):
    """List comments."""
    from cli_anything.langfuse.core.comments import list_comments

    try:
        client = _make_client(ctx)
        result = list_comments(client, page=page, limit=limit,
                               object_type=object_type, object_id=object_id)
    except (LangfuseAPIError, ValueError) as e:
        _handle_error(ctx, e) if isinstance(e, LangfuseAPIError) else click.echo(f"Error: {e}", err=True) or sys.exit(1)
        return

    if ctx.obj.get("json_output"):
        output_json(result)
        return

    data = result.get("data", [])
    if not data:
        click.echo("No comments found.")
        return

    headers = ["ID", "Object Type", "Object ID", "Content", "Created"]
    rows = []
    for c in data:
        rows.append([
            c.get("id", "")[:12],
            c.get("objectType", "-"),
            c.get("objectId", "")[:12],
            truncate(c.get("content", "-"), 30),
            format_timestamp(c.get("createdAt")),
        ])
    output_table(headers, rows)


@comments.command("create")
@click.option("--object-type", required=True, type=click.Choice(["TRACE", "OBSERVATION", "SESSION", "PROMPT"]))
@click.option("--object-id", required=True, help="Object ID to comment on.")
@click.option("--content", required=True, help="Comment content (markdown).")
@click.pass_context
def comments_create(ctx, object_type, object_id, content):
    """Create a comment on an object."""
    from cli_anything.langfuse.core.comments import create_comment

    try:
        client = _make_client(ctx)
        result = create_comment(client, object_type=object_type, object_id=object_id, content=content)
    except LangfuseAPIError as e:
        _handle_error(ctx, e)
        return

    if ctx.obj.get("json_output"):
        output_json(result)
    else:
        click.echo(f"Comment created: {result.get('id')}")


# ══════════════════════════════════════════════════════════════════════
# METRICS
# ══════════════════════════════════════════════════════════════════════


@cli.group()
@click.pass_context
def metrics(ctx):
    """Query usage metrics."""
    pass


@metrics.command("daily")
@click.option("--limit", default=50, help="Number of results.")
@click.option("--page", default=1, help="Page number.")
@click.option("--trace-name", help="Filter by trace name.")
@click.option("--user-id", help="Filter by user ID.")
@click.option("--tags", help="Tags (comma-separated).")
@click.option("--from", "from_ts", help="From timestamp (ISO).")
@click.option("--to", "to_ts", help="To timestamp (ISO).")
@click.pass_context
def metrics_daily(ctx, limit, page, trace_name, user_id, tags, from_ts, to_ts):
    """Get daily usage metrics."""
    from cli_anything.langfuse.core.metrics import get_daily_metrics

    tag_list = tags.split(",") if tags else None

    try:
        client = _make_client(ctx)
        result = get_daily_metrics(
            client, page=page, limit=limit, trace_name=trace_name,
            user_id=user_id, tags=tag_list,
            from_timestamp=from_ts, to_timestamp=to_ts,
        )
    except (LangfuseAPIError, ValueError) as e:
        _handle_error(ctx, e) if isinstance(e, LangfuseAPIError) else click.echo(f"Error: {e}", err=True) or sys.exit(1)
        return

    if ctx.obj.get("json_output"):
        output_json(result)
        return

    data = result.get("data", [])
    if not data:
        click.echo("No metrics found.")
        return

    headers = ["Date", "Trace Name", "Count", "Total Cost", "Usage"]
    rows = []
    for m in data:
        rows.append([
            m.get("date", "-"),
            truncate(m.get("traceName", "-"), 20),
            str(m.get("countTraces", "-")),
            format_cost(m.get("totalCost")),
            str(m.get("usage", "-")),
        ])
    output_table(headers, rows)


# ══════════════════════════════════════════════════════════════════════
# PROJECTS & HEALTH
# ══════════════════════════════════════════════════════════════════════


@cli.command("projects")
@click.pass_context
def projects_current(ctx):
    """Get current project info."""
    from cli_anything.langfuse.core.projects import get_projects

    try:
        client = _make_client(ctx)
        result = get_projects(client)
    except LangfuseAPIError as e:
        _handle_error(ctx, e)
        return

    if ctx.obj.get("json_output"):
        output_json(result)
    else:
        data = result.get("data", [result]) if isinstance(result, dict) else result
        if isinstance(data, dict):
            data = [data]
        for p in data:
            click.echo(f"Project: {p.get('name', '-')}")
            click.echo(f"  ID: {p.get('id', '-')}")


@cli.command("health")
@click.pass_context
def health_check(ctx):
    """Check Langfuse API health status."""
    from cli_anything.langfuse.core.projects import get_health

    try:
        # Health check doesn't need auth but we still construct the client
        # to get the base_url
        creds = resolve_credentials(
            public_key=ctx.obj.get("public_key") or "check",
            secret_key=ctx.obj.get("secret_key") or "check",
            base_url=ctx.obj.get("base_url"),
            profile=ctx.obj.get("profile"),
        )
        client = LangfuseClient(
            public_key=creds["public_key"],
            secret_key=creds["secret_key"],
            base_url=creds["base_url"],
        )
        result = get_health(client)
    except LangfuseAPIError as e:
        if ctx.obj.get("json_output"):
            output_json({"status": "error", "message": str(e)})
        else:
            click.echo(f"Health check failed: {e}", err=True)
        sys.exit(1)
        return

    if ctx.obj.get("json_output"):
        output_json(result)
    else:
        status = result.get("status", "unknown")
        icon = "OK" if status.upper() == "OK" else "DEGRADED"
        click.echo(f"Langfuse API: {icon}")
        click.echo(f"  Base URL: {creds['base_url']}")
        click.echo(f"  Version:  {result.get('version', '-')}")


# ══════════════════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════════════════


@cli.group()
@click.pass_context
def config(ctx):
    """Manage CLI configuration profiles."""
    pass


@config.command("set")
@click.option("--profile", "profile_name", default="default", help="Profile name.")
@click.option("--public-key", help="Langfuse public key.")
@click.option("--secret-key", help="Langfuse secret key.")
@click.option("--base-url", help="Langfuse base URL.")
@click.option("--activate", is_flag=True, help="Set as active profile.")
@click.pass_context
def config_set(ctx, profile_name, public_key, secret_key, base_url, activate):
    """Set configuration for a profile."""
    result = set_profile(profile_name, public_key=public_key,
                         secret_key=secret_key, base_url=base_url)
    if activate:
        set_active_profile(profile_name)

    if ctx.obj.get("json_output"):
        output_json({"profile": profile_name, "updated": True})
    else:
        click.echo(f"Profile '{profile_name}' updated.")
        if activate:
            click.echo(f"Active profile set to '{profile_name}'.")


@config.command("show")
@click.pass_context
def config_show(ctx):
    """Show all profiles."""
    profiles = list_profiles()

    if ctx.obj.get("json_output"):
        output_json(profiles)
        return

    if not profiles:
        click.echo("No profiles configured.")
        click.echo("Run: cli-anything-langfuse config set --public-key pk-lf-... --secret-key sk-lf-...")
        return

    headers = ["Profile", "Active", "Base URL", "Public Key", "Has Secret"]
    rows = []
    for p in profiles:
        rows.append([
            p["name"],
            "*" if p["active"] else "",
            p["base_url"],
            p["public_key"],
            "yes" if p["has_secret"] else "no",
        ])
    output_table(headers, rows)


@config.command("activate")
@click.argument("profile_name")
@click.pass_context
def config_activate(ctx, profile_name):
    """Set the active profile."""
    set_active_profile(profile_name)

    if ctx.obj.get("json_output"):
        output_json({"active_profile": profile_name})
    else:
        click.echo(f"Active profile set to '{profile_name}'.")


@config.command("delete")
@click.argument("profile_name")
@click.option("--yes", is_flag=True, help="Skip confirmation.")
@click.pass_context
def config_delete(ctx, profile_name, yes):
    """Delete a profile."""
    if not yes:
        click.confirm(f"Delete profile '{profile_name}'?", abort=True)

    if delete_profile(profile_name):
        if ctx.obj.get("json_output"):
            output_json({"status": "deleted", "profile": profile_name})
        else:
            click.echo(f"Profile '{profile_name}' deleted.")
    else:
        if ctx.obj.get("json_output"):
            output_json({"status": "not_found", "profile": profile_name})
        else:
            click.echo(f"Profile '{profile_name}' not found.", err=True)


# ══════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════


def main():
    cli(auto_envvar_prefix="LANGFUSE")


if __name__ == "__main__":
    main()
