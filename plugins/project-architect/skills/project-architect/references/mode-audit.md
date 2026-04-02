# AUDIT — Diagnóstico de Problemas

**Lembrete de escopo:** Você é arquiteto, não developer. O AUDIT diagnostica e corrige a **documentação** (CLAUDE.md, CONTEXT.md, routing tables, estrutura). Se encontrar bugs no código (tipos errados, migrations duplicadas, schemas inconsistentes), documente no TODO — mas NÃO edite código-fonte. O output do AUDIT deve resultar em CONTEXT.md e CLAUDE.md atualizados, não em PRs de código.

## Passo 0 — Deep Scan

Execute o Deep Scan (seção da SKILL.md).

## Passo 0.5 — Context7

Execute a Consulta de Stack (seção da SKILL.md) para as libs principais identificadas no scan. Compare patterns em uso vs docs atuais — isso alimenta o Erro 8.

## Os 8 Erros de Estrutura

Verifique em ordem. Para cada erro: reporte o que está errado, por que importa e a correção concreta.

**Erro 1 — CLAUDE.md muito longo**
**Flag se:** mais de 40-50 linhas.
**Por que importa:** queima tokens em toda sessão. O sinal se perde no ruído.
**Fix:** mantenha só identidade + workspaces + routing + convenções. Mova tudo o mais para os CONTEXT.md.

**Erro 2 — Sem routing table**
**Flag se:** sem tabela mapeando tarefas → workspace → arquivo a ler.
**Por que importa:** sem routing, o Claude adivinha qual contexto carregar. Output inconsistente.
**Fix:** adicione tabela de 3 colunas. Veja template na SKILL.md.

**Erro 3 — Workspaces demais**
**Flag se:** mais de 4-5 workspaces, ou workspaces que representam estágios do mesmo modo mental.
**Por que importa:** overhead de manutenção cresce mais que o trabalho. Context files ficam desatualizados.
**Fix:** o teste é mudança de modo mental, não tipo de tarefa.

**Erro 4 — Context descreve personalidade em vez de trabalho**
**Flag se:** instruções comportamentais ("seja criativo", "pense passo a passo") em vez de descrições do projeto.
**Por que importa:** o Claude responde mais a contexto sobre o trabalho do que sobre si mesmo.
**Fix:** 80% do context file deve descrever o trabalho, não o comportamento.

**Erro 5 — Context desatualizado**
**Flag se:** sem `Last updated:`, data antiga, ou "Claude ficou pior".
**Por que importa:** "Claude ficou pior" é quase sempre contexto stale.
**Fix:** adicione `Last updated:`. Trate como documento vivo.

**Erro 6 — Diretório plano**
**Flag se:** mais de 8-10 arquivos no mesmo nível sem subpastas.
**Por que importa:** o Claude adivinha o que pertence junto. Mais erros.
**Fix:** agrupe por workspace, depois por etapa ou tipo.

**Erro 7 — Over-built antes de usar**
**Flag se:** tempo significativo planejando antes de usar.
**Por que importa:** metade das decisões vai estar errada. Workflow hipotético, não real.
**Fix:** mínimo primeiro. Itere com base em dores reais. 15 minutos para a primeira versão.

**Erro 8 — Libs ou patterns desatualizados**
**Flag se:** o Deep Scan identificou libs com alternativas melhores, APIs deprecated, ou patterns que os docs desrecomendam.
**Por que importa:** libs sem manutenção acumulam vulnerabilidades. Patterns deprecated quebram em upgrades.
**Como verificar:** use Context7 — `npx ctx7 docs /[lib-id] "migration guide"` ou `"deprecated APIs"`.
**O que reportar:**
- Lib X versão Y → versão Z disponível com breaking changes relevantes
- Pattern X em `arquivo:linha` → docs recomendam pattern Y
- Lib X sem release há >1 ano → alternativa Z resolve o mesmo caso
**Fix:** liste trocas sugeridas com impacto e esforço. Não force — apresente como recomendação.

---

## Erros de Segurança

O Deep Scan (categoria O) coleta os fatos. Aqui você interpreta e classifica.

**Erro 9 — Secrets expostos ou mal protegidos**
**Flag se:** qualquer item em O.1 do scan retornou achados.
**Por que importa:** um secret vazado compromete todo o sistema — não importa quão bom é o resto da arquitetura. É o erro mais crítico que existe.
**Checklist de verificação (rode os comandos):**

```bash
# Arquivos .env commitados no git
git ls-files '*.env*' 2>/dev/null

# Chaves privadas no repo
git ls-files '*.pem' '*.key' '*.p12' '*.pfx' '*.jks' 2>/dev/null

# Patterns de secrets hardcoded (genérico, qualquer stack)
grep -rn --include='*.ts' --include='*.js' --include='*.py' --include='*.go' --include='*.rb' --include='*.java' --include='*.yml' --include='*.yaml' --include='*.json' --include='*.toml' \
  -E '(password|secret|token|apikey|api_key|private_key)\s*[:=]\s*["\x27][^"\x27]{8,}' \
  --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=vendor --exclude-dir=dist . || true

# .gitignore cobre secrets?
for pattern in '.env*' '*.pem' '*.key' 'credentials*' 'serviceaccount*'; do
  grep -q "$pattern" .gitignore 2>/dev/null && echo "OK: $pattern no .gitignore" || echo "FALTANDO: $pattern no .gitignore"
done
```

**Severidade:**
- Secret hardcoded em código-fonte → CRÍTICO
- `.env` commitado com valores reais → CRÍTICO
- `.gitignore` sem patterns de secrets → ALTO
- Secret em log/print → ALTO
- Secret em URL de config → MÉDIO (se o repo é privado)

