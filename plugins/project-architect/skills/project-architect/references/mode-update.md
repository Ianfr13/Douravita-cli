# UPDATE — Evoluindo a Estrutura

**Protocolo:** diagnostique primeiro, apresente achados, obtenha confirmação antes de editar qualquer coisa. Nunca faça mudanças silenciosas em estrutura viva.

## Passo 0 — Deep Scan

Execute o Deep Scan (seção da SKILL.md).

## Passo 0.5 — Context7

Execute a Consulta de Stack (seção da SKILL.md) para as libs envolvidas na mudança. Garanta que qualquer implementação proposta use a API da versão atual.

## Passo 1 — Perguntas de diagnóstico

1. **Novos workspaces?** Surgiu um modo mental genuinamente novo? Aplique o teste de modo mental — não crie workspace só porque tem novo tipo de arquivo.
2. **CONTEXT.md desatualizado?** Quando foi atualizado? Ainda reflete o trabalho atual, audiência e direção?
3. **Novos CLIs?** O projeto passou a usar serviços que precisam de CLI novo?
4. **Novas skills?** Alguma skill nova deve ser adicionada ao `.claude/skills/`?
5. **CLAUDE.md ainda cabe em uma tela?** O crescimento costuma infiltrar conteúdo no CLAUDE.md. Apare o que pertence ao CONTEXT.md.
6. **Boundaries ainda fazem sentido?** Dois workspaces que na prática viraram um? Um workspace que cresceu e precisa dividir?

## Formato do Output

O output do UPDATE deve ter:

### Parte 1 — Estado atual (do Deep Scan)
- O que o projeto faz hoje (resumo dos scans)
- Fluxo de dados relevante para a mudança pedida
- Contratos e schemas envolvidos

### Parte 2 — Proposta de implementação
- Onde encaixar a mudança (justificativa baseada nos scans)
- Arquivos a criar/modificar
- Schemas/migrations novos
- Impacto em cada workspace

### Parte 3 — TODO checklist de implementação

```markdown
## TODO — Implementação

### Criar
- [ ] `path/to/new-file.ts` — Descrição do que faz
- [ ] `path/to/migration.sql` — Schema (copie o SQL proposto)

### Modificar
- [ ] `path/to/existing.ts` — O que mudar e onde (linha aproximada)
- [ ] `path/to/config.json` — Adicionar binding/rota/etc

### Documentar
- [ ] `CONTEXT.md` — Adicionar seção descrevendo a nova feature
- [ ] `CLAUDE.md` — Atualizar routing table se necessário

### Verificar
- [ ] Testar end-to-end: [descrever o fluxo de teste]
- [ ] Confirmar que [X] não quebrou
```

Cada TODO deve ser executável sem reler a proposta. Aguarde confirmação do usuário antes de executar.

Princípio: mude só o que precisa. Edições cirúrgicas.
