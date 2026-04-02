# UPDATE — Evoluindo a Estrutura

**Lembrete de escopo:** Você propõe a arquitetura da mudança e atualiza a documentação (CLAUDE.md, CONTEXT.md). O TODO de implementação lista o que o developer vai criar/modificar no código — mas você não escreve o código. Você garante que a estrutura e documentação estejam prontas para o dev executar.

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

## Passo 1.5 — Verificação de segurança

A cada UPDATE, rode uma verificação rápida de segurança nas áreas impactadas pela mudança. O objetivo não é um audit completo — é garantir que a mudança proposta não introduza (ou perpetue) riscos óbvios.

**Secrets:**
```bash
# .env commitados
git ls-files '*.env*' 2>/dev/null
# Secrets hardcoded nas áreas afetadas
grep -rn -E '(password|secret|token|apikey|api_key|private_key)\s*[:=]\s*["\x27][^"\x27]{8,}' [paths-afetados] --exclude-dir=node_modules --exclude-dir=.git || true
# .gitignore cobre o básico
for p in '.env*' '*.pem' '*.key'; do grep -q "$p" .gitignore 2>/dev/null && echo "OK: $p" || echo "FALTA: $p"; done
```

**Código (nas áreas da mudança):**
- Novos endpoints/handlers → têm auth? Têm validação de input?
- Novas queries/operações de banco → são parametrizadas?
- Novo input de usuário → é sanitizado antes de usar em HTML/SQL/shell/paths?
- Novas dependências → são mantidas e sem CVEs conhecidas?
- Novos logs → incluem dados sensíveis?

Se encontrar riscos, adicione-os na seção SEGURANÇA do TODO (Parte 3). A mudança proposta deve resolver ou ao menos não agravar problemas de segurança existentes.

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
- [ ] **Todos** os `CONTEXT.md` afetados — Adicionar seção descrevendo a nova feature + atualizar `Last updated: [YYYY-MM-DD]`
- [ ] `CLAUDE.md` — Atualizar routing table se necessário

### Segurança
- [ ] `path/to/file.ts:NN` — [risco encontrado + sugestão de correção]

### Verificar
- [ ] Testar end-to-end: [descrever o fluxo de teste]
- [ ] Confirmar que [X] não quebrou
```

Cada TODO deve ser executável sem reler a proposta. Aguarde confirmação do usuário antes de executar.

### Parte 4 — Sugestões de skills (se aplicável)

Se a mudança introduz um domínio novo ou workflow repetitivo, sugira skills. Leia `references/skill-suggestions.md` para o formato e critérios. Só inclua esta parte se houver sugestão concreta — não force.

Princípio: mude só o que precisa. Edições cirúrgicas.
