# Automation Recommender — Douravita (dinâmico)

Depois do Deep Scan (ou, no BUILD/FORK, das respostas do usuário sobre o projeto), recomende automações sob medida. **Nada de catálogo fixo.** As tabelas aqui são **sementes** — o trabalho de verdade é descobrir, na hora, as tools/agents/skills/hooks que casam com o stack real do projeto.

## Princípio

Pergunta-guia: **"que sinal a codebase emite, e qual automação ataca esse sinal?"**

A fonte dos sinais é o **inventário do Deep Scan** (stack, contratos de API, data stores, auth, error handling, testes, segurança, jobs). No BUILD/FORK sem código ainda, os sinais são as respostas do usuário sobre stack e serviços externos.

Você cobre as **5 formas de extensão** do Claude Code:

| Tipo | Pra quê |
|------|---------|
| **CLIs** | Ações em serviços externos via terminal (a Douravita é CLI-first) |
| **Skills** | Conhecimento/workflows empacotados, invocáveis por `/nome` |
| **Subagents** | Revisores/analisadores especializados, rodam em paralelo |
| **Hooks** | Ações automáticas em eventos de tool (format, lint, bloquear edição) |
| **MCP servers** | Integração com serviço externo **quando não há CLI equivalente** |

## Postura Douravita: CLI-first

Antes de recomendar um MCP server, cheque se existe um **CLI** que resolve (no registry da Douravita ou de terceiros). Recomende MCP só quando não houver CLI equivalente — o terminal é auditável, versionável e não consome contexto com tools sempre carregadas. (Isso substitui o antigo guia "migrar MCP → CLI".)

## Motor de descoberta — é aqui que mora o "nada fixo"

Para cada categoria, **descubra na hora** — não dependa de memória nem de lista estática:

### 1. CLIs Douravita → registry vivo

O catálogo de CLIs da Douravita é o `registry.json` do repo `Douravita-cli`. **Leia-o sempre fresco**, nunca de memória:

```bash
# Da fonte (sempre atual):
curl -fsSL https://raw.githubusercontent.com/Ianfr13/Douravita-cli/main/registry.json
# Ou local, se o repo estiver clonado:
cat /caminho/para/Douravita-cli/registry.json
```

Cada entrada tem `name`, `description`, `requires`, `install_cmd`, `category`. Filtre por `category`/`description` que casem com os serviços que o scan detectou e use o `install_cmd` verbatim.

### 2. Agents / Skills / Commands / Hooks / MCPs → Claude Code Templates + GitHub

Catálogo comunitário (aitmpl.com / repo `davila7/claude-code-templates`): 600+ agents, 200+ commands, 55+ MCPs, 39+ hooks, skills. Browse em `https://www.aitmpl.com` e instale via `npx` (zero install global, catálogo sempre `@latest`):

```bash
npx claude-code-templates@latest --agent   <categoria/nome> --yes
npx claude-code-templates@latest --skill   <nome>           --yes
npx claude-code-templates@latest --command <categoria/nome> --yes
npx claude-code-templates@latest --hook    <categoria/nome> --yes
npx claude-code-templates@latest --mcp     <categoria/nome> --yes
npx claude-code-templates@latest                                  # interativo (browse)
```

Pegue o `<categoria/nome>` exato navegando no aitmpl.com — não chute o path. Para algo específico do stack que não esteja lá, **busque no GitHub** (ex: `awesome-claude-code`, coleções de subagents) e na web (`[framework/serviço] + "claude code agent/skill/hook"`).

### 3. Libs/SDKs do stack → Context7

Para validar patterns e achar tooling de uma lib específica, use Context7 (ver `references/documentation-lookup.md`).

### Regra de ouro

Trate **toda tabela-semente abaixo como ponto de partida, não verdade**. Se o stack do projeto tem uma tool melhor ou mais específica, descubra e recomende ela — mesmo que não esteja em lista nenhuma. (É o que o claude-code-setup chama de *"go beyond the reference lists"*.)

## Sementes: sinal → recomendação (NÃO-exaustivo — sempre confirme no registry/aitmpl)

### CLIs (pegue o `install_cmd` real no registry)
| Sinal no scan | Procure no registry |
|---|---|
| Paid ads (Meta/Facebook/Instagram) | CLI de Meta Ads |
| Tracking/analytics (GTM, pixels) | CLI de Google Tag Manager |
| Atribuição / performance marketing | CLI de RedTrack |
| Deploy de servidor | Railway CLI |
| Secrets manipulados via código | wrapper do Infisical |
| Observabilidade de LLM | Langfuse |
| Deploy Cloudflare | wrangler |
| Backend Supabase | supabase |
| Browser / E2E | playwright |
| GitHub ops | gh |