**Fix:** documente no TODO com ação exata — ex: "mover `API_KEY` em `src/config.ts:12` para variável de ambiente" ou "adicionar `.env*` ao `.gitignore` e rodar `git rm --cached .env`".

**Erro 10 — Vulnerabilidades de código**
**Flag se:** qualquer item em O.2 a O.6 do scan retornou achados.
**Por que importa:** input sem validação é a porta de entrada de injection attacks. Auth fraca permite acesso não autorizado. Cada gap é uma superfície de ataque.

**O que verificar (a partir dos achados do scan):**

| Categoria | O que procurar | Severidade base |
|-----------|---------------|-----------------|
| Injection | SQL sem parameterize, HTML sem escape, shell com input dinâmico, path traversal | CRÍTICO |
| Auth gaps | Endpoints sem auth, auth bypass, sem expiração de token | CRÍTICO |
| Authz gaps | Verifica login mas não ownership do recurso | ALTO |
| CORS | `Access-Control-Allow-Origin: *` em API com auth | ALTO |
| Info leak | Stack traces em prod, PII em logs, debug endpoints expostos | MÉDIO |
| Deps | Libs com CVEs conhecidas, `eval()`/`exec()` com input dinâmico | ALTO |
| Infra | Container como root, debug em prod, HTTPS não forçado | MÉDIO |

**Fix:** cada achado vira item no TODO com:
- Arquivo:linha exato
- O que está errado (fato, não opinião)
- Sugestão de correção genérica (ex: "usar parameterized query" — não reescreva o código)
- Severidade

## Verificações Douravita

Execute e reporte:
```bash
ls .devcontainer/devcontainer.json && echo "OK: devcontainer existe" || echo "FALTANDO: devcontainer"
grep "douravita-base" .devcontainer/devcontainer.json 2>/dev/null && echo "OK: imagem base correta" || echo "ATENÇÃO: imagem base diferente"
grep "YOUR_PROJECT_ID" .devcontainer/devcontainer.json 2>/dev/null && echo "PENDENTE: substituir projectId" || echo "OK: projectId configurado"
git remote -v
```

## Após o diagnóstico — Atualizar CONTEXT.md

**Independente do que o diagnóstico encontrou**, ao final de todo AUDIT você deve:

1. **Abrir cada CONTEXT.md do projeto**
2. **Atualizar `Last updated: [YYYY-MM-DD]`** com a data de hoje — mesmo que o conteúdo esteja correto, um audit é um evento que justifica o timestamp
3. Se não existir `Last updated:`, adicionar logo abaixo do título
4. Se o Erro 5 encontrou itens desatualizados, corrigir o conteúdo também
5. Incluir no CONTEXT.md do workspace relevante um resumo dos achados de segurança (como seção "Postura de Segurança" ou similar)

O `Last updated:` é um contrato com o próximo dev — ele precisa saber quando o documento foi revisado pela última vez, não só quando foi criado.

## Formato do Output

O output DEVE ter estas 4 partes nesta ordem:

### Parte 1 — Diagnóstico (o que está errado)

Para cada erro encontrado:
- O que está errado (com arquivo:linha)
- Por que importa
- Severidade: CRÍTICO / ALTO / MÉDIO / BAIXO

### Parte 2 — Spec extraída dos scans

Resume o estado real da codebase. Inclua:
- API Contracts (endpoints, request/response shapes, auth)
- Data Stores (schemas DB, cache keys + value shapes, queue messages)
- Regras de negócio críticas
- Conexões entre workspaces
- **Postura de segurança** — resumo dos achados da categoria O do scan: como secrets são gerenciados, onde há validação de input, quais endpoints têm auth e quais não, superfície de ataque geral

Serve como referência para quem for corrigir — não precisa reler o código.

### Parte 3 — TODO checklist de correções

Lista priorizada de ações concretas:

```markdown
## TODO — Correções

### CRÍTICO
- [ ] `dashboard/CONTEXT.md` — Remover `Cloaker.tsx` da listagem (não existe)
- [ ] `dashboard/CONTEXT.md` — Adicionar `Funnels.tsx` (270 linhas), `FunnelDetail.tsx` (527 linhas)

### ALTO
- [ ] `workers/CONTEXT.md` — Adicionar handler `funnels.ts` (11 endpoints) à seção API
- [ ] `workers/CONTEXT.md` — Documentar KV keys: `funnel:{slug}`, `config:{slug}`

### MÉDIO
- [ ] Ambos CONTEXT.md — Atualizar `Last updated` para data de hoje

### SEGURANÇA
- [ ] `src/config.ts:12` — Mover `API_KEY` hardcoded para variável de ambiente
- [ ] `.gitignore` — Adicionar `.env*`, `*.pem`, `*.key`, `credentials*`
- [ ] `src/api/users.ts:34` — Adicionar validação de input (SQL injection possível via `req.query.id`)
- [ ] `src/auth/middleware.ts:8` — Endpoint `/admin/debug` sem auth check
- [ ] `workers/api/src/index.ts:15` — CORS `*` em API autenticada, restringir origens

### RECOMENDADO (libs/patterns)
- [ ] Avaliar migração de X para Y (Context7 mostrou que...)
```

Cada TODO deve ser específico para executar sem reler o diagnóstico.

Se o AUDIT encontrar CONTEXT.md muito desatualizado (Erro 5 com mais de 5 itens faltando), gere também um **rascunho do CONTEXT.md corrigido** como proposta.

### Parte 4 — Sugestões de skills

Baseado no scan completo, sugira skills que fariam diferença neste projeto. Leia `references/skill-suggestions.md` para o formato e critérios. Cada sugestão deve ser acionável via `/skill-creator`.
