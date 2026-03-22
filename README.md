# Douravita CLI

Agent-native CLI wrappers built with the [cli-anything](https://github.com/Ianfr13/cli-anything) methodology.

## CLIs

### `cli-anything-infisical`
CLI wrapper for [Infisical](https://infisical.com) secrets manager.

```bash
cd infisical
pip install -e .
```

### `cli-anything-railway`
CLI wrapper for [Railway](https://railway.app) deployment platform.

```bash
cd railway
pip install -e .
```

### `cli-anything-obsidian`
CLI wrapper for [Obsidian](https://obsidian.md) via the [Local REST API](https://coddingtonbear.github.io/obsidian-local-rest-api/) plugin.
Read/write vault files, periodic notes, search, tags, and run commands — from the terminal or AI agents.

```bash
cd obsidian
pip install -e .
export OBSIDIAN_API_KEY="your-key-from-obsidian-settings"
cli-anything-obsidian --help
```

## Usage

See each CLI's `README.md` for full command reference.
