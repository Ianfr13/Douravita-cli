# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repo Is

CLI-Anything is a framework for generating agent-native CLI harnesses for GUI applications. It consists of:

1. **`cli-anything-plugin/`** — A Claude Code plugin that runs a 7-phase pipeline to auto-generate a full CLI harness for any software given its source code or GitHub URL.
2. **`<software>/agent-harness/`** — Individually installable Python packages, one per supported application (e.g., `gimp/`, `blender/`, `audacity/`).
3. **`registry.json`** — The CLI-Hub registry listing all available CLIs for the web hub.

## Commands

### Installing a Harness

```bash
cd <software>/agent-harness
pip install -e .
```

### Running Tests

```bash
# All tests for a harness (from inside agent-harness/)
python3 -m pytest cli_anything/<software>/tests/ -v

# Unit tests only (no backend software required)
python3 -m pytest cli_anything/<software>/tests/test_core.py -v

# E2E tests only (requires real backend installed)
python3 -m pytest cli_anything/<software>/tests/test_full_e2e.py -v

# Force-installed mode: requires the installed CLI command (not module fallback)
CLI_ANYTHING_FORCE_INSTALLED=1 python3 -m pytest cli_anything/<software>/tests/ -v -s
```

### Generating a SKILL.md

```bash
cd cli-anything-plugin
python skill_generator.py /path/to/software/agent-harness
```

### Plugin Commands (inside Claude Code)

```bash
/cli-anything:cli-anything <software-path-or-repo>   # Full 7-phase build
/cli-anything:refine <software-path> ["focus area"]  # Gap-analysis + incremental expansion
/cli-anything:test <software-path>                   # Run tests, update TEST.md
/cli-anything:validate <software-path>               # Validate against HARNESS.md standards
```

## Architecture

### The Plugin (`cli-anything-plugin/`)

`HARNESS.md` is the single source of truth for the methodology. The plugin's slash commands (`commands/`) reference it. When building or modifying a harness, always read `HARNESS.md` first — it defines all phases, patterns, and non-negotiable rules.

The 7-phase pipeline:
- **Phase 1**: Analyze the target software's codebase, identify its backend engine and data model
- **Phase 2**: Design command groups, state model, and output formats
- **Phase 3**: Implement Click CLI with REPL, core modules, and backend wrapper
- **Phase 4**: Write `TEST.md` test plan (written before any test code)
- **Phase 5**: Implement unit tests and E2E tests (must invoke real software, verify real artifacts)
- **Phase 6**: Run tests and append full results to `TEST.md`
- **Phase 6.5**: Generate `SKILL.md` using `skill_generator.py`
- **Phase 7**: Create `setup.py`, install to PATH, verify with `which`

`repl_skin.py` in the plugin root is the canonical REPL skin. It is copied verbatim into each harness's `utils/repl_skin.py` — never modify per-harness copies.

### Each Harness (`<software>/agent-harness/`)

All harnesses share the same internal structure:

```
<software>/agent-harness/
├── <SOFTWARE>.md                       # Software-specific architecture SOP
├── setup.py                            # Uses find_namespace_packages(include=["cli_anything.*"])
└── cli_anything/                       # NO __init__.py — PEP 420 namespace package
    └── <software>/                     # HAS __init__.py
        ├── <software>_cli.py           # Click CLI entry point + REPL default behavior
        ├── core/                       # Domain modules: project.py, session.py, export.py, ...
        ├── utils/
        │   ├── <software>_backend.py   # Invokes the real software via subprocess
        │   └── repl_skin.py            # Unmodified copy from cli-anything-plugin/
        ├── skills/SKILL.md             # AI-discoverable skill definition
        └── tests/
            ├── TEST.md                 # Test plan (written first) + results (appended after)
            ├── test_core.py            # Unit tests — synthetic data, no external deps
            └── test_full_e2e.py        # E2E + subprocess tests
```

The `cli_anything/` directory has **no `__init__.py`** — intentional. It is a PEP 420 namespace package so multiple `cli-anything-*` packages coexist in the same Python environment, each contributing `cli_anything/<software>/`.

### Key Design Rules

- **The real software is a hard dependency.** Every harness calls the actual application (e.g., `libreoffice --headless`, `blender --background`, `sox`) for rendering. No fallbacks, no reimplementations. Missing software must raise a clear error with install instructions.
- **Every command supports `--json`** for machine-readable output. Running the CLI bare (no subcommand) enters REPL mode via `invoke_without_command=True` on the Click group.
- **Subprocess tests use `_resolve_cli()`** — never hardcode `sys.executable`. The helper checks `shutil.which()` first; `CLI_ANYTHING_FORCE_INSTALLED=1` requires the installed command.
- **E2E tests must verify real artifacts** — check magic bytes (`%PDF-`), ZIP structure (OOXML), pixel/audio analysis. Process exit code 0 is not sufficient.
- **Session files use exclusive locking** — open with `"r+"` (not `"w"`) so the file isn't truncated before the lock is acquired; truncate inside the lock.

### Registry (`registry.json`)

All installable CLIs are listed here and served by the CLI-Hub. When adding a new harness, include an entry with `name`, `display_name`, `version`, `description`, `requires`, `install_cmd`, `entry_point`, `skill_md`, and `category`. The hub updates automatically on merge to `main`.

### Platform Integrations

The same methodology is also available via:
- `opencode-commands/` — OpenCode slash commands (copy alongside `HARNESS.md`)
- `openclaw-skill/` — OpenClaw `SKILL.md`
- `codex-skill/` — Codex skill with install scripts (`scripts/install.sh` / `install.ps1`)
- `qoder-plugin/` — Qodercli plugin registered via `setup-qodercli.sh`

---
# System CLIs Available

The following CLI tools are pre-installed. Full docs are in `.claude/cli-docs/` and available as slash commands.

Installed: ai-context cli-anything-infisical cli-anything-railway cloudflared gh gws playwright supabase wrangler
