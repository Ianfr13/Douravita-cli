# FORK — Adaptando Repo Externo

**Pré-voo:** leia os arquivos de referência antes de responder:
- `references/devcontainer-templates.md`
- `references/infisical-setup.md`
- `references/automation-recommender.md`

## Passo 1 — Fork e clone

Se repo **público**, execute:
```bash
gh repo fork <url-do-repo> --clone --fork-name <nome>
cd <nome>
```

Se repo **privado** com acesso, execute:
```bash
gh repo clone <org>/<repo>
cd <repo>
```

Se repo privado sem acesso: informe o usuário e peça que solicite acesso ao owner.

Troubleshooting: execute `gh auth status`. Erro "repository not found" em repo privado = sem acesso.

## Passo 2 — Deep Scan

Execute o Deep Scan (seção da SKILL.md) para entender o repo existente antes de propor qualquer mudança.

## Passo 3 — Propor adaptação

Apresente ao usuário antes de gerar qualquer coisa:
- Workspaces propostos (adaptados à estrutura existente — não force boundaries que cortam código relacionado)
- Automações a instalar (CLIs, skills, subagents, hooks — via recommender)
- MCPs a migrar para CLI (se houver)
- O que **não** será tocado (código existente, configs do projeto original)

**Regra de ouro:** adicione novos arquivos, nunca sobrescreva existentes. Se já existe um `CLAUDE.md`, leia-o, combine o conteúdo e reescreva com confirmação do usuário. Não delete código, pastas ou configs do projeto original.

Aguarde confirmação explícita antes de prosseguir.

## Passo 4 — Adicionar estrutura Douravita

Após confirmação, execute os Passos 3-5 do BUILD (ver `references/mode-build.md`) adaptando ao repo existente. A estrutura se encaixa no código que existe, não o contrário.

## Passo 5 — Migrar MCPs para CLIs (CLI-first)

Se foram detectados MCP servers, prefira o CLI equivalente (postura CLI-first do recommender):
- Remova a configuração de MCP do `CLAUDE.md` ou `settings.json`
- **Descubra** o CLI correspondente no `registry.json` vivo ou no aitmpl.com e adicione no Dockerfile (se não estiver no base)
- Ver `references/automation-recommender.md` (postura CLI-first). Mantenha o MCP só se não houver CLI equivalente.

## Passo 6 — Commit e sincronização futura

Execute:
```bash
git add .
git commit -m "chore: adicionar estrutura Douravita (devcontainer, CLAUDE.md, skills)"
git push
```

Para sincronizar com o upstream quando o repo original evoluir:
```bash
git remote add upstream <url-original>
git fetch upstream
git rebase upstream/main
git push --force-with-lease origin
```

Execute o checklist de verificação do BUILD Passo 6.
