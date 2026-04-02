# Documentation Lookup — Context7

Consulta de documentação atualizada de qualquer lib/framework via Context7.
Dois métodos: MCP (se disponível) ou CLI (sempre funciona via npx, sem instalar).

---

## Método 1: MCP (preferido se as tools estiverem disponíveis)

```
1. mcp__context7__resolve-library-id  → resolve nome da lib para ID
   Params: libraryName, query
2. mcp__context7__query-docs          → consulta docs
   Params: libraryId (ex: /vercel/next.js), query
```

Escolha o melhor match por: name similarity > benchmark score > source reputation.

## Método 2: CLI via npx (sempre funciona, zero install)

```bash
# Passo 1 — Resolver nome → Library ID
npx ctx7 library react "How to use useEffect cleanup"
# Output inclui: /facebook/react (Library ID)

# Passo 2 — Consultar docs com ID
npx ctx7 docs /facebook/react "useEffect cleanup with async"

# Output JSON (para parsing programático)
npx ctx7 docs /facebook/react "question" --json
```

### Exemplos por stack

```bash
# Node/TypeScript
npx ctx7 library hono "middleware routing"
npx ctx7 docs /honojs/hono "how to add middleware"

# Python
npx ctx7 library fastapi "dependency injection"
npx ctx7 docs /tiangolo/fastapi "dependency injection pattern"

# Frontend
npx ctx7 library "tailwind css" "v4 configuration"
npx ctx7 docs /tailwindlabs/tailwindcss "v4 migration"

# ORM/Banco
npx ctx7 library drizzle "sqlite"
npx ctx7 docs /drizzle-team/drizzle-orm "d1 setup"

# Cloud
npx ctx7 library "cloudflare workers" "queues"
npx ctx7 docs /cloudflare/cloudflare-docs "workers queues producer consumer"
```

---

## Regras

- **Library ID sempre começa com `/`** — `/facebook/react`, `/honojs/hono`
- **Queries específicas > keywords** — "How to set up JWT auth middleware in Hono" > "auth"
- **Máximo 3 consultas por lib** — foque no relevante
- **Não envie secrets** em queries
- Se MCP disponível, prefira MCP. Se não, use `npx ctx7`.

## Quando usar (dentro do project-architect)

- **Após Deep Scan:** verificar se o projeto usa patterns/APIs atuais
- **Antes de propor implementação:** garantir que o código sugerido segue a API da versão atual
- **No AUDIT:** identificar libs deprecated ou com alternativas melhores
- **No BUILD:** escolher libs corretas com patterns atuais desde o início

## Quando NÃO usar

- Libs internas do projeto (não estão no Context7)
- Conceitos genéricos de programação
- Business logic sem dependência de lib
