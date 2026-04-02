# AUDIT — Diagnóstico de Problemas

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

## Verificações Douravita

Execute e reporte:
```bash
ls .devcontainer/devcontainer.json && echo "OK: devcontainer existe" || echo "FALTANDO: devcontainer"
grep "douravita-base" .devcontainer/devcontainer.json 2>/dev/null && echo "OK: imagem base correta" || echo "ATENÇÃO: imagem base diferente"
grep "YOUR_PROJECT_ID" .devcontainer/devcontainer.json 2>/dev/null && echo "PENDENTE: substituir projectId" || echo "OK: projectId configurado"
git remote -v
```

## Formato do Output

O output DEVE ter estas 3 partes nesta ordem:

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

### RECOMENDADO (libs/patterns)
- [ ] Avaliar migração de X para Y (Context7 mostrou que...)
```

Cada TODO deve ser específico para executar sem reler o diagnóstico.

Se o AUDIT encontrar CONTEXT.md muito desatualizado (Erro 5 com mais de 5 itens faltando), gere também um **rascunho do CONTEXT.md corrigido** como proposta.
