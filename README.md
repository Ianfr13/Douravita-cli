# Douravita CLI & Plugins

Agent-native CLIs e plugins para o workflow Douravita. CLIs seguem o pattern [cli-anything](https://github.com/Ianfr13/cli-anything). Plugins seguem o formato [Claude Code Marketplace](https://docs.anthropic.com/en/docs/claude-code/plugins).

---

## Plugins (Claude Code)

### `project-architect`

Setup completo de projetos do zero ao fim. 6 modos de operacao:

| Modo | O que faz |
|------|-----------|
| **INSTALL** | Maquina nova sem nada — instala Docker, VS Code, Git, Node, Claude Code, Infisical |
| **BUILD** | Projeto novo — devcontainer, Infisical, GitHub, CLAUDE.md, CONTEXT.md, skills |
| **FORK** | Adapta repo externo para o workflow Douravita |
| **MIGRATION** | Projeto existente sem estrutura — adiciona layers |
| **UPDATE** | Estrutura que cresceu — novos workspaces, CLIs, skills |
| **AUDIT** | Diagnostica problemas — 8 erros de estrutura + libs desatualizadas |

**Features:**
- Deep Scan spec-driven com subagentes isolados (14 categorias: API contracts, data stores, auth, regras de negocio, etc.)
- Context7 integrado (MCP + CLI `npx ctx7`) para validar libs e patterns
- Hook que forca uso de subagentes no scan
- Output com TODO checklist executavel

**Instalar:**

```bash
# No Claude Code
/plugin marketplace add Ianfr13/Douravita-cli
/plugin install project-architect@douravita-plugins
```

Ou via `settings.json` do projeto:

```json
{
  "extraKnownMarketplaces": {
    "douravita-plugins": {
      "source": {
        "source": "github",
        "repo": "Ianfr13/Douravita-cli"
      }
    }
  },
  "enabledPlugins": {
    "project-architect@douravita-plugins": true
  }
}
```

---

## CLIs

Instalados via pip. Disponíveis na imagem base `ghcr.io/ianfr13/douravita-base:latest` ou individualmente:

```bash
pip install "git+https://github.com/Ianfr13/Douravita-cli.git#subdirectory=<nome>"
```

### `meta-ads`
Gerenciar campanhas Meta (Facebook/Instagram) — criar, pausar, insights, audiences.

### `google-tag-manager`
Gerenciar containers GTM — tags, triggers, variaveis, versoes.

### `redtrack`
Performance marketing — campanhas, conversoes, relatorios, ROAS.

### `cli-anything-infisical`
Wrapper Python para manipulacao programatica da API do Infisical.

### `cli-anything-railway`
Deploy e gerenciamento de apps no Railway.

### `cli-anything-obsidian`
Leitura/escrita no vault Obsidian via Local REST API — arquivos, busca, Dataview, Templater, charts.

```bash
export OBSIDIAN_API_KEY="your-key"
cli-anything-obsidian --help
```

### `langfuse`
Observabilidade de LLM — traces, scores, prompts.

---

## Estrutura do Repo

```
Douravita-cli/
├── .claude-plugin/
│   └── marketplace.json         # Catalogo de plugins Claude Code
├── plugins/
│   └── project-architect/       # Plugin: project architect
│       ├── .claude-plugin/
│       │   └── plugin.json
│       ├── hooks/
│       │   └── hooks.json
│       └── skills/
│           └── project-architect/
│               ├── SKILL.md     # Core (208 linhas)
│               ├── agents/
│               │   └── scanner.md
│               ├── scripts/
│               │   └── enforce-deep-scan.sh
│               └── references/
│                   ├── mode-*.md
│                   ├── install-guide.md
│                   ├── documentation-lookup.md
│                   └── ...
├── meta-ads/
├── google-tag-manager/
├── redtrack/
├── infisical/
├── railway/
├── obsidian/
└── langfuse/
```
