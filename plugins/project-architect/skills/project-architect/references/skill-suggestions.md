# Skill Suggestions — Sugestões de Skills para o Projeto

Após o Deep Scan e a análise de segurança, você tem um inventário completo do que o projeto faz, como faz e onde tem gaps. Use esse conhecimento para sugerir skills que fariam diferença real no dia a dia do projeto.

## Quando gerar sugestões

- **AUDIT** — sempre. É o momento natural de olhar o projeto de fora e ver o que falta.
- **UPDATE** — se a mudança proposta envolve um workflow repetitivo ou um domínio novo.
- **MIGRATION** — sempre. Projeto chegando ao workflow Douravita merece skills sob medida.

## Como pensar em sugestões

A pergunta não é "que skill seria legal?" — é **"que tarefa o dev vai repetir neste projeto e que beneficiaria de contexto persistente?"**

Uma boa skill candidata tem pelo menos 2 destes sinais:

| Sinal | Exemplo |
|-------|---------|
| **Repetição** | "Toda semana alguém cria uma nova landing page com a mesma estrutura" |
| **Contexto especializado** | "As regras de cloaking dependem de 5 variáveis que mudam por campanha" |
| **Multi-step com ordem** | "Deploy precisa: migration → seed KV → wrangler deploy → purge cache" |
| **Domínio externo** | "Integração com Stripe/RedTrack/Meta Ads tem regras específicas da API" |
| **Risco de erro** | "Já quebramos prod 2x por esquecer de rodar migration antes do deploy" |
| **Segurança recorrente** | "Cada endpoint novo precisa: auth check, input validation, rate limit" |

## Fontes de dados para sugestões

Use o que o scan já coletou — não precisa ler mais nada:

1. **Stack e dependências (B)** — APIs externas e serviços consumidos indicam domínios de integração
2. **Contratos de API (C)** — patterns repetitivos de endpoints sugerem skill de scaffolding
3. **Fluxos de configuração (H)** — fluxos multi-step que o dev precisa lembrar
4. **Error handling (I)** — retry/fallback patterns complexos que seriam melhor documentados numa skill
5. **Segurança (O)** — gaps recorrentes sugerem skill de security checklist
6. **Testes (L)** — gaps de teste sugerem skill de test scaffolding
7. **Jobs agendados (J)** — cron jobs com lógica complexa que precisam de manutenção

## O que NÃO sugerir

- Skills que já existem no projeto (cheque `.claude/skills/`)
- Skills que já existem no catálogo global (cheque `skills-catalog.md`) — a menos que a versão global não cubra o caso específico do projeto
- Skills genéricas demais ("uma skill de coding") — precisa de domínio ou workflow específico
- Skills para tarefas que acontecem uma vez ("migrar de X para Y" — isso é uma tarefa, não uma skill)

## Formato da sugestão

Para cada skill sugerida:

```markdown
### [nome-da-skill]

**O que faz:** [1 frase — a ação concreta]
**Por que este projeto precisa:** [baseado no scan — cite o achado que motivou a sugestão]
**Trigger:** [quando o dev usaria — frase natural]
**Tipo:** research | execução | par (research + execução)
**Prioridade:** alta | média | baixa
**Esforço para criar:** pequeno (< 1h) | médio (1-3h) | grande (> 3h)
```

**Exemplo real:**

```markdown
### deploy-checklist

**O que faz:** Guia passo-a-passo de deploy com verificações de segurança, migrations e rollback.
**Por que este projeto precisa:** Scan encontrou 3 workers com wrangler.jsonc, 8 migrations D1, e zero documentação de deploy. O fluxo de deploy depende de ordem específica (migration → KV seed → worker deploy → cache purge) que não está documentada em lugar nenhum.
**Trigger:** "deployar", "fazer deploy", "publicar worker", "atualizar produção"
**Tipo:** execução
**Prioridade:** alta
**Esforço para criar:** médio
```

## Quantas sugerir

- **3-5 sugestões** é o ideal. Menos que 3 pode estar deixando oportunidades de fora. Mais que 5 vira lista de desejos.
- Ordene por prioridade (alta primeiro).
- Se o projeto é simples e realmente não precisa de mais skills, diga: "Nenhuma skill adicional recomendada — o catálogo atual cobre os workflows do projeto."

## Integração com skill-creator

Cada sugestão deve ser criável via `/skill-creator`. O formato acima é desenhado para ser o input inicial de uma sessão de skill-creator — o dev pode copiar a sugestão e começar direto.
