# cli-anything-redtrack

A CLI harness for [RedTrack](https://redtrack.io), a performance marketing tracking platform. Wraps the RedTrack REST API (`https://api.redtrack.io`) so campaigns, offers, traffic channels, landers, conversions, costs, reports, automation rules, domains, and dictionary lookups can all be driven from the command line or from an AI agent.

## Installation

```bash
cd redtrack/agent-harness
pip install -e .
cli-anything-redtrack --help
```

**Requirements:** Python 3.10+, a RedTrack account and API key.

## Authentication

```bash
export REDTRACK_API_KEY=your_api_key_here
```

Your key is available in the RedTrack dashboard under Account → API. You can also pass it per-invocation with `--api-key KEY`.

## Quick Examples

```bash
# List all campaigns (human-readable table)
cli-anything-redtrack campaign list

# List campaigns as JSON, filtered by date
cli-anything-redtrack --json campaign list --date-from 2024-01-01 --date-to 2024-01-31

# Create a campaign
cli-anything-redtrack --json campaign create \
    --name "Q1 Push" --traffic-channel-id 5 --cost-type cpc --cost-value 0.25

# Bulk-pause multiple campaigns
cli-anything-redtrack --json campaign update-statuses \
    --ids c1 --ids c2 --status paused

# General performance report grouped by country
cli-anything-redtrack --json report general \
    --date-from 2024-01-01 --date-to 2024-01-31 --group-by country

# Look up all country codes (no API key required)
cli-anything-redtrack --json lookup get countries
```

## Command Reference

### Global options

| Option | Description |
|--------|-------------|
| `--json` | Machine-readable JSON output (all commands) |
| `--api-key KEY` | Override `REDTRACK_API_KEY` |
| `--base-url URL` | Override API base URL (default: `https://api.redtrack.io`) |

### account

| Command | Endpoint |
|---------|----------|
| `account info` | `GET /user` |

### campaign

| Command | Endpoint |
|---------|----------|
| `campaign list [--date-from DATE] [--date-to DATE] [--page N] [--per N]` | `GET /campaigns` |
| `campaign list-v2` | `GET /campaigns/v2` |
| `campaign get <id>` | `GET /campaigns/<id>` |
| `campaign create --name NAME --traffic-channel-id ID [--domain D] [--cost-type T] [--cost-value V]` | `POST /campaigns` |
| `campaign update <id> [--name NAME] [--status STATUS] [--cost-type T] [--cost-value V]` | `PUT /campaigns/<id>` |
| `campaign update-statuses --ids ID [--ids ID ...] --status STATUS` | `PATCH /campaigns/status` |
| `campaign delete <id> --confirm` | `PATCH /campaigns/status` (sets status to `archived`) |
| `campaign links <id>` | `GET /campaigns/<id>` (extracts tracking URLs) |

### offer

| Command | Endpoint |
|---------|----------|
| `offer list` | `GET /offers` |
| `offer get <id>` | `GET /offers/<id>` |
| `offer create --name NAME [--url URL] [--payout AMOUNT] [--network-id ID]` | `POST /offers` |
| `offer update <id> [--name NAME] [--url URL] [--payout AMOUNT] [--status STATUS]` | `PUT /offers/<id>` |
| `offer update-statuses --ids ID [--ids ID ...] --status STATUS` | `PATCH /offers/status` |
| `offer export [--status STATUS]` | `GET /offers/export` |
| `offer delete <id>` | `DELETE /offers/<id>` |

### offer-source

| Command | Endpoint |
|---------|----------|
| `offer-source list` | `GET /offer_sources` |
| `offer-source get <id>` | `GET /offer_sources/<id>` |
| `offer-source create --name NAME [--postback-url URL]` | `POST /offer_sources` |
| `offer-source update <id> [--name NAME] [--postback-url URL]` | `PUT /offer_sources/<id>` |
| `offer-source delete <id>` | `DELETE /offer_sources/<id>` |

### traffic

| Command | Endpoint |
|---------|----------|
| `traffic list` | `GET /traffic_channels` |
| `traffic get <id>` | `GET /traffic_channels/<id>` |
| `traffic create --name NAME [--template TEMPLATE]` | `POST /traffic_channels` |
| `traffic update <id> [--name NAME] [--status STATUS]` | `PUT /traffic_channels/<id>` |
| `traffic delete <id>` | `DELETE /traffic_channels/<id>` |

### lander

| Command | Endpoint |
|---------|----------|
| `lander list` | `GET /landers` |
| `lander get <id>` | `GET /landers/<id>` |
| `lander create --name NAME [--url URL]` | `POST /landers` |
| `lander update <id> [--name NAME] [--url URL] [--status STATUS]` | `PUT /landers/<id>` |
| `lander delete <id>` | `DELETE /landers/<id>` |

### conversion

| Command | Endpoint |
|---------|----------|
| `conversion list [--date-from DATE] [--date-to DATE] [--campaign-id ID] [--status STATUS]` | `GET /conversions` |
| `conversion upload --click-id ID [--status STATUS] [--payout AMOUNT] [--type TYPE]` | `POST /conversions` |
| `conversion export --date-from DATE --date-to DATE` | `GET /conversions/export` |
| `conversion types` | static list (no API call) |

### report

| Command | Endpoint |
|---------|----------|
| `report general [--date-from DATE] [--date-to DATE] [--group-by FIELD]` | `GET /report` |
| `report campaigns [--date-from DATE] [--date-to DATE]` | `GET /report/campaigns` |
| `report clicks [--date-from DATE] [--date-to DATE] [--campaign-id ID]` | `GET /clicks` |
| `report stream [--date-from DATE] [--date-to DATE]` | `GET /report` with `group_by=stream` |

### cost

| Command | Endpoint / Note |
|---------|----------------|
| `cost list [--date-from DATE] [--date-to DATE]` | `GET /report` (cost data is extracted from the report endpoint; there is no dedicated `/costs` endpoint in the RedTrack API) |

### rule

| Command | Endpoint |
|---------|----------|
| `rule list` | `GET /rules` |
| `rule get <id>` | `GET /rules/<id>` |
| `rule create --name NAME [--condition COND] [--action ACTION]` | `POST /rules` |
| `rule update <id> [--status active\|paused] [--name NAME]` | `PATCH /rules/<id>` |
| `rule delete <id>` | `DELETE /rules/<id>` |

### domain

| Command | Endpoint |
|---------|----------|
| `domain list` | `GET /domains` |
| `domain add --domain DOMAIN` | `POST /domains` |
| `domain update <id> --domain DOMAIN` | `PUT /domains/<id>` |
| `domain delete <id>` | `DELETE /domains/<id>` |
| `domain regenerate-ssl <id>` | `POST /domains/regenerated_free_ssl/<id>` |

### lookup

| Command | Endpoint / Note |
|---------|----------------|
| `lookup list` | Static list of 14 available dictionary keys |
| `lookup get <key>` | `GET /<key>` — no API key required for most lookups (e.g. `countries`, `browsers`, `os`) |

### session

```bash
cli-anything-redtrack session status
```

Shows the current API key (masked) and base URL.

## Interactive REPL

Run without arguments to enter the interactive REPL:

```bash
cli-anything-redtrack
```

Provides persistent history, auto-suggest, and `quit` / `exit` to leave.

## API Coverage Notes

- All major entity endpoints (campaigns, offers, landers, traffic channels, conversions, rules, domains) have full CRUD coverage.
- Bulk status updates use `PATCH /<resource>/status` with an `ids` array.
- `campaign delete` archives via `PATCH /campaigns/status` rather than a hard DELETE.
- Cost data is retrieved from `GET /report`; the RedTrack API does not expose a dedicated `/costs` endpoint.
- Dictionary lookups (`/countries`, `/browsers`, etc.) do not require an API key.

## Running Tests

```bash
cd redtrack/agent-harness

# Unit tests — no API key needed (139 tests)
python3 -m pytest cli_anything/redtrack/tests/test_core.py -v

# E2E tests — requires REDTRACK_API_KEY (25 tests)
REDTRACK_API_KEY=your_key python3 -m pytest cli_anything/redtrack/tests/test_full_e2e.py -v

# All tests including subprocess CLI tests
CLI_ANYTHING_FORCE_INSTALLED=1 REDTRACK_API_KEY=your_key \
    python3 -m pytest cli_anything/redtrack/tests/ -v -s
```

See [`cli_anything/redtrack/tests/TEST.md`](cli_anything/redtrack/tests/TEST.md) for the full test inventory and known gaps.

## Architecture

See [REDTRACK.md](REDTRACK.md) for the full architecture SOP, endpoint mapping, and design decisions.
For AI agent usage, the SKILL.md at `cli_anything/redtrack/skills/SKILL.md` is the authoritative command reference.
