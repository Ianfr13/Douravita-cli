# CLI Catalog — Douravita

Todos os CLIs disponíveis no ecossistema Douravita. Use este catálogo no BUILD/FORK/MIGRATION para decidir o que instalar em cada projeto.

---

## CLIs da Imagem Base (sempre disponíveis)

Todo projeto que use `ghcr.io/ianfr13/douravita-base:latest` já tem:

| CLI | O que faz |
|-----|-----------|
| `gh` | GitHub CLI — criar repos, PRs, issues, releases |
| `infisical` | Secrets management — carregar vars por ambiente |
| `gws` | Google Workspace CLI — Drive, Sheets, Docs, Gmail |
| `obsidian` | Leitura/escrita no vault Obsidian via REST API |
| `claude` | Claude Code — agente AI |
| `git`, `curl`, `jq`, `fzf` | Ferramentas de sistema |
| `node` / `npm` | Node 22 + npm |
| `python3` / `pip3` | Python 3 |

---

## CLIs Douravita (Douravita-cli repo)

Instalados por projeto via pip. Código em: `https://github.com/Ianfr13/Douravita-cli`

| CLI | Subdiretório | O que faz | Quando usar |
|-----|-------------|-----------|-------------|
| `meta-ads` | `meta-ads/` | Gerenciar campanhas Meta (Facebook/Instagram) | Projetos com paid ads no Meta |
| `google-tag-manager` | `google-tag-manager/` | Gerenciar containers GTM, tags, triggers | Projetos com tracking/analytics |
| `redtrack` | `redtrack/` | Performance marketing — campanhas, conversões, relatórios | Projetos com atribuição/tracking avançado |
| `cli-anything-railway` | `railway/` | Deploy e gerenciamento no Railway | Projetos com deploy de servidor |
| `cli-anything-infisical` | `infisical/` | Wrapper Python para manipulação programática da API do Infisical | Projetos que criam/editam secrets via código — diferente do `infisical` CLI nativo que apenas carrega vars no container |

### Como instalar no Dockerfile

```dockerfile
FROM ghcr.io/ianfr13/douravita-base:latest

# Adicione os CLIs específicos deste projeto
RUN pip3 install --break-system-packages \
    "git+https://github.com/Ianfr13/Douravita-cli.git#subdirectory=meta-ads" \
    "git+https://github.com/Ianfr13/Douravita-cli.git#subdirectory=google-tag-manager"
```

---

## CLIs de Terceiros (instalados por projeto)

| CLI | Instalar | O que faz | Quando usar |
|-----|---------|-----------|-------------|
| `supabase` | `npm i -g supabase` | Banco de dados, auth, storage | Projetos com backend Supabase |
| `wrangler` | `npm i -g wrangler` | Deploy Cloudflare Workers/Pages | Projetos na Cloudflare |
| `playwright` | `npm i -g playwright` | Testes e automação de browser | Landing pages, scraping, testes E2E |

---

## Guia de Seleção por Tipo de Projeto

| Tipo de projeto | CLIs recomendados (além do base) |
|----------------|----------------------------------|
| Landing page / marketing | `meta-ads`, `google-tag-manager`, `playwright` |
| SaaS / app com backend | `supabase` ou `railway`, `playwright` |
| Ferramenta interna / script | Só o base, + `railway` se precisar de deploy |
| Automação / tracking | `redtrack`, `google-tag-manager`, `meta-ads` |
| Cloudflare Workers/Pages | `wrangler` |
| Fork de projeto externo | Analise o stack e adicione os necessários |

---

## Migração de MCP para CLI

Se o repo sendo adaptado usa MCP servers, mapeie para o CLI equivalente:

| MCP server | CLI equivalente |
|-----------|----------------|
| `@modelcontextprotocol/server-github` | `gh` (GitHub CLI) |
| `obsidian-mcp` | `obsidian` CLI |
| Qualquer MCP de filesystem | Ferramentas nativas do Claude Code |
| MCP sem equivalente | Construir novo CLI em Douravita-cli |

---

## Construindo um Novo CLI

Se o projeto precisa de integração que não existe ainda:
1. Criar subdiretório em `Douravita-cli/nome-do-servico/`
2. Seguir o padrão `cli-anything` (Python package com `setup.py`)
3. Instalar via `pip3 install --break-system-packages "git+https://github.com/Ianfr13/Douravita-cli.git#subdirectory=nome"`
4. Documentar em `NOME.md` no subdiretório
