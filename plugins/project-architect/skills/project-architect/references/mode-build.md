# BUILD — Projeto Novo do Zero

**Pré-voo:** antes de responder qualquer coisa ao usuário, leia os 4 arquivos de referência:
- `references/devcontainer-templates.md`
- `references/cli-catalog.md`
- `references/infisical-setup.md`
- `references/skills-catalog.md`

## Passo 1 — Entender o projeto

Faça estas perguntas ao usuário e aguarde as respostas antes de prosseguir:

1. **O que é este projeto?** (2-3 frases: o que faz, para quem)
2. **Quais são os modos mentais de trabalho?** (ex: pesquisa vs. código vs. publicação)
3. **Qual o stack técnico principal?** (Node, Python, HTML puro, etc.)
4. **Precisa de deploy?** (Railway, Cloudflare Workers, nenhum)
5. **Quais serviços externos vai usar?** (Meta Ads, GTM, RedTrack, Supabase, etc.)
6. **Tem convenções de nomenclatura?** (padrões de nome de arquivo, pastas, etc.)

## Passo 2 — Propor CLIs, Skills e Workspaces

Com base nas respostas, prepare uma proposta e apresente ao usuário para confirmação antes de gerar qualquer arquivo:

**CLIs:** com base no `cli-catalog.md`, liste quais instalar além do base. Justifique brevemente cada um.

**Skills:** com base no `skills-catalog.md`, liste quais instalar em `.claude/skills/`. Para cada skill, diga quando o usuário vai usá-la neste projeto. Organize em **pares de workflow** (research → execução) seguindo o "Padrão de Workflow com Skills". Se uma skill de research não existe, marque para criar com `skill-creator`.

**Workspaces:** aplique o **teste de modo mental** — se você não mudaria de marcha mental entre duas tarefas, elas ficam no mesmo workspace. Sinal útil: se você quiseria que o Claude "esquecesse" o que estava fazendo — isso é um boundary de workspace. Comece com 2-3 workspaces. Quando em dúvida, junte — é sempre mais fácil dividir depois do que fundir.

Exemplos de boundaries certos:
- Pesquisa vs. escrever copy → modos diferentes ✓
- Escrever copy vs. revisar copy → mesmo modo (iteração) ✗
- Criar landing page vs. fazer deploy → depende: se a mesma pessoa faz, mesmo workspace

Aguarde confirmação explícita do usuário antes de seguir.

## Passo 3 — Gerar a estrutura

Após confirmação, crie os arquivos nesta ordem:

1. **`CLAUDE.md`** na raiz (use o template da SKILL.md)
2. **`CONTEXT.md`** em cada workspace (use o template da SKILL.md — já inclua as CLIs/Skills do Passo 2)
3. **`.devcontainer/devcontainer.json`** — use o template simples; se precisar de CLIs extras, use o template estendido com Dockerfile
4. **`.claude/skills/`** — instale as skills selecionadas (veja abaixo)
5. **`.gitignore`** básico se não existir

**Como instalar skills em `.claude/skills/`:**
- Para skills que já existem globalmente: `cp -r ~/.claude/skills/nome-da-skill .claude/skills/`
- Para skills que ainda não existem: use a skill `skill-creator` para criá-las
- Crie sempre a pasta: `mkdir -p .claude/skills/`

## Passo 4 — GitHub

Execute:
```bash
gh auth status
```
Se não logado, execute `gh auth login --web` e aguarde o usuário completar o fluxo no browser.

Após autenticado, execute:
```bash
git init
git add .
git commit -m "chore: estrutura inicial do projeto"
gh repo create <nome-do-repo> --private --source=. --remote=origin --push
```

Use `--public` apenas se o usuário pedir explicitamente.

## Passo 5 — Infisical

Guie o usuário (esta etapa requer ação manual no browser):
1. Acesse `https://sec.douravita.com.br` e crie um novo projeto com o nome do repo
2. Copie o `projectId` (aparece na URL ou nas configurações do projeto)
3. Substitua `YOUR_PROJECT_ID` no `postStartCommand` do `devcontainer.json`

Após o usuário informar o `projectId`, faça a substituição no arquivo e confirme.

Leia `references/infisical-setup.md` para o passo a passo completo.

## Passo 6 — Checklist de verificação

Execute e reporte:
```bash
git remote -v
grep "YOUR_PROJECT_ID" .devcontainer/devcontainer.json && echo "PENDENTE: substituir projectId" || echo "OK: projectId configurado"
```

Instrua o usuário a:
1. Abrir o devcontainer no VS Code (`Reopen in Container`)
2. Dentro do container: verificar se o Claude Code está logado (`claude --version`)
3. Se secrets não carregam: verificar INFISICAL_CLIENT_ID e INFISICAL_CLIENT_SECRET no `~/.zshrc` do host

Dê um próximo passo concreto ao final.
