---
name: "cli-anything-google-tag-manager"
description: "Agent-native CLI for Google Tag Manager API v2. Manage accounts, containers, workspaces, tags, triggers, variables, folders, environments, versions, and user permissions."
triggers:
  - "google tag manager"
  - "GTM"
  - "tag manager"
  - "gtm container"
  - "gtm workspace"
  - "gtm tag"
  - "gtm trigger"
  - "gtm variable"
---

# cli-anything-google-tag-manager

Agent-native CLI for Google Tag Manager (GTM) API v2. Provides full programmatic access to all GTM resources via a structured command-line interface with REPL mode, JSON output, and environment-variable-based context management.

## Prerequisites

- Python 3.10+
- A Google Cloud project with the Tag Manager API enabled
- Authentication: service account JSON key **or** OAuth2 credentials

```bash
# Enable the Tag Manager API
gcloud services enable tagmanager.googleapis.com

# Install the CLI
pip install cli-anything-google-tag-manager
# or from source:
pip install -e /path/to/google-tag-manager/agent-harness/
```

## Authentication

### Option 1: Service Account (recommended for agents)

```bash
# Install service account credentials
cli-anything-google-tag-manager auth init --service-account /path/to/service-account.json

# Or set environment variable directly
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

### Option 2: OAuth2 Browser Flow

```bash
cli-anything-google-tag-manager auth init --oauth-secrets /path/to/client_secrets.json
# Opens browser for authorization
```

### Test Authentication

```bash
cli-anything-google-tag-manager auth test
cli-anything-google-tag-manager auth info
```

## Basic Usage

```bash
# Interactive REPL (default when run with no subcommand)
cli-anything-google-tag-manager

# One-shot commands
cli-anything-google-tag-manager account list
cli-anything-google-tag-manager --account-id 12345 container list
cli-anything-google-tag-manager --json account list  # machine-readable JSON

# Set context via environment variables (reduces repetition)
export GTM_ACCOUNT_ID=12345
export GTM_CONTAINER_ID=67890
export GTM_WORKSPACE_ID=3
```

## Global Options

| Option | Env Var | Description |
|--------|---------|-------------|
| `--account-id TEXT` | `GTM_ACCOUNT_ID` | GTM Account ID |
| `--container-id TEXT` | `GTM_CONTAINER_ID` | GTM Container ID |
| `--workspace-id TEXT` | `GTM_WORKSPACE_ID` | GTM Workspace ID |
| `--credentials TEXT` | `GOOGLE_APPLICATION_CREDENTIALS` | Path to credentials JSON |
| `--json` | — | Output machine-readable JSON |

## Command Reference

### auth — Authentication Management

```bash
cli-anything-google-tag-manager auth init --service-account sa.json
cli-anything-google-tag-manager auth init --oauth-secrets secrets.json
cli-anything-google-tag-manager auth test
cli-anything-google-tag-manager auth info
```

### account — Account Operations

```bash
cli-anything-google-tag-manager account list
cli-anything-google-tag-manager account get [ACCOUNT_ID]
cli-anything-google-tag-manager account update [ACCOUNT_ID] --name "New Name"
```

### container — Container Management

```bash
cli-anything-google-tag-manager container list [ACCOUNT_ID]
cli-anything-google-tag-manager container get [CONTAINER_ID] --account-id 123
cli-anything-google-tag-manager container create "My Container" --usage-context web
cli-anything-google-tag-manager container update [CONTAINER_ID] --name "New Name"
cli-anything-google-tag-manager container delete [CONTAINER_ID] --force
cli-anything-google-tag-manager container snippet [CONTAINER_ID]
```

### workspace — Workspace Operations

```bash
cli-anything-google-tag-manager workspace list
cli-anything-google-tag-manager workspace get [WORKSPACE_ID]
cli-anything-google-tag-manager workspace create "Dev Workspace" --description "Development"
cli-anything-google-tag-manager workspace update [WORKSPACE_ID] --name "New Name"
cli-anything-google-tag-manager workspace delete [WORKSPACE_ID] --force
cli-anything-google-tag-manager workspace status [WORKSPACE_ID]
cli-anything-google-tag-manager workspace sync [WORKSPACE_ID]
cli-anything-google-tag-manager workspace preview [WORKSPACE_ID]
cli-anything-google-tag-manager workspace publish [WORKSPACE_ID] --name "v2.0" --notes "Release"
```

### tag — Tag Management

```bash
cli-anything-google-tag-manager tag list
cli-anything-google-tag-manager tag get TAG_ID
cli-anything-google-tag-manager tag create "GA4 Config" --type googtag \
  --trigger 123 \
  --param '{"type":"template","key":"tagId","value":"G-XXXXXX"}'
