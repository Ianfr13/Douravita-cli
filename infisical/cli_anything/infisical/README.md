# cli-anything-infisical

A CLI wrapper for the [Infisical](https://infisical.com) secrets manager REST API.

## Installation

```bash
pip install -e /path/to/infisical/agent-harness/
```

## Configuration

| Variable | Flag | Default |
|---|---|---|
| `INFISICAL_TOKEN` | `--token` | (required) |
| `INFISICAL_WORKSPACE_ID` | `--workspace` / `-w` | (required for secrets) |
| `INFISICAL_ENV` | `--env` / `-e` | `dev` |
| `INFISICAL_URL` | `--url` | `https://sec.douravita.com.br` |
| `INFISICAL_ORG_ID` | `--org-id` | (required for project create) |

## Usage

```bash
# List all secrets
cli-anything-infisical -w <workspace-id> secrets list

# Get a specific secret
cli-anything-infisical -w <workspace-id> secrets get MY_SECRET

# Export as KEY=VALUE
cli-anything-infisical -w <workspace-id> secrets export

# Export as JSON
cli-anything-infisical -w <workspace-id> secrets export --json

# Create a secret
cli-anything-infisical -w <workspace-id> secrets create MY_KEY my_value

# Update a secret
cli-anything-infisical -w <workspace-id> secrets edit MY_KEY new_value

# List projects
cli-anything-infisical projects list

# Create a project
cli-anything-infisical projects create "My Project" --org-id <org-id>

# Interactive REPL mode
cli-anything-infisical
```

## Python module

```bash
python -m cli_anything.infisical --help
```
