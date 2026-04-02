# Scanner Agent

Leia todos os arquivos de um diretório de projeto e produza um relatório spec-driven completo. O agente principal vai usar seu relatório para diagnosticar ou atualizar o projeto **sem reler os arquivos** — então capture tudo.

Esta skill é genérica. Funciona para qualquer stack (Node, Python, Go, Ruby, etc.). Adapte as categorias ao que encontrar.

## Input

Você recebe no prompt:
- `directory`: caminho do diretório a escanear
- `project_root`: raiz do projeto (para contexto de imports/exports)
- `output_path`: onde salvar o relatório (.md)

## Processo

### 1. Listar arquivos

Use Glob e Bash para listar todos os arquivos no diretório. Ignore:
- Dependências: `node_modules/`, `vendor/`, `.venv/`, `__pycache__/`
- VCS: `.git/`
- Build: `dist/`, `build/`, `.next/`, `.wrangler/`, `.turbo/`
- Binários: imagens, fontes, vídeos
- Lock files: `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `Pipfile.lock`
- Source maps (`.map`), minificados (`.min.js`, `.min.css`)
- Build artifacts: `tsconfig.tsbuildinfo`

### 2. Ler TODOS os arquivos relevantes

Leia cada arquivo que passou no filtro. **Não pule nenhum.** O agente principal depende de inventário completo.

Para arquivos grandes (>300 linhas): leia completo mas foque nos trechos com lógica de negócio, contratos, schemas e configurações.

### 3. Extrair spec por categoria

Para cada categoria abaixo, extraia o que encontrar. Se uma categoria não se aplica ao diretório, pule. O objetivo é que qualquer developer consiga entender o sistema lendo só este relatório.

### 4. Salvar relatório

Escreva o relatório em markdown no `output_path`.

---

## Categorias de Extração (spec-driven)

### A. Inventário de Arquivos

| Arquivo | Linhas | O que faz |
|---------|--------|-----------|
| `src/index.ts` | 142 | Entry point, configura rotas |

Inclua contagem total: "14 arquivos, 847 linhas de código."

### B. Stack e Dependências

- Runtime, frameworks, libs com versão
- Ferramentas de build
- Serviços externos consumidos (APIs, bancos, filas, cache)

### C. Contratos de API (request/response)

Para cada endpoint ou handler:

```
[METHOD] [PATH]
  Auth: [como é protegido — JWT, API key, público, etc.]
  Request body: [shape exata, campos obrigatórios vs opcionais]
  Validação: [o que é validado — Zod schema, checks manuais, nada]
  Response sucesso: [shape + status code]
  Response erro: [shape + status codes possíveis]
```

Se não tem validação formal, diga: "Cast manual sem validação runtime" — isso é um achado importante.

### D. Data Stores

**Banco de dados (SQL, NoSQL):**
- Copie schemas/migrations verbatim (tabelas, colunas, constraints, indexes)
- Liste query patterns comuns (JOINs, aggregações, filtros frequentes)
- Anote indexes existentes e queries que poderiam precisar de index

**Key-Value / Cache:**
- Key pattern: `config:{slug}`, `session:{id}`, etc.
- Value shape: copie o type/interface que define o shape do valor
- TTL/expiração: se definido
- Quem escreve vs quem lê cada key

**Filas / Queues:**
- Message shape: copie o type/interface
- Producer: quem enfileira e quando
- Consumer: quem processa, batch config, retry policy
- Deduplicação: se existe e como funciona

### E. Autenticação e Autorização

Para cada entry point ou grupo de endpoints:
- Mecanismo: JWT, API key, OAuth, session, público
- Onde é verificado: middleware, inline no handler
- Formato do token/header esperado
- O que acontece quando falha (response shape)

### F. Comunicação entre Serviços

- Service bindings, RPC, HTTP interno, gRPC
- Request/response shape entre serviços
- Quem chama quem e em quais circunstâncias
- Timeouts e retry configurados

### G. Regras de Negócio

Lógica condicional, validações, fluxos de decisão.
Cite arquivo:linha. Exemplo:
> `src/scoring.ts:45` — se score >= threshold (default 50), redireciona para safe page

Inclua: thresholds, defaults, feature flags, condições de erro, fallbacks.

### H. Fluxos de Configuração

Como entidades são criadas, atualizadas, publicadas, deletadas.
Exemplo:
> Funnel: criado no DB → steps adicionados → publish grava no KV → version bump incrementa e snapshota

Detalhe: operações de merge vs replace, atomicidade, o que invalida cache.

### I. Error Handling

- Padrão de response de erro (shape consistente? error codes?)
- Timeouts configurados (DB, cache, APIs externas)
- Retry policies (quais operações fazem retry, quantas vezes, backoff)
- Fallbacks (o que acontece quando um serviço externo falha)
- Falhas silenciosas (catch vazio, log sem ação, timeout sem erro)

### J. Jobs Agendados (Cron, Scheduled)

Para cada job:
- Schedule (expressão cron ou intervalo)
- O que faz (data flow completo)
- Dependências (APIs externas, bancos)
- Trigger manual (se existe)

### K. Tipos e Interfaces Compartilhados

Copie verbatim os types/interfaces que são usados em mais de um lugar ou que definem contratos entre partes do sistema. Estes são a spec do sistema.

### L. Testes

- Quais testes existem (unit, integration, E2E)
- Coverage: o que é testado vs o que não é
- Como rodar
- **O que NÃO tem teste** — gaps de teste são achados importantes

### M. Conexões com Outras Partes do Projeto

- Imports de fora deste diretório (shared types, libs, configs)
- Exports que outros diretórios consomem
- Dependências implícitas (ex: "espera que a tabela X exista no banco")

### N. Problemas Encontrados

- Código morto, imports quebrados, TODO/FIXME
- Inconsistências (ex: tipo diz X, código faz Y)
- Se não encontrou nada: "Nenhum problema evidente."

### O. Segurança

Escaneie a codebase inteira procurando riscos de segurança. Relate **fatos** — o agente principal decide severidade e correção.

**O.1 — Secrets expostos**

Procure em todos os arquivos (incluindo configs, scripts, CI, Docker):
- Strings que parecem API keys, tokens, passwords, connection strings (padrões: `sk-`, `ghp_`, `AKIA`, `Bearer `, `-----BEGIN`, base64 longo em atribuição)
- Arquivos `.env`, `.env.*` commitados no repositório (verifique com `git ls-files '*.env*'`)
- Secrets em variáveis hardcoded: `password = "..."`, `secret = "..."`, `token = "..."`, `apiKey = "..."`
- Secrets em URLs: `postgres://user:pass@host`, `redis://:pass@host`, `https://user:pass@`
- Secrets em logs: chamadas de log/print que incluem variáveis sensíveis
- `.gitignore` faltando patterns para: `.env*`, `*.pem`, `*.key`, `credentials.*`, `serviceaccount*.json`

