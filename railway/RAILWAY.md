# cli-anything-railway

A CLI wrapper for the [Railway](https://railway.app) deployment platform, built
on the cli-anything methodology.

## Installation

```bash
pip install -e /home/sandbox/workspace/repo/railway/agent-harness/
```

## Authentication

Set the `RAILWAY_TOKEN` environment variable, or pass `--token` on every
command:

```bash
export RAILWAY_TOKEN=your_token_here
```

## Usage

Start the interactive REPL:

```bash
cli-anything-railway
```

Or run a single command directly:

```bash
cli-anything-railway projects list
cli-anything-railway projects create my-app
cli-anything-railway projects info <PROJECT_ID>

cli-anything-railway services list --project <PROJECT_ID>
cli-anything-railway services info <SERVICE_ID>

cli-anything-railway deployments list --service <SERVICE_ID>
cli-anything-railway deployments trigger <SERVICE_ID>
cli-anything-railway deployments status <DEPLOYMENT_ID>

cli-anything-railway variables list --project <PROJECT_ID> --env <ENV_ID>
cli-anything-railway variables set KEY VALUE --project <PROJECT_ID> --env <ENV_ID>
cli-anything-railway variables delete KEY --project <PROJECT_ID> --env <ENV_ID>

cli-anything-railway environments list --project <PROJECT_ID>
cli-anything-railway environments create <NAME> --project <PROJECT_ID>
```

Add `--json` to any command for machine-readable JSON output.

## GraphQL Endpoint

`https://backboard.railway.app/graphql/v2`
