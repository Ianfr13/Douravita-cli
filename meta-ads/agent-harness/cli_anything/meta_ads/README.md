# cli-anything-meta-ads

Full CLI harness for the Meta Ads API (Graph API v21.0).
Manage campaigns, ad sets, ads, creatives, audiences, and insights.

## Requirements

- Python 3.10+
- A valid Meta **access token** with ads_management and ads_read permissions
- An **ad account ID** (numeric, with or without act_ prefix)

## Installation

    cd meta-ads/agent-harness && pip install -e .

## Quick Setup

    cli-anything-meta-ads config set-token YOUR_ACCESS_TOKEN
    cli-anything-meta-ads config set-account YOUR_AD_ACCOUNT_ID

Or use environment variables:

    export META_ADS_ACCESS_TOKEN=YOUR_TOKEN
    export META_ADS_AD_ACCOUNT_ID=YOUR_ACCOUNT_ID

## Usage

    # Interactive REPL
    cli-anything-meta-ads

    # One-shot commands
    cli-anything-meta-ads campaign list
    cli-anything-meta-ads --json campaign list
    cli-anything-meta-ads campaign create --name Q1 --objective OUTCOME_TRAFFIC --daily-budget 5000
    cli-anything-meta-ads insights account --preset last_7d
    cli-anything-meta-ads insights campaign 123456 --since 2024-01-01 --until 2024-01-31

## Command Groups

- config    : Store/show/clear credentials
- account   : Account info, spend summary, list accounts
- campaign  : List, create, update, pause, activate, delete campaigns
- adset     : Ad set targeting, budgets, scheduling
- ad        : Create ads, assign creatives, status control
- creative  : Create link/video creatives, upload/list images
- audience  : Custom and lookalike audience management
- insights  : Performance metrics at account/campaign/adset/ad level
- page      : List connected Facebook Pages

## Running Tests

    python3 -m pytest cli_anything/meta_ads/tests/test_core.py -v
    CLI_ANYTHING_FORCE_INSTALLED=1 python3 -m pytest cli_anything/meta_ads/tests/ -v -s
