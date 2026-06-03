#!/bin/bash
# Hook: enforce-deep-scan (project-architect)
#
# Garante que a codebase seja escaneada via WORKFLOW de Deep Scan antes de o agente
# PRINCIPAL ler arquivos de fonte do projeto diretamente. Os scanner-agents do Workflow
# (sub-agentes) leem livremente — a trava existe só para o loop principal, para forçá-lo
# a ATIVAR O WORKFLOW em vez de ler a codebase crua, arquivo por arquivo, no contexto.
#
# Ativação:  a skill grava a raiz do projeto em /tmp/.require-deep-scan no início de
#            AUDIT / UPDATE / FORK / MIGRATION.
# Liberação: a leitura é permitida quando QUALQUER uma vale:
#            (a) a chamada vem de um sub-agente  → campo `agent_id` no payload (stdin)
#            (b) o scan já produziu relatórios    → /tmp/project-scan/*.md existem
#            (c) o scan está em andamento         → marker /tmp/project-scan/.scanning
#            (d) o alvo não é fonte do projeto    → fora da raiz, .md, .git, .claude, /tmp
#
# Exit codes:  0 = permitir   |   2 = bloquear (stdout vira a mensagem de erro pro modelo)

FLAG=/tmp/.require-deep-scan
SCAN_DIR=/tmp/project-scan

# (sem flag) Não estamos em modo de scan → permitir tudo.
[ ! -f "$FLAG" ] && exit 0

# (b) Scan concluído — há relatórios .md → permitir.
[ "$(find "$SCAN_DIR" -maxdepth 1 -name '*.md' 2>/dev/null | wc -l)" -gt 0 ] && exit 0

# (c) Scan em andamento — marker presente → permitir (cobre os scanner-agents do Workflow
#     mesmo que o hook dispare dentro deles sem `agent_id`).
[ -f "$SCAN_DIR/.scanning" ] && exit 0

# Ler o payload do tool use (JSON via stdin).
INPUT=$(cat)

# (a) Chamada de SUB-AGENTE → permitir. Sub-agentes têm `agent_id` no payload; o agente
#     principal, não. Assim os scanners leem a codebase à vontade.
if printf '%s' "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); sys.exit(0 if d.get('agent_id') else 1)" 2>/dev/null; then
  exit 0
fi

# Raiz do projeto: conteúdo do flag (fallback p/ CLAUDE_PROJECT_DIR).
ROOT=$(head -n1 "$FLAG" 2>/dev/null | tr -d '[:space:]')
[ -z "$ROOT" ] && ROOT="${CLAUDE_PROJECT_DIR:-}"
# Sem raiz conhecida → permitir (safety: não dá pra decidir o que é "do projeto").
[ -z "$ROOT" ] && exit 0

# Caminho alvo. Read usa tool_input.file_path; Grep usa tool_input.path.
# Fallback para o formato antigo (campo no topo) por robustez entre versões.
FILE_PATH=$(printf '%s' "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
ti = d.get('tool_input') or {}
print(ti.get('file_path') or ti.get('path') or d.get('file_path') or d.get('path') or '')
" 2>/dev/null)
# Sem caminho (ex: Grep sem path) → permitir (safety).
[ -z "$FILE_PATH" ] && exit 0

# Normalizar para absoluto.
case "$FILE_PATH" in
  /*) ABS="$FILE_PATH" ;;
  *)  ABS="$ROOT/$FILE_PATH" ;;
esac

# (d) Fora da raiz do projeto → permitir (SKILL.md, ~/.claude, libs do sistema, etc.).
case "$ABS" in
  "$ROOT"/*) : ;;
  *) exit 0 ;;
esac

# (d) Exceções dentro do projeto, sempre liberadas: docs/markdown (CLAUDE.md, CONTEXT.md,
#     README), .git, .claude, e a própria saída do scan.
case "$ABS" in
  *.md|*.MD|*.markdown) exit 0 ;;
  "$ROOT"/.git/*)       exit 0 ;;
  "$ROOT"/.claude/*)    exit 0 ;;
  "$SCAN_DIR"/*)        exit 0 ;;
esac

# Caso contrário: arquivo-fonte do projeto, agente principal, scan ainda não rodou → BLOQUEAR.
# Exit 2 bloqueia a tool; a mensagem precisa ir para STDERR para o modelo vê-la.
cat >&2 << 'EOF'
BLOQUEADO: Deep Scan obrigatório antes de ler arquivos do projeto diretamente.

A skill project-architect escaneia a codebase via WORKFLOW (ultracode) — não leia os
arquivos de fonte um a um no contexto principal.

O que fazer agora:
1. Garanta a saída e ative o gate com a raiz do projeto:
     mkdir -p /tmp/project-scan && pwd > /tmp/.require-deep-scan
2. Mapeie as áreas funcionais do projeto:
     find . -type d -not -path './.git/*' -not -path '*/node_modules/*' -maxdepth 3 | sort
3. Sinalize o início e rode o Workflow de Deep Scan (script bundled da skill):
     touch /tmp/project-scan/.scanning
     Workflow({ scriptPath: "[skill_dir]/scripts/deep-scan.workflow.js",
                args: { skill_dir, project_root, areas: [{ name, path }, ...] } })
   Cada scanner-agent roda em paralelo, retorna inventário estruturado E grava
   /tmp/project-scan/[area].md.
4. Quando /tmp/project-scan/ tiver os .md, esta trava libera sozinha.

Motivo: o Workflow escaneia em paralelo, com contexto isolado por área, produzindo um
inventário spec-driven completo sem estourar nem poluir o contexto principal. Ler as
fontes direto, sequencialmente, perde detalhes e gasta o contexto à toa.
EOF
exit 2
