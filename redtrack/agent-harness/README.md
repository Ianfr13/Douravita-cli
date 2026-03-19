# cli-anything-redtrack

A CLI harness for [RedTrack](https://redtrack.io), a performance marketing
tracking platform. Manage campaigns, offers, traffic channels, landers,
conversions, costs, reports, and automation rules via the RedTrack REST API.

## Installation

```bash
# From source (recommended for development)
cd redtrack/agent-harness
pip install -e .

# Or install from PyPI (when published)
pip install cli-anything-redtrack
```

**Requirements:**
- Python 3.10+
- A RedTrack account and API key

## Authentication

Set your RedTrack API key as an environment variable:

```bash
export REDTRACK_API_KEY=your_api_key_here
```

Or pass it per-command:

```bash
cli-anything-redtrack --api-key YOUR_KEY campaign list
```

Your API key is available in the RedTrack dashboard under Account → API.

## Quick Start

```bash
# Show help
cli-anything-redtrack --help

# Start interactive REPL
cli-anything-redtrack

# List campaigns (human-readable)
cli-anything-redtrack campaign list

# List campaigns (JSON for scripts/agents)
cli-anything-redtrack --json campaign list

# Get account info
cli-anything-redtrack account info
```

## Command Reference

### Global Options

| Option | Description |
|--------|-------------|
| `--json` | Output as JSON (all commands) |
| `--api-key KEY` | Override REDTRACK_API_KEY |
| `--base-url URL` | Override API base URL (default: https://api.redtrack.io) |

### account

```bash
cli-anything-redtrack account info
```

### campaign

```bash
cli-anything-redtrack campaign list [--date-from YYYY-MM-DD] [--date-to YYYY-MM-DD] [--limit N] [--offset N]
cli-anything-redtrack campaign get <id>
cli-anything-redtrack campaign create --name NAME --traffic-channel-id ID [--domain DOMAIN] [--cost-type TYPE] [--cost-value VALUE]
cli-anything-redtrack campaign update <id> [--name NAME] [--status STATUS] [--cost-type TYPE] [--cost-value VALUE]
cli-anything-redtrack campaign delete <id>
cli-anything-redtrack campaign links <id>
```

### offer

```bash
cli-anything-redtrack offer list
cli-anything-redtrack offer get <id>
cli-anything-redtrack offer create --name NAME [--offer-source-id ID] [--url URL] [--payout AMOUNT]
cli-anything-redtrack offer update <id> [--name NAME] [--url URL] [--payout AMOUNT] [--status STATUS]
cli-anything-redtrack offer delete <id>
```

### offer-source

```bash
cli-anything-redtrack offer-source list
cli-anything-redtrack offer-source get <id>
cli-anything-redtrack offer-source create --name NAME [--postback-url URL] [--click-id-param PARAM] [--payout-param PARAM]
cli-anything-redtrack offer-source update <id> [--name NAME] [--postback-url URL]
cli-anything-redtrack offer-source delete <id>
```

### traffic

```bash
cli-anything-redtrack traffic list
cli-anything-redtrack traffic get <id>
cli-anything-redtrack traffic create --name NAME [--template TEMPLATE]
cli-anything-redtrack traffic update <id> [--name NAME] [--status STATUS]
cli-anything-redtrack traffic delete <id>
```

### lander

```bash
cli-anything-redtrack lander list
cli-anything-redtrack lander get <id>
cli-anything-redtrack lander create --name NAME [--url URL] [--tracking-type TYPE]
cli-anything-redtrack lander update <id> [--name NAME] [--url URL] [--status STATUS]
cli-anything-redtrack lander delete <id>
```

### conversion

```bash
cli-anything-redtrack conversion list [--date-from DATE] [--date-to DATE] [--campaign-id ID] [--status STATUS]
cli-anything-redtrack conversion upload --click-id ID [--status STATUS] [--payout AMOUNT] [--type TYPE]
cli-anything-redtrack conversion types
```

### report

```bash
cli-anything-redtrack report general [--date-from DATE] [--date-to DATE] [--group-by FIELD] [--filters EXPR]
cli-anything-redtrack report campaigns [--date-from DATE] [--date-to DATE]
cli-anything-redtrack report clicks [--date-from DATE] [--date-to DATE] [--campaign-id ID]
```

### cost

```bash
cli-anything-redtrack cost list [--date-from DATE] [--date-to DATE]
cli-anything-redtrack cost update --campaign-id ID --cost AMOUNT [--date DATE]
cli-anything-redtrack cost auto
```

### rule

```bash
cli-anything-redtrack rule list
cli-anything-redtrack rule get <id>
cli-anything-redtrack rule create --name NAME [--condition COND] [--action ACTION]
cli-anything-redtrack rule update <id> [--status active|paused] [--name NAME]
cli-anything-redtrack rule delete <id>
```

### domain

```bash
cli-anything-redtrack domain list
cli-anything-redtrack domain add --domain DOMAIN
```

### session

```bash
cli-anything-redtrack session status
```

## Interactive REPL

Run without arguments to enter the interactive REPL:

```bash
cli-anything-redtrack
```

The REPL provides:
- Persistent command history (`~/.cli-anything-redtrack/history`)
- Auto-suggest from history
- `help` command listing
- `quit` / `exit` to leave

## Testing

```bash
cd redtrack/agent-harness

# Unit tests (no API key needed)
python -m pytest cli_anything/redtrack/tests/test_core.py -v

# E2E tests (requires API key)
REDTRACK_API_KEY=your_key python -m pytest cli_anything/redtrack/tests/test_full_e2e.py -v

# All tests
python -m pytest cli_anything/redtrack/tests/ -v
```

## For AI Agents

When using this CLI programmatically from an agent:

1. Always use `--json` for structured output
2. Check exit code: 0 = success, non-zero = error
3. On error, the JSON output contains `{"error": "...", "type": "..."}`
4. Set `REDTRACK_API_KEY` in the environment before invoking
5. Use `session status` to verify configuration

Example agent workflow:

```bash
# Verify connection
cli-anything-redtrack --json account info

# Get all campaigns
cli-anything-redtrack --json campaign list

# Create a new campaign
cli-anything-redtrack --json campaign create \
    --name "Q1 Push Campaign" \
    --traffic-channel-id 5 \
    --cost-type cpc \
    --cost-value 0.25
```

## Architecture

See [REDTRACK.md](REDTRACK.md) for full architecture documentation,
API endpoint mapping, authentication details, and design decisions.
