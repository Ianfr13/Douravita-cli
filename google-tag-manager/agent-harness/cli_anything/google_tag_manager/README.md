# cli-anything-google-tag-manager

Agent-native CLI for Google Tag Manager API v2. Manage GTM accounts, containers, workspaces, tags, triggers, variables, folders, environments, versions, and user permissions from the command line.

## Requirements

- Python 3.10+
- Google Cloud project with Tag Manager API enabled
- Authentication: Service Account JSON key or OAuth2 credentials

**The GTM API is a hard dependency** — this CLI is useless without valid Google API credentials. It makes real API calls to the GTM API v2.

## Installation

```bash
# From source
pip install -e /path/to/google-tag-manager/agent-harness/

# Verify installation
which cli-anything-google-tag-manager
cli-anything-google-tag-manager --help
```

## Setting Up Credentials

### Service Account (recommended for agents/automation)

1. Go to https://console.cloud.google.com/iam-admin/serviceaccounts
2. Create a service account with Tag Manager permissions
3. Download the JSON key file
4. Grant the service account access to your GTM account in GTM UI

```bash
cli-anything-google-tag-manager auth init --service-account /path/to/sa.json
# or
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/sa.json
```

### OAuth2 Browser Flow (for interactive use)

1. Go to https://console.cloud.google.com/apis/credentials
2. Create OAuth2 credentials (Desktop App)
3. Download the client secrets JSON

```bash
cli-anything-google-tag-manager auth init --oauth-secrets /path/to/client_secrets.json
```

## Quick Start

```bash
# Test authentication
cli-anything-google-tag-manager auth test

# List accounts
cli-anything-google-tag-manager account list

# Set context (avoids repeating IDs)
export GTM_ACCOUNT_ID=12345
export GTM_CONTAINER_ID=67890
export GTM_WORKSPACE_ID=3

# List workspace contents
cli-anything-google-tag-manager tag list
cli-anything-google-tag-manager trigger list
cli-anything-google-tag-manager variable list

# JSON output for agents
cli-anything-google-tag-manager --json tag list
```

## Interactive REPL

Running without arguments enters interactive REPL mode:

```bash
cli-anything-google-tag-manager
# Enters REPL with branded prompt and command history
```

## Running Tests

```bash
# Unit tests only (no GTM API required)
python3 -m pytest cli_anything/google_tag_manager/tests/test_core.py -v

# E2E tests (requires real GTM API credentials)
GOOGLE_APPLICATION_CREDENTIALS=/path/to/sa.json \
GTM_ACCOUNT_ID=12345 \
python3 -m pytest cli_anything/google_tag_manager/tests/test_full_e2e.py -v

# Subprocess tests (requires pip install -e . first)
CLI_ANYTHING_FORCE_INSTALLED=1 \
python3 -m pytest cli_anything/google_tag_manager/tests/ -v -s
```

## API Documentation

GTM API v2 reference: https://developers.google.com/tag-platform/tag-manager/api/v2
