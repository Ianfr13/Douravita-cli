# Douravita CLI & Plugins

Agent-native CLIs e plugins para o workflow Douravita. CLIs seguem o pattern [cli-anything](https://github.com/Ianfr13/cli-anything). Plugins seguem o formato [Claude Code Marketplace](https://docs.anthropic.com/en/docs/claude-code/plugins).

---

## Plugins (Claude Code)

### `project-architect`

Setup completo de projetos do zero ao fim. 6 modos de operacao:

| Modo | O que faz |
|------|-----------|
| **INSTALL** | Maquina nova sem nada — instala Docker, VS Code, Git, Node, Claude Code, Infisical, Agent Vault |
| **BUILD** | Projeto novo — devcontainer, Infisical, GitHub, CLAUDE.md, CONTEXT.md, skills |
| **FORK** | Adapta repo externo para o workflow Douravita |
| **MIGRATION** | Projeto existente sem estrutura — adiciona layers |
| **UPDATE** | Estrutura que cresceu — novos workspaces, CLIs, skills |
| **AUDIT** | Diagnostica problemas — 8 erros de estrutura + libs desatualizadas |

**Features:**
- Deep Scan spec-driven via **Workflow (ultracode)** — um scanner-agent por area funcional, em paralelo, com output estruturado + relatorio `.md` por area (15 categorias: API contracts, data stores, auth, regras de negocio, seguranca, etc.)
- **Automation recommender dinamico** — sem catalogo fixo: recomenda CLIs, skills, subagents, hooks e MCP a partir dos sinais do scan, descobrindo via `registry.json` vivo + aitmpl.com (`npx claude-code-templates`) + GitHub. Pergunta antes de instalar.
- **Secrets via Agent Vault** — proxy de credenciais (Infisical) que entrega secrets aos agentes sem expo-los; instala se faltar
- Context7 integrado (MCP + CLI `npx ctx7`) para validar libs e patterns
- Hook que forca o scan via Workflow antes de leitura direta da codebase
- Output com TODO checklist + `setup-recommendations.md` executaveis

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
│               ├── SKILL.md     # Core
│               ├── agents/
│               │   └── scanner.md
│               ├── scripts/
│               │   ├── deep-scan.workflow.js   # Workflow ultracode do Deep Scan
│               │   └── enforce-deep-scan.sh    # Hook: forca o scan via Workflow
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
