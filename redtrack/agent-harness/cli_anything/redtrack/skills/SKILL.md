---
name: cli-anything-redtrack
description: >-
  Performance marketing tracking CLI for RedTrack — manage campaigns, offers,
  traffic channels, landers, conversions, costs, reports, and automation rules
  via the RedTrack REST API.
---

# cli-anything-redtrack

A stateful CLI for the RedTrack performance marketing tracking platform.
Provides full access to the RedTrack REST API for campaign management,
conversion tracking, reporting, and marketing automation.

## Setup

```bash
# Set your API key
export REDTRACK_API_KEY=your_api_key

# Install
pip install cli-anything-redtrack
# or from source:
pip install -e .
```

## Usage

```bash
# Enter interactive REPL (no subcommand)
cli-anything-redtrack

# One-shot commands
cli-anything-redtrack account info
cli-anything-redtrack campaign list

# JSON output for agent/script consumption
cli-anything-redtrack --json campaign list
cli-anything-redtrack --json campaign get 12345

# Override API key on command line
cli-anything-redtrack --api-key YOUR_KEY account info

# Override base URL (e.g., for proxies or testing)
cli-anything-redtrack --base-url https://custom.api.io campaign list
```

## Command Groups

### account
Account information.

| Command | Description |
|---------|-------------|
| `info` | Show RedTrack account details (GET /user) |

### campaign
Campaign management.

| Command | Description |
|---------|-------------|
| `list` | List campaigns (--date-from, --date-to, --limit, --offset) |
| `get <id>` | Get a campaign by ID |
| `create` | Create a campaign (--name required, --traffic-channel-id required) |
| `update <id>` | Update a campaign (--name, --status, --cost-type, --cost-value) |
| `delete <id>` | Archive/delete a campaign |
| `links <id>` | Show tracking links for a campaign |

### offer
Offer management.

| Command | Description |
|---------|-------------|
| `list` | List all offers |
| `get <id>` | Get an offer by ID |
| `create` | Create an offer (--name required, --url, --payout, --offer-source-id) |
| `update <id>` | Update an offer (--name, --url, --payout, --status) |
| `delete <id>` | Delete an offer |

### offer-source
Affiliate network management.

| Command | Description |
|---------|-------------|
| `list` | List all offer sources |
| `get <id>` | Get an offer source by ID |
| `create` | Create an offer source (--name, --postback-url, --click-id-param, --payout-param) |
| `update <id>` | Update an offer source |
| `delete <id>` | Delete an offer source |

### traffic
Traffic channel management.

| Command | Description |
|---------|-------------|
| `list` | List all traffic channels |
| `get <id>` | Get a traffic channel by ID |
| `create` | Create a traffic channel (--name, --template) |
| `update <id>` | Update a traffic channel (--name, --status) |
| `delete <id>` | Delete a traffic channel |

### lander
Landing page management.

| Command | Description |
|---------|-------------|
| `list` | List all landers |
| `get <id>` | Get a lander by ID |
| `create` | Create a lander (--name, --url, --tracking-type) |
| `update <id>` | Update a lander (--name, --url, --tracking-type, --status) |
| `delete <id>` | Delete a lander |

### conversion
Conversion tracking.

| Command | Description |
|---------|-------------|
| `list` | List conversions (--date-from, --date-to, --campaign-id, --status) |
| `upload` | Upload a conversion (--click-id required, --status, --payout, --type) |
| `types` | List available conversion types |

### report
Performance reporting.

| Command | Description |
|---------|-------------|
| `general` | General report (--date-from, --date-to, --group-by, --filters) |
| `campaigns` | Campaigns report (--date-from, --date-to) |
| `clicks` | Click logs (--date-from, --date-to, --campaign-id) |

### cost
Cost tracking.

| Command | Description |
|---------|-------------|
| `list` | List cost records (--date-from, --date-to) |
| `update` | Manually update cost (--campaign-id, --cost, --date) |
| `auto` | Show auto-cost update status |

### rule
Automation rule management.

| Command | Description |
|---------|-------------|
| `list` | List all automation rules |
| `get <id>` | Get a rule by ID |
| `create` | Create a rule (--name, --condition, --action) |
| `update <id>` | Update a rule (--status, --name) |
| `delete <id>` | Delete a rule |

### domain
Custom tracking domain management.

| Command | Description |
|---------|-------------|
| `list` | List custom tracking domains |
| `add` | Add a custom domain (--domain required) |

### session
Session inspection.

| Command | Description |
|---------|-------------|
| `status` | Show current session (masked API key, base URL) |

## Examples

```bash
# List all campaigns as JSON
cli-anything-redtrack --json campaign list

# Create a campaign
cli-anything-redtrack campaign create \
    --name "My Campaign" \
    --traffic-channel-id 5 \
    --cost-type cpc \
    --cost-value 0.50

# Get campaign tracking links
cli-anything-redtrack campaign links 12345

# List offers
cli-anything-redtrack offer list

# Create an offer
cli-anything-redtrack offer create \
    --name "My Offer" \
    --url "https://example.com/offer?clickid={clickid}" \
    --payout 10.00

# Upload a conversion
cli-anything-redtrack conversion upload \
    --click-id "abc123def456" \
    --status approved \
    --payout 10.00

# Get a performance report
cli-anything-redtrack --json report general \
    --date-from 2024-01-01 \
    --date-to 2024-01-31 \
    --group-by campaign

# Create an automation rule
cli-anything-redtrack rule create \
    --name "Pause low ROI" \
    --condition '{"metric":"roi","op":"<","value":0}' \
    --action "pause_campaign"

# Check session
cli-anything-redtrack session status
```

## For AI Agents

When using this CLI programmatically:

1. **Always use `--json` flag** for parseable output
2. **Check return codes** — 0 for success, non-zero for errors
3. **Parse stderr** for error messages on failure
4. **Set REDTRACK_API_KEY** before invoking — or use `--api-key`
5. **Session status** is not persistent between invocations (stateless CLI)

## Output Formats

All commands support dual output:

- **Human-readable** (default): Formatted tables and key-value pairs
- **Machine-readable** (`--json` flag): Structured JSON for script/agent use

## Version

1.0.0