cli-anything-google-tag-manager tag update TAG_ID --name "New Name"
cli-anything-google-tag-manager tag delete TAG_ID --force
cli-anything-google-tag-manager tag revert TAG_ID
```

### trigger — Trigger Management

```bash
cli-anything-google-tag-manager trigger list
cli-anything-google-tag-manager trigger get TRIGGER_ID
cli-anything-google-tag-manager trigger create "All Pages" --type pageview
cli-anything-google-tag-manager trigger create "Button Click" --type click \
  --filter '{"type":"contains","parameter":[{"type":"template","key":"arg0","value":"{{Click Classes}}"},{"type":"template","key":"arg1","value":"cta-button"}]}'
cli-anything-google-tag-manager trigger update TRIGGER_ID --name "New Name"
cli-anything-google-tag-manager trigger delete TRIGGER_ID --force
cli-anything-google-tag-manager trigger revert TRIGGER_ID
```

### variable — Variable Management

```bash
cli-anything-google-tag-manager variable list
cli-anything-google-tag-manager variable get VARIABLE_ID
cli-anything-google-tag-manager variable create "GA Tracking ID" --type v \
  --param '{"type":"template","key":"value","value":"UA-123456-1"}'
cli-anything-google-tag-manager variable create "DL Event Name" --type d \
  --param '{"type":"template","key":"name","value":"event"}'
cli-anything-google-tag-manager variable update VARIABLE_ID --name "New Name"
cli-anything-google-tag-manager variable delete VARIABLE_ID --force
cli-anything-google-tag-manager variable revert VARIABLE_ID
```

### folder — Folder Management

```bash
cli-anything-google-tag-manager folder list
cli-anything-google-tag-manager folder get FOLDER_ID
cli-anything-google-tag-manager folder create "Analytics Tags"
cli-anything-google-tag-manager folder update FOLDER_ID "New Folder Name"
cli-anything-google-tag-manager folder delete FOLDER_ID --force
cli-anything-google-tag-manager folder entities FOLDER_ID
cli-anything-google-tag-manager folder move FOLDER_ID --tag 111 --trigger 222 --variable 333
```

### env — Environment Management

```bash
cli-anything-google-tag-manager env list
cli-anything-google-tag-manager env get ENV_ID
cli-anything-google-tag-manager env create "Staging" --url "https://staging.example.com"
cli-anything-google-tag-manager env update ENV_ID --url "https://new-staging.example.com"
cli-anything-google-tag-manager env delete ENV_ID --force
cli-anything-google-tag-manager env reauth ENV_ID
```

### version — Version History

```bash
cli-anything-google-tag-manager version list
cli-anything-google-tag-manager version list --include-deleted
cli-anything-google-tag-manager version latest
```

### permission — User Permission Management

```bash
cli-anything-google-tag-manager permission list [ACCOUNT_ID]
cli-anything-google-tag-manager permission get USER_PERM_ID
cli-anything-google-tag-manager permission grant user@example.com --access user \
  --container-access '{"containerId":"123","permission":"edit"}'
cli-anything-google-tag-manager permission update USER_PERM_ID --access admin
cli-anything-google-tag-manager permission revoke USER_PERM_ID --force
```

## Common Workflows

### Set Up a New Container

```bash
export GTM_ACCOUNT_ID=12345

# Create container
cli-anything-google-tag-manager container create "My Website" \
  --usage-context web \
  --domain example.com \
  --json

# Get the container snippet
cli-anything-google-tag-manager container snippet CONTAINER_ID
```

### Add GA4 Configuration Tag

```bash
export GTM_ACCOUNT_ID=12345
export GTM_CONTAINER_ID=67890
export GTM_WORKSPACE_ID=3

