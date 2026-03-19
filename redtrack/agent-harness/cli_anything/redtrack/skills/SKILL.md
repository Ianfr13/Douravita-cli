---
name: cli-anything-redtrack
description: >-
  Performance marketing tracking CLI for RedTrack — manage campaigns, offers,
  traffic channels, landers, conversions, costs, reports, and automation rules
  via the RedTrack REST API.
---

# cli-anything-redtrack

A CLI for the RedTrack performance marketing tracking platform.
Wraps the RedTrack REST API (https://api.redtrack.io).

## Installation

pip install -e redtrack/agent-harness

## Authentication

Set the REDTRACK_API_KEY environment variable:
  export REDTRACK_API_KEY=your_api_key

Or pass per-command: cli-anything-redtrack --api-key YOUR_KEY <command>

Note: The API key must be sent as a query parameter (?api_key=). The CLI handles this automatically.

## Usage

  cli-anything-redtrack [--json] [--api-key KEY] [--base-url URL] <group> <subcommand> [OPTIONS]

Use --json for machine-readable output (recommended for agent use).

## Command Reference

### account
  account info                        Get account settings and profile (GET /me/settings)

### campaign
  campaign list                       List campaigns (GET /campaigns)
    --date-from DATE                  Filter start date (YYYY-MM-DD)
    --date-to DATE                    Filter end date (YYYY-MM-DD)
    --page INT                        Page number (default: 1)
    --per INT                         Results per page (default: 100)
  campaign list-v2                    List campaigns via lighter v2 endpoint (no total_stat)
    --date-from DATE
    --date-to DATE
    --page INT
    --per INT
  campaign get <ID>                   Get a single campaign
  campaign create                     Create a new campaign
    --name TEXT (required)
    --traffic-channel-id TEXT (required)
    --domain TEXT
    --cost-type TEXT                  cpc|cpm|cpa|revshare|auto|daily_budget
    --cost-value FLOAT
  campaign update <ID>                Update campaign (PUT /campaigns/{id})
    --name TEXT
    --status TEXT                     active|paused
    --cost-type TEXT
    --cost-value FLOAT
  campaign delete <ID>                Archive a campaign (sets status=archived)
    --confirm                         Skip confirmation prompt
  campaign status-update <IDS...>     Bulk update campaign statuses
    --status TEXT (required)          active|paused|archived
  campaign links <ID>                 Get tracking links for a campaign

### offer
  offer list                          List offers (GET /offers)
  offer get <ID>                      Get a single offer
  offer create                        Create a new offer
    --name TEXT (required)
    --offer-source-id TEXT            Affiliate network (offer source) ID
    --url TEXT                        Offer destination URL
    --payout FLOAT
  offer update <ID>                   Update offer (PUT /offers/{id})
    --name TEXT
    --url TEXT
    --payout FLOAT
    --status TEXT
  offer delete <ID>                   Delete an offer
  offer status-update <IDS...>        Bulk update offer statuses
    --status TEXT (required)          active|paused|archived
  offer export                        Export offers to S3 (GET /offers/export)
    --ids TEXT                        Comma-separated offer IDs
    --status TEXT
    --networks TEXT
    --countries TEXT

### offer-source  (affiliate networks)
  offer-source list                   List affiliate networks (GET /networks)
  offer-source get <ID>               Get a network
  offer-source create                 Create a network
    --name TEXT (required)
    --postback-url TEXT
    --click-id-param TEXT             Click ID parameter name
    --payout-param TEXT               Payout parameter name
  offer-source update <ID>            Update a network (PUT /networks/{id})
    --name TEXT
    --postback-url TEXT
    --click-id-param TEXT
    --payout-param TEXT
  offer-source delete <ID>            Delete a network

### traffic  (traffic channels / sources)
  traffic list                        List traffic channels (GET /sources)
  traffic get <ID>                    Get a traffic channel
  traffic create                      Create a traffic channel
    --name TEXT (required)
    --template TEXT
  traffic update <ID>                 Update a traffic channel (PUT /sources/{id})
    --name TEXT
    --status TEXT
  traffic delete <ID>                 Delete a traffic channel

### lander  (landing pages)
  lander list                         List landers (GET /landings)
  lander get <ID>                     Get a lander
  lander create                       Create a lander
    --name TEXT (required)
    --url TEXT
    --tracking-type TEXT              redirect|direct
  lander update <ID>                  Update a lander (PUT /landings/{id})
    --name TEXT
    --url TEXT
    --tracking-type TEXT
    --status TEXT
  lander delete <ID>                  Delete a lander

### conversion
  conversion list                     List conversions (GET /conversions)
    --date-from DATE
    --date-to DATE
    --campaign-id TEXT
    --status TEXT                     approved|pending|declined|fired
  conversion upload                   Upload a conversion (POST /conversions)
    --click-id TEXT (required)
    --status TEXT                     approved|pending|declined (default: approved)
    --payout FLOAT
    --type TEXT
  conversion export                   Export conversions (GET /conversions/export)
    --date-from DATE (required)
    --date-to DATE (required)
    --campaign-id TEXT
    --offer-id TEXT
  conversion types                    List valid conversion types (local, no auth needed)

### report
  report general                      General performance report (GET /report)
    --date-from DATE
    --date-to DATE
    --group-by TEXT                   campaign|offer|lander|source|network|country|device|os|browser
    --filters TEXT
  report campaigns                    Campaign-level report (group_by=campaign)
    --date-from DATE
    --date-to DATE
  report clicks                       Click-level report (GET /report, group_by=click)
    --date-from DATE
    --date-to DATE
    --campaign-id TEXT
  report stream                       Stream-level report (group_by=stream)
    --date-from DATE
    --date-to DATE

### cost
  cost list                           Cost metrics via report endpoint (group_by=campaign)
    --date-from DATE
    --date-to DATE
  Note: RedTrack has no /costs endpoint. Cost data is accessed via /report.

### rule  (automation rules)
  rule list                           List automation rules (GET /rules)
  rule get <ID>                       Get a rule
  rule create                         Create a rule
    --name TEXT (required)
    --condition TEXT                  Condition expression or JSON
    --action TEXT                     Action to take when condition is met
  rule update <ID>                    Update a rule
    --name TEXT
    --status TEXT                     active|paused
  rule delete <ID>                    Delete a rule

### domain
  domain list                         List custom tracking domains (GET /domains)
  domain add                          Add a custom domain (POST /domains)
    --domain TEXT (required)
  domain update <ID>                  Update a domain (PUT /domains/{id})
    --domain-name TEXT
  domain delete <ID>                  Delete a domain
    --confirm                         Skip confirmation prompt
  domain ssl-renew <ID>               Regenerate free SSL certificate for a domain

### lookup  (reference data — no auth needed)
  lookup list                         List all available lookup types
  lookup get <TYPE>                   Get reference data for a type
    TYPE: browsers | browser_fullnames | categories | cities |
          connection_types | countries | currencies | device_brands |
          device_fullnames | devices | isp | languages | os | os_fullnames

### session
  session status                      Show current session (masked API key, base URL)

## Examples

# List all campaigns as JSON
cli-anything-redtrack --json campaign list

# Get report for January 2025 grouped by country
cli-anything-redtrack --json report general --date-from 2025-01-01 --date-to 2025-01-31 --group-by country

# Create a campaign
cli-anything-redtrack campaign create --name "My Campaign" --traffic-channel-id abc123

# Upload a conversion
cli-anything-redtrack conversion upload --click-id CLICKID123 --status approved --payout 5.50

# Bulk pause campaigns
cli-anything-redtrack campaign status-update id1 id2 id3 --status paused

# Archive (delete) a campaign
cli-anything-redtrack campaign delete CAMPID --confirm

# Look up all countries
cli-anything-redtrack --json lookup get countries

# Get cost data for a date range
cli-anything-redtrack --json cost list --date-from 2025-01-01 --date-to 2025-01-31

# Export conversions to S3
cli-anything-redtrack --json conversion export --date-from 2025-01-01 --date-to 2025-01-31

# Create an automation rule
cli-anything-redtrack rule create --name "Pause low ROI" --condition '{"metric":"roi","op":"<","value":0}' --action "pause_campaign"

# Add a custom tracking domain
cli-anything-redtrack domain add --domain track.example.com

## Interactive REPL

Run without arguments to enter the interactive REPL:
  cli-anything-redtrack

The REPL supports all commands with tab completion and history.

## Known Limitations

- No /costs endpoint in RedTrack API — cost data via /report
- campaign delete uses status archiving (sets status=archived), not a true DELETE call
- /rules endpoint exists but rule conditions/actions schema is undocumented
- lookup commands do not require authentication
