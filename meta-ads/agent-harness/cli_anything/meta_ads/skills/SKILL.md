---
name: "cli-anything-meta-ads"
description: "Full CLI for the Meta Ads API: manage campaigns, ad sets, ads, creatives, audiences, and insights via Graph API v21.0."
---

# cli-anything-meta-ads

A stateful CLI for the Meta Ads API. Provides structured access to all Meta Ads operations
with JSON output for agent consumption.

## Prerequisites

- Python 3.10+
- Meta access token with ads_management + ads_read permissions
- An ad account ID

## Setup

    cli-anything-meta-ads config set-token YOUR_TOKEN
    cli-anything-meta-ads config set-account YOUR_ACCOUNT_ID

## Command Groups

- config    : Manage credentials (set-token, set-account, show, clear)
- account   : Account info, spend summary, list accounts
- campaign  : List/create/update/pause/activate/delete campaigns
- adset     : Ad set targeting, budget, scheduling, status
- ad        : Create ads, assign creatives, control status
- creative  : Create link/video creatives, upload/list images
- audience  : Custom and lookalike audience management
- insights  : Performance metrics (account/campaign/adset/ad level)
- page      : List Facebook Pages

## Usage Examples

    cli-anything-meta-ads campaign list
    cli-anything-meta-ads --json campaign list
    cli-anything-meta-ads campaign create --name Q1 --objective OUTCOME_TRAFFIC --daily-budget 5000
    cli-anything-meta-ads adset create --name Brazilians --campaign ID --daily-budget 2000 --targeting '{"geo_locations":{"countries":["BR"]}}'
    cli-anything-meta-ads creative upload-image banner.jpg
    cli-anything-meta-ads creative create --name Banner --page-id PID --link URL --image-hash HASH --call-to-action SHOP_NOW
    cli-anything-meta-ads ad create --name Ad1 --adset ADSET_ID --creative CREATIVE_ID
    cli-anything-meta-ads audience create-custom --name Buyers --subtype CUSTOM
    cli-anything-meta-ads audience create-lookalike --name LAL --source-id AUD_ID --country BR --ratio 0.02
    cli-anything-meta-ads insights account --preset last_30d
    cli-anything-meta-ads --json insights campaign CAMPAIGN_ID --preset last_7d
    cli-anything-meta-ads insights adset ADSET_ID --breakdown age gender

## Agent Guidance

- Use --json on every command for machine-readable output.
- Budgets are in the account currency smallest unit (e.g. USD cents: 1000 = $10.00).
- Pass --targeting as a JSON string.
- Upload images first (creative upload-image) to get their hash before creating link creatives.
- Use --preset lifetime or --since/--until for insights date ranges (YYYY-MM-DD).
