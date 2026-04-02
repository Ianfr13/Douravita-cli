#!/bin/bash
# Hook: enforce-deep-scan
# Bloqueia leitura direta de arquivos do projeto se Deep Scan não foi executado.
# O modelo DEVE spawnar subagentes (Agent tool) para ler a codebase.
#
# Ativação: a skill cria /tmp/.require-deep-scan no início de AUDIT/UPDATE/FORK/MIGRATION
# Desativação: quando /tmp/project-scan/ tem arquivos .md, a leitura é liberada
#
# Exit codes:
#   0 = permitir
#   2 = bloquear (stdout vira mensagem de erro pro modelo)

# Se o flag não existe, não estamos em modo de scan — permitir tudo
[ ! -f /tmp/.require-deep-scan ] && exit 0

# Se já tem scans, liberar
SCAN_COUNT=$(find /tmp/project-scan -name "*.md" 2>/dev/null | wc -l)
if [ "$SCAN_COUNT" -gt 0 ]; then
  exit 0
fi

# Ler o input do tool use (JSON via stdin)
INPUT=$(cat)

# Extrair o file_path do JSON
FILE_PATH=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('file_path',''))" 2>/dev/null)

# Se não conseguiu parsear, permitir (safety)
[ -z "$FILE_PATH" ] && exit 0

# Paths que SÃO projeto (bloquear leitura direta)
PROJECT_PATHS="/workspace/workers/ /workspace/dashboard/src/ /workspace/cli/ /workspace/workers/"

for PREFIX in $PROJECT_PATHS; do
  if [[ "$FILE_PATH" == ${PREFIX}* ]]; then
    cat << 'EOF'
BLOQUEADO: Deep Scan obrigatório antes de ler arquivos do projeto.

Você está tentando ler arquivos do projeto diretamente. A skill project-architect exige que você use SUBAGENTES para escanear a codebase.

O que fazer agora:
1. Rode: mkdir -p /tmp/project-scan
2. Spawne subagentes com a tool Agent — um por área funcional do projeto
3. Cada subagente deve ler os arquivos e salvar relatório em /tmp/project-scan/[nome].md
4. Após os scans, rode: ls /tmp/project-scan/
5. Só então prossiga com o diagnóstico/proposta

Prompt para cada subagente:
> Leia as instruções do scanner em /home/node/.claude/skills/project-architect/agents/scanner.md
> Escaneie o diretório [path] do projeto em /workspace
> Salve o relatório em /tmp/project-scan/[nome].md

Motivo: cada subagente tem contexto limpo e dedicado, produzindo um inventário spec-driven completo. Leitura sequencial perde detalhes.
EOF
    exit 2
  fi
done

# Não é arquivo do projeto — permitir (pode ler SKILL.md, CLAUDE.md, etc.)
exit 0
