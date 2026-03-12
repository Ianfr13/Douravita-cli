# INFISICAL — Standard Operating Procedure

## Overview

`cli-anything-infisical` is a Python CLI wrapper for the Infisical self-hosted secrets manager REST API at `sec.douravita.com.br`.

It follows the `cli-anything` methodology: namespace packages under `cli_anything.*`, consistent `ReplSkin` branding, and a `setup.py` entry point.

---

## Installation

```bash
pip install -e /home/sandbox/workspace/repo/infisical/agent-harness/
```

Verify:

```bash
which cli-anything-infisical
cli-anything-infisical --help
```

---

## Authentication

The CLI uses a **Bearer token** for all API calls.

Supply it via:
- Environment variable: `export INFISICAL_TOKEN=<token>`
- CLI flag: `--token <token>`

**Never hard-code the token in any file.**

---

## Common workflows

### List secrets

```bash
export INFISICAL_TOKEN=<token>
export INFISICAL_WORKSPACE_ID=<workspace-id>
export INFISICAL_ENV=production

cli-anything-infisical secrets list
```

### Export secrets for a shell script

```bash
eval $(cli-anything-infisical secrets export)
echo $MY_SECRET
```

### Export as JSON (for CI/CD pipelines)

```bash
cli-anything-infisical secrets export --json > secrets.json
```

### Create / update secrets

```bash
cli-anything-infisical secrets create DB_PASSWORD "super-secret"
cli-anything-infisical secrets edit DB_PASSWORD "new-super-secret"
```

### Manage projects

```bash
cli-anything-infisical projects list
cli-anything-infisical projects create "New Project" --org-id <org-id>
```

---

## API reference

| Operation | Endpoint |
|---|---|
| List secrets | `GET /api/v3/secrets/raw` |
| Get secret | `GET /api/v3/secrets/raw/{name}` |
| Create secret | `POST /api/v3/secrets/raw/{name}` |
| Update secret | `PATCH /api/v3/secrets/raw/{name}` |
| List workspaces | `GET /api/v1/workspace` |
| Create workspace | `POST /api/v2/workspace` |

---

## Directory layout

```
infisical/
└── agent-harness/
    ├── INFISICAL.md              ← this file
    ├── setup.py
    └── cli_anything/
        └── infisical/
            ├── __init__.py
            ├── __main__.py
            ├── README.md
            ├── infisical_cli.py
            ├── core/
            │   ├── __init__.py
            │   ├── secrets.py
            │   └── projects.py
            ├── utils/
            │   ├── __init__.py
            │   ├── infisical_backend.py
            │   └── repl_skin.py
            └── tests/
                ├── TEST.md
                └── test_core.py
```

---

## Running tests

```bash
python3 -m pytest /home/sandbox/workspace/repo/infisical/agent-harness/cli_anything/infisical/tests/test_core.py -v
```

---

## Environment variables reference

| Variable | Purpose | Default |
|---|---|---|
| `INFISICAL_TOKEN` | API Bearer token | — |
| `INFISICAL_WORKSPACE_ID` | Target workspace/project ID | — |
| `INFISICAL_ENV` | Target environment | `dev` |
| `INFISICAL_URL` | Infisical instance base URL | `https://sec.douravita.com.br` |
| `INFISICAL_ORG_ID` | Organization ID for project creation | — |