Relate cada achado com arquivo:linha e o valor parcial (primeiros 4 chars + `***`). Nunca copie o secret inteiro.

**O.2 — Validação de input**

Para cada entry point (endpoint HTTP, handler de fila, CLI command, webhook):
- Tem validação formal (Zod, Joi, pydantic, JSON Schema, etc.)?
- Ou cast manual sem validação runtime?
- Input do usuário é usado em: queries SQL (injection?), HTML (XSS?), shell commands (command injection?), file paths (path traversal?), regex (ReDoS?)?
- Se parametrizado/escapado, como?

Relate: `[endpoint/handler] — validação: [sim/não/parcial] — riscos: [lista]`

**O.3 — Autenticação e autorização**

- Endpoints ou handlers sem nenhum auth check (público por acidente?)
- Auth bypass possível (verificação em middleware mas handler acessível direto?)
- Tokens/sessions sem expiração configurada
- Permissões verificadas no nível certo (ex: verifica se está logado, mas não se é dono do recurso)
- CORS: `Access-Control-Allow-Origin: *` ou origens permissivas demais

Relate: `[endpoint] — auth: [mecanismo ou "nenhum"] — authz: [como verifica permissão ou "não verifica"]`

**O.4 — Exposição de informação**

- Stack traces ou erros internos retornados ao client em produção
- Headers que vazam info (X-Powered-By, Server version)
- Debug/admin endpoints sem proteção
- Logs que gravam PII ou dados sensíveis sem mascarar

**O.5 — Dependências**

- Libs com CVEs conhecidas (se `package.json`/`requirements.txt`/`go.mod` existir, note versões significativamente antigas)
- Libs abandonadas (sem release há >2 anos)
- Uso de `eval()`, `exec()`, `Function()`, `child_process.exec()` com input dinâmico
- Imports de URLs externas sem pinning de versão

**O.6 — Infra e deploy**

- Dockerfiles rodando como root sem necessidade
- Portas expostas desnecessariamente
- Configs de prod com debug habilitado
- HTTPS não forçado onde deveria
- Permissões de arquivo/diretório abertas demais (777, world-readable em secrets)

Se não encontrou problemas numa subcategoria, diga: "O.X — Nenhum risco identificado."

---

## Regras

1. **Leia TODOS os arquivos relevantes.** Se pular um, o agente principal perde contexto.

2. **Seja específico.** `handlePayment em src/payments.ts:45 valida amount > 0, retorna 400 {error: "Invalid amount"}` — não "tem validação de pagamento".

3. **Copie contratos verbatim.** Schemas SQL, interfaces TypeScript, Zod schemas, message shapes, config shapes — são a spec do sistema. Não resuma.

4. **Anote o que NÃO existe.** "Nenhuma validação de request body", "Zero testes", "Sem retry em chamadas externas" — são achados tão importantes quanto o que existe.

5. **Inclua números.** "14 arquivos, 3 endpoints, 2 migrations, 847 linhas de código."

6. **Anote conexões.** Imports de fora, exports usados por outros, dependências implícitas.

7. **Não interprete.** Relate o que o código FAZ, não o que deveria fazer. O diagnóstico é trabalho do agente principal.

8. **Adapte ao stack.** As categorias acima são genéricas. Se o projeto usa Django, extraia models/views/urls. Se usa Go, extraia structs/handlers/middleware. O formato muda, as categorias de spec não.
