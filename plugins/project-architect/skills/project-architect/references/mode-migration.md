# MIGRATION — Projeto Existente Sem Estrutura

Use quando o projeto tem código real mas sem devcontainer, sem CLAUDE.md, sem estrutura de workspaces.

## Passo 1 — Deep Scan

Execute o Deep Scan (seção da SKILL.md) para inventariar o projeto.

## Passo 2 — Mapa de modo mental

Para cada grupo de arquivos ou pasta, identifique o modo mental necessário para trabalhar neles. Grupos com mesmo modo mental vão para o mesmo workspace. Se arquivos existentes não se encaixam limpos em 2-3 workspaces, o sinal é simplificar — não criar mais workspaces.

## Passo 3 — Proponha workspaces

Apresente com justificativa para cada boundary. Confirme antes de gerar qualquer arquivo.

## Passo 4 — Gere a estrutura

Crie `CLAUDE.md` + `CONTEXT.md` por workspace. Não mova nem delete arquivos existentes.

## Passo 5 — Devcontainer

Se não existir, adicione seguindo `references/devcontainer-templates.md`. Se existir mas usar imagem diferente, pergunte ao usuário antes de modificar.

## Passo 6 — Infisical

Se não configurado, guie o usuário seguindo `references/infisical-setup.md`.

## Passo 7 — CLIs e Skills

Com base no que o projeto já faz, proponha e confirme antes de instalar.

## Passo 8 — Mapa de migração

Liste para o usuário: quais arquivos existentes pertencem a qual workspace e o que renomear para seguir as convenções.

Execute o checklist de verificação do BUILD (ver `references/mode-build.md` Passo 6).
