# Skills Catalog — Douravita

Skills são instaladas por projeto em `.claude/skills/` dentro do repo. Apenas config básica vai no global `~/.claude/`.

Use este catálogo para decidir quais skills instalar ao configurar um novo projeto.

---

## Skills Disponíveis

| Skill | O que faz | Instalar quando |
|-------|-----------|----------------|
| `project-architect` | Setup completo de projetos — devcontainer, Infisical, GitHub, estrutura 3 layers | **Global** (`~/.claude/skills/`) — disponível para todos os projetos |
| `folder-architect` | Auditoria e build de estrutura 3 layers (CLAUDE.md → CONTEXT.md → Skills) | Projetos que precisam de organização de workspace |
| `skill-creator` | Criar, testar e iterar skills novas | Projetos onde você vai criar skills |
| `vsl-copywriting` | VSLs e copy de vendas usando o Método Derick | Projetos de copy/vendas |
| `seo-blog-architect` | Blog posts SEO de alta conversão (contexto Douravita 55+) | Projetos com blog/conteúdo |
| `youtube-strategist` | Estratégia de canal YouTube (pesquisa + planejamento) | Projetos com canal YouTube |
| `claude-api` | Apps com Claude API / Anthropic SDK | Projetos que integram AI via API |

---

## Guia de Seleção por Tipo de Projeto

| Tipo de projeto | Skills recomendadas |
|----------------|---------------------|
| Landing page de produto | `vsl-copywriting` |
| Blog / conteúdo | `seo-blog-architect` |
| Canal YouTube | `youtube-strategist` |
| App/ferramenta com AI | `claude-api`, `skill-creator` |
| Ferramenta interna | `skill-creator` (se vai criar skills) |
| Marketing ops (ads, tracking) | `skill-creator` (criar skills específicas) |
| Novo projeto qualquer | `folder-architect` (se estrutura complexa) |

---

## Como Instalar uma Skill num Projeto

Skills são diretórios com um `SKILL.md` dentro de `.claude/skills/` no repo.

**Opção A — Copiar de outro repo:**
```bash
cp -r /caminho/para/skill-origem/.claude/skills/nome-da-skill .claude/skills/
```

**Opção B — Copiar de global:**
```bash
cp -r ~/.claude/skills/nome-da-skill .claude/skills/
```

**Opção C — Criar do zero:**
Use a skill `skill-creator` para criar uma nova skill específica para o projeto.

---

## Estrutura de Skills no Projeto

```
.claude/
└── skills/
    ├── nome-da-skill/
    │   ├── SKILL.md           ← obrigatório
    │   └── references/        ← opcional, docs de referência
    └── outra-skill/
        └── SKILL.md
```

---

## Criando Skills Novas

Se o projeto precisar de uma skill que não existe ainda, use `skill-creator`:

1. Descreva o workflow que a skill deve capturar
2. A skill-creator vai draftar, testar com casos reais e iterar
3. Salve a skill final em `.claude/skills/` do projeto
4. Se for útil para outros projetos, considere mover para o global `~/.claude/skills/`

**Princípio:** skills específicas de domínio ficam no projeto. Skills de workflow geral (project-architect, skill-creator) ficam global.
