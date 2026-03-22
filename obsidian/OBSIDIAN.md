# Obsidian Local REST API: Project-Specific Analysis & SOP

## Architecture Summary

Obsidian Local REST API is a plugin that exposes a REST interface to an Obsidian vault,
enabling external scripts, AI agents, and automation tools to read and modify notes
programmatically via HTTP.

```
┌──────────────────────────────────────────────────────────┐
│                  Obsidian Desktop App                    │
│  ┌────────────┐ ┌─────────────┐ ┌────────────────────┐  │
│  │   Vault    │ │  Periodic   │ │  Commands Plugin   │  │
│  │  Manager   │ │   Notes     │ │      System        │  │
│  └─────┬──────┘ └──────┬──────┘ └────────┬───────────┘  │
│        │               │                 │               │
│  ┌─────┴───────────────┴─────────────────┴────────────┐  │
│  │         Local REST API Plugin (port 27124/27123)   │  │
│  │                                                    │  │
│  │  /           /active/    /vault/    /periodic/     │  │
│  │  /search/    /commands/  /tags/     /open/         │  │
│  └────────────────────────┬───────────────────────────┘  │
└───────────────────────────┼──────────────────────────────┘
                            │ HTTPS (27124) or HTTP (27123)
               ┌────────────┴───────────┐
               │    cli-anything-obsidian│
               │    REST API wrapper     │
               └─────────────────────────┘
```

## CLI Strategy: REST API Wrapper

Obsidian Local REST API exposes a clean REST API. Our CLI wraps it with:

1. **requests** — HTTP client for all API calls (with SSL verification bypass for self-signed cert)
2. **Click CLI** — Structured command groups matching the API surface
3. **REPL** — Interactive mode for exploratory vault navigation
4. **Dual output** — Human-readable and `--json` for agent consumption

### API Endpoints

| Endpoint | Methods | Purpose |
|----------|---------|---------|
| `/` | GET | Server status check |
| `/active/` | GET, POST, PUT, PATCH, DELETE | Active file operations |
| `/vault/` | GET | List vault root |
| `/vault/{path}/` | GET | List directory |
| `/vault/{filename}` | GET, POST, PUT, PATCH, DELETE | File operations |
| `/periodic/{period}/` | GET, POST, PUT, PATCH, DELETE | Current period note |
| `/periodic/{period}/{y}/{m}/{d}/` | GET, POST, PUT, PATCH, DELETE | Specific date note |
| `/commands/` | GET | List Obsidian commands |
| `/commands/{id}/` | POST | Execute command |
| `/search/simple/` | POST | Fuzzy full-text search |
| `/search/` | POST | Advanced search (DQL or JsonLogic) |
| `/tags/` | GET | List all tags with counts |
| `/open/{filename}` | POST | Open file in Obsidian UI |

## Command Map: API Endpoint → CLI Command

| API | CLI Command |
|-----|------------|
| `GET /` | `status` |
| `GET /active/` | `active get [--format]` |
| `POST /active/` | `active append <content>` |
| `PUT /active/` | `active put <content>` |
| `PATCH /active/` | `active patch --op --type --target <content>` |
| `DELETE /active/` | `active delete` |
| `GET /vault/` | `vault list` |
| `GET /vault/{path}/` | `vault list <path>` |
| `GET /vault/{file}` | `vault get <file> [--format]` |
| `POST /vault/{file}` | `vault append <file> <content>` |
| `PUT /vault/{file}` | `vault put <file> <content>` |
| `PATCH /vault/{file}` | `vault patch <file> --op --type --target <content>` |
| `DELETE /vault/{file}` | `vault delete <file>` |
| `GET /periodic/{period}/` | `periodic get <period>` |
| `POST /periodic/{period}/` | `periodic append <period> <content>` |
| `PUT /periodic/{period}/` | `periodic put <period> <content>` |
| `DELETE /periodic/{period}/` | `periodic delete <period>` |
| `GET /periodic/{period}/{y}/{m}/{d}/` | `periodic get <period> --date YYYY-MM-DD` |
| `GET /commands/` | `commands list` |
| `POST /commands/{id}/` | `commands run <id>` |
| `POST /search/simple/` | `search <query> [--context N]` |
| `POST /search/` (DQL) | `search dql <query>` |
| `POST /search/` (JsonLogic) | `search jsonlogic <json>` |
| `GET /tags/` | `tags` |
| `POST /open/{file}` | `open <file> [--new-leaf]` |

## Authentication

- **Bearer token** — Required on all endpoints except `GET /`
- Configured via `OBSIDIAN_API_KEY` env var or `--api-key` flag
- Token found in Obsidian Settings → Local REST API

## Supported Output Formats (GET file/active)

| Accept Header | CLI Flag | Description |
|--------------|----------|-------------|
| `text/markdown` | `--format markdown` (default) | Raw markdown content |
| `application/vnd.olrapi.note+json` | `--format json` | Parsed note with frontmatter, tags |
| `application/vnd.olrapi.document-map+json` | `--format map` | Structural document map |

## PATCH Operation Parameters

| Header | CLI Flag | Description |
|--------|----------|-------------|
| `Operation` | `--op append\|prepend\|replace` | Operation type |
| `Target-Type` | `--type heading\|block\|frontmatter` | Target type |
| `Target` | `--target <value>` | Section name, block ref, or frontmatter key |
| `Target-Delimiter` | `--delimiter <char>` | Nested heading separator (default `::`) |
| `Create-Target-If-Missing` | `--create` | Create section if absent |

## Periodic Note Periods

- `daily`, `weekly`, `monthly`, `quarterly`, `yearly`

## Test Coverage Plan

1. **Unit tests** (`test_core.py`): No Obsidian server needed
   - Backend URL construction and headers
   - Authentication header injection
   - Content-type handling for different formats
   - Error handling paths (connection error, 404, 401)
   - CLI argument parsing via Click test runner
   - Output formatting helpers

2. **E2E tests** (`test_full_e2e.py`): Requires Obsidian running with plugin enabled
   - Server status check
   - Vault listing
   - File creation, read, append, replace, delete
   - Search (simple and advanced)
   - Tag listing
   - Command listing
   - Periodic notes (daily)
   - Active file operations