# Create a trigger (All Pages)
cli-anything-google-tag-manager trigger create "All Pages" --type pageview --json

# Create GA4 Config tag
cli-anything-google-tag-manager tag create "GA4 Configuration" \
  --type googtag \
  --trigger TRIGGER_ID \
  --param '{"type":"template","key":"tagId","value":"G-XXXXXXXXXX"}' \
  --json

# Preview the workspace changes
cli-anything-google-tag-manager workspace preview

# Create a version
cli-anything-google-tag-manager workspace publish --name "v1.0 - GA4 Setup"
```

### Workspace Status and Sync

```bash
# Check what changed in workspace
cli-anything-google-tag-manager workspace status --json

# Sync with latest published version
cli-anything-google-tag-manager workspace sync --json
```

## JSON Output Examples

### account list --json

```json
[
  {
    "path": "accounts/12345",
    "accountId": "12345",
    "name": "My Company",
    "shareData": false
  }
]
```

### tag list --json

```json
[
  {
    "path": "accounts/12345/containers/67890/workspaces/3/tags/1",
    "accountId": "12345",
    "containerId": "67890",
    "workspaceId": "3",
    "tagId": "1",
    "name": "GA4 Configuration",
    "type": "googtag",
    "parameter": [
      {"type": "template", "key": "tagId", "value": "G-XXXXXXXXXX"}
    ],
    "firingTriggerId": ["2345"],
    "tagFiringOption": "oncePerEvent"
  }
]
```

### workspace status --json

```json
{
  "workspaceChange": [
    {
      "tag": {
        "tagId": "1",
        "name": "GA4 Configuration",
        "type": "googtag"
      },
      "changeStatus": "added"
    }
  ]
}
```

## Agent-Specific Guidance

- **Always use `--json`** for programmatic output — never parse human-readable table output.
- **Set context env vars** (`GTM_ACCOUNT_ID`, `GTM_CONTAINER_ID`, `GTM_WORKSPACE_ID`) to avoid repeating IDs on every command.
- **Error handling**: Errors are printed to stderr with clear messages. JSON errors use format: `{"error": "...", "type": "..."}`.
- **IDs are strings**: GTM IDs are numeric strings. Pass them as strings (e.g., `"12345"`, not `12345`).
- **Parameters**: Tag, trigger, and variable parameters use GTM's parameter schema:
  ```json
  {"type": "template", "key": "trackingId", "value": "UA-123456-1"}
  {"type": "boolean", "key": "enableLinkId", "value": "true"}
  {"type": "integer", "key": "scrollThreshold", "value": "75"}
  {"type": "list", "key": "triggers", "list": [...]}
  {"type": "map", "key": "customDimensions", "map": [...]}
  ```
- **Workspace required for tags/triggers/variables**: Always set `GTM_WORKSPACE_ID` before managing workspace-level resources.
- **Publishing**: Use `workspace publish` to create a version. GTM's live publishing happens through the GTM UI or separately via the `containers.versions.publish` API method.

## Variable Type Reference

| Type | Description |
|------|-------------|
| `v` | Constant Variable |
| `k` | First-Party Cookie |
| `d` | Data Layer Variable |
| `j` | Custom JavaScript |
| `u` | URL |
| `jsm` | JavaScript Variable |
| `remm` | Regular Expression Table |
| `smm` | Lookup Table |
| `gas` | Google Analytics Settings |

## Tag Type Reference

| Type | Description |
|------|-------------|
| `ua` | Universal Analytics |
| `googtag` | Google tag (GA4/Ads) |
| `awct` | Google Ads Conversion Tracking |
| `html` | Custom HTML |
| `img` | Custom Image |
| `flc` | Floodlight Counter |
| `fls` | Floodlight Sales |

## Trigger Type Reference

| Type | Description |
|------|-------------|
| `pageview` | Page View |
| `domReady` | DOM Ready |
| `windowLoaded` | Window Loaded |
| `click` | All Elements Click |
| `linkClick` | Just Links Click |
| `formSubmission` | Form Submission |
| `historyChange` | History Change |
| `jsError` | JavaScript Error |
| `scrollDepth` | Scroll Depth |
| `youtubeVideo` | YouTube Video |
| `customEvent` | Custom Event |
| `always` | Consent Initialization - All Pages |
