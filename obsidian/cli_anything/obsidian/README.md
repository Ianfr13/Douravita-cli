# cli-anything-obsidian

CLI interface for Obsidian via the Local REST API plugin.

## Prerequisites

- **Obsidian** desktop app running
- **obsidian-local-rest-api** plugin installed and enabled
- **OBSIDIAN_API_KEY** environment variable set

Optional plugins for extended features:
- Dataview — enables `dataview` command group
- Templater — enables `templater` command group
- Folder Notes — enables `foldernotes` command group
- Obsidian Charts — enables `charts` command group
- Periodic Notes — enables weekly/monthly/quarterly/yearly in `periodic` group

## Installation

```bash
pip install cli-anything-obsidian
```

## Configuration

```bash
export OBSIDIAN_API_KEY="your-api-key-from-obsidian-settings"
export OBSIDIAN_HOST="https://127.0.0.1:27124"  # optional, this is the default
```

## Usage

```bash
# One-shot commands
cli-anything-obsidian status
cli-anything-obsidian vault list
cli-anything-obsidian vault get "Notes/My Note.md"
cli-anything-obsidian --json search simple "meeting notes"

# Interactive REPL
cli-anything-obsidian
```

## Command Reference

| Group | Commands | Description |
|-------|----------|-------------|
| `status` | — | Check API connection |
| `vault` | list, get, put, append, patch, delete, move, exists | File CRUD + move/exists |
| `active` | get, put, append, patch, delete | Operations on open file |
| `periodic` | get, put, append, patch, delete | Daily/weekly/monthly/quarterly/yearly notes |
| `search` | simple, dql, jsonlogic | Full-text, Dataview DQL, JsonLogic |
| `dataview` | raw, table, list, task | Dataview plugin queries |
| `templater` | list, get, create, run, insert | Templater plugin integration |
| `foldernotes` | get, create, refresh, list, exists | Folder Notes plugin |
| `charts` | generate, insert | Obsidian Charts — generate/insert chart blocks |
| `commands` | list, run | Execute Obsidian commands |
| `tags` | — | List vault tags with counts |
| `open` | — | Open file in Obsidian UI |

## Running Tests

```bash
# Unit tests (no Obsidian needed)
python3 -m pytest cli_anything/obsidian/tests/test_core.py -v

# E2E tests (requires running Obsidian + API key)
export OBSIDIAN_API_KEY="your-key"
python3 -m pytest cli_anything/obsidian/tests/test_full_e2e.py -v -s
```