### Skills (descubra no aitmpl/GitHub; ou crie via `/skill-creator`)
| Sinal | Direção |
|---|---|
| Tarefa repetida com ordem (deploy multi-step) | skill de execução sob medida |
| Domínio externo com regras (Stripe, Meta API) | skill de integração |
| Scaffolding repetitivo (endpoints, components) | skill de geração |
| Gap de segurança recorrente | skill de security checklist |

### Subagents (descubra no aitmpl)
| Sinal | Direção |
|---|---|
| Codebase grande (>500 arquivos) | code-reviewer paralelo |
| Auth / pagamentos | security-reviewer |
| Projeto de API | api-documenter |
| Muito frontend | ui / accessibility reviewer |
| Gaps de teste | test-writer |

### Hooks (descubra no aitmpl)
| Sinal (config detectada) | Direção |
|---|---|
| Prettier / ESLint / Ruff configurado | PostToolUse: format/lint on edit |
| Projeto TypeScript | PostToolUse: type-check on edit |
| `.env` / lock files presentes | PreToolUse: bloquear edição |
| Código sensível (auth/payments) | PreToolUse: exigir confirmação |

### MCP servers (só se NÃO houver CLI equivalente)
| Sinal | Direção |
|---|---|
| Lib popular sem CLI | context7 (docs ao vivo) |
| Serviço externo sem CLI equivalente | MCP do serviço |

## Como pensar numa boa recomendação

A pergunta não é "que automação seria legal?" — é **"que tarefa o dev vai repetir, e que automação ataca um sinal real do scan?"** Uma boa candidata tem ≥2 destes sinais:

- **Repetição** — tarefa que volta toda semana
- **Contexto especializado** — regras que dependem de várias variáveis
- **Multi-step com ordem** — sequência fácil de errar
- **Domínio externo** — API com regras próprias
- **Risco de erro** — já quebrou prod por isso
- **Segurança recorrente** — cada feature nova precisa do mesmo checklist

Fontes de sinal no scan: Stack (B), Contratos (C), Fluxos de config (H), Error handling (I), Segurança (O), Testes (L), Jobs (J).

## O que NÃO recomendar

- Automação que já existe no projeto (cheque `.claude/`)
- Genérica demais ("uma skill de coding") — precisa de domínio/workflow específico
- Para tarefa que acontece uma vez (isso é tarefa, não automação)
- MCP quando há CLI equivalente

## Output — `setup-recommendations.md`

Recomende **1-2 por categoria** (3-5 se o usuário pedir um tipo específico). Pule categorias irrelevantes. Para cada item, diga **por que** (citando o achado do scan) e o **comando concreto** de obter:

```markdown
## Recomendações de Automação — [Projeto]

### Perfil (do Deep Scan)
- Stack: [...]
- Serviços externos: [...]
- Sinais-chave: [...]

### 🔌 CLIs
#### [nome]
- **Por que:** [sinal do scan — cite a área/achado]
- **Instalar:** `[install_cmd do registry]`

### 🎯 Skills
#### [nome]
- **Por que:** [sinal]
- **Obter:** `npx claude-code-templates@latest --skill [nome] --yes` (ou criar via `/skill-creator`)
- **Invocação:** user-only / both / claude-only

### 🤖 Subagents
#### [nome]
- **Por que:** [sinal]
- **Obter:** `npx claude-code-templates@latest --agent [cat/nome] --yes`

### ⚡ Hooks
#### [nome]
- **Por que:** [config detectada]
- **Obter:** `npx claude-code-templates@latest --hook [cat/nome] --yes` (ou escrever em `.claude/settings.json`)

### 🔗 MCP servers (só se não houver CLI)
#### [nome]
- **Por que:** [sinal + por que não dá pra resolver com CLI]
- **Obter:** `npx claude-code-templates@latest --mcp [cat/nome] --yes`

**Quer mais de alguma categoria?** É só pedir (ex: "mais opções de hook").
```

## Instalar — perguntar antes

A skill **age**, mas com confirmação explícita. Depois de gerar `setup-recommendations.md`:

1. **Apresente a lista** ao usuário.
2. **Pergunte quais instalar.** Não rode nada sem o "ok".
3. **Instale os escolhidos** — `npx claude-code-templates@latest …`, CLIs do registry (`install_cmd`), `cp` de skills para `.claude/skills/`. Para hooks/MCP que mexem em `settings.json` ou secrets, mostre o diff e confirme de novo.
4. O que o usuário não escolheu **fica no `setup-recommendations.md`** como handoff acionável.

## Quando gerar

- **AUDIT** — sempre (o scan completo dá visibilidade total dos gaps).
- **MIGRATION** — sempre (projeto chegando ao workflow Douravita merece automações sob medida).
- **UPDATE** — se a mudança traz domínio novo ou workflow repetitivo.
- **BUILD / FORK** — no passo de propor a estrutura, a partir das respostas e do stack.
