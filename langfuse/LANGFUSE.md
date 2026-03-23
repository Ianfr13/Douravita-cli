# Langfuse CLI — SOP & Architecture

## Software Overview

**Langfuse** is an open-source LLM observability platform. It provides tracing,
prompt management, evaluations, datasets, cost tracking, and analytics for LLM
applications.

- **Type:** Web platform (SaaS + self-hosted)
- **Backend:** REST API over HTTPS
- **Auth:** HTTP Basic Auth (public key + secret key)
- **Data Model:** Traces → Observations (Spans/Generations/Events) → Scores
- **Native Formats:** JSON (API responses)

## Backend Engine

Unlike desktop GUI apps, Langfuse's "backend" is its REST API. The CLI wraps
the Langfuse public API (`/api/public/*`) using HTTP requests with Basic Auth.

### Authentication
- Username: Langfuse Public Key (`pk-lf-...`)
- Password: Langfuse Secret Key (`sk-lf-...`)
- Base URL: `https://cloud.langfuse.com` (EU), `https://us.cloud.langfuse.com` (US), or self-hosted

### Base URLs
| Environment | URL |
|---|---|
| Cloud EU | `https://cloud.langfuse.com` |
| Cloud US | `https://us.cloud.langfuse.com` |
| Self-hosted | `http://localhost:3000` |

## Data Model

### Core Entities
- **Trace** — Top-level unit representing one LLM interaction/request
- **Observation** — Child of a trace: SPAN, GENERATION, or EVENT
- **Score** — Numeric, boolean, or categorical evaluation attached to a trace/observation
- **Session** — Group of related traces
- **Prompt** — Versioned prompt template (text or chat format)
- **Dataset** — Collection of input/output pairs for evaluation
- **Dataset Item** — Single input/output pair in a dataset
- **Dataset Run** — Execution of a dataset against a model
- **Model** — LLM model definition with pricing info
- **Comment** — Annotation on traces/observations/sessions/prompts

## CLI Architecture

### Command Groups
| Group | Operations | API Base |
|-------|-----------|----------|
| `config` | set, show, profiles | Local config file |
| `traces` | list, get, delete | `/api/public/traces` |
| `observations` | list, get | `/api/public/observations` |
| `scores` | create, list, get, delete | `/api/public/scores` |
| `score-configs` | create, list, get | `/api/public/score-configs` |
| `prompts` | create, list, get | `/api/public/v2/prompts` |
| `datasets` | create, list, get | `/api/public/v2/datasets` |
| `dataset-items` | create, list, get, delete | `/api/public/dataset-items` |
| `dataset-runs` | list, get, delete | `/api/public/datasets/{name}/runs` |
| `sessions` | list, get | `/api/public/sessions` |
| `models` | create, list, get, delete | `/api/public/models` |
| `comments` | create, list, get | `/api/public/comments` |
| `projects` | current | `/api/public/projects` |
| `metrics` | daily | `/api/public/metrics` |
| `health` | check | `/api/public/health` |

### State Model
- **No project state** — Langfuse CLI is stateless; each command is independent
- **Config file** — `~/.cli-anything-langfuse/config.json` stores profiles (API keys, base URL)
- **Active profile** — Selected via `--profile` flag or `LANGFUSE_PROFILE` env var

### Output Format
- Human-readable tables by default
- `--json` flag for machine-readable JSON output
- Pagination via `--limit` and `--page` flags

## Implementation Notes

### No Local Software Dependency
Unlike other cli-anything CLIs, Langfuse CLI does NOT require local software
installation. The "backend" is the remote Langfuse API server. The CLI is
purely an HTTP API client.

### Required: API Keys
The CLI requires Langfuse API keys to function. These can be provided via:
1. Config file profile (`cli-anything-langfuse config set`)
2. Environment variables (`LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_BASE_URL`)
3. CLI flags (`--public-key`, `--secret-key`, `--base-url`)

Priority: CLI flags > env vars > config file profile.
