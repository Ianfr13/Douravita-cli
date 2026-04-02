# Templates de Devcontainer

Dois templates: simples (sem CLIs extras) e estendido (com CLIs adicionais via Dockerfile).

---

## Template Simples — Só a Imagem Base

Use quando o projeto não precisa de CLIs extras além do que já vem na imagem base.

### `.devcontainer/devcontainer.json`

```json
{
  "name": "[Nome do Projeto]",
  "image": "ghcr.io/ianfr13/douravita-base:latest",
  "customizations": {
    "vscode": {
      "extensions": [
        "anthropic.claude-code",
        "eamodio.gitlens"
      ],
      "settings": {
        "terminal.integrated.defaultProfile.linux": "zsh",
        "terminal.integrated.profiles.linux": {
          "zsh": { "path": "zsh" }
        }
      }
    }
  },
  "remoteUser": "node",
  "mounts": [
    "source=[nome-do-projeto]-history-${devcontainerId},target=/commandhistory,type=volume",
    "source=${localEnv:HOME}/.claude,target=/home/node/.claude,type=bind,consistency=cached"
  ],
  "containerEnv": {
    "NODE_OPTIONS": "--max-old-space-size=4096",
    "CLAUDE_CONFIG_DIR": "/home/node/.claude",
    "ANTHROPIC_API_KEY": "${localEnv:ANTHROPIC_API_KEY}",
    "INFISICAL_CLIENT_ID": "${localEnv:INFISICAL_CLIENT_ID}",
    "INFISICAL_CLIENT_SECRET": "${localEnv:INFISICAL_CLIENT_SECRET}"
  },
  "workspaceMount": "source=${localWorkspaceFolder},target=/workspace,type=bind,consistency=delegated",
  "workspaceFolder": "/workspace",
  "postStartCommand": "infisical run --projectId=YOUR_PROJECT_ID --env=dev --domain=https://sec.douravita.com.br/api -- sh -c 'env | grep -v \"^INFISICAL_CLIENT\" > /home/node/.infisical.env' && grep -qF 'source /home/node/.infisical.env' /home/node/.zshrc || echo 'source /home/node/.infisical.env' >> /home/node/.zshrc && echo 'Secrets carregados'"
}
```

**Substitua:**
- `[Nome do Projeto]` → nome legível do projeto
- `[nome-do-projeto]` → slug (sem espaços) para o volume de histórico
- `YOUR_PROJECT_ID` → ID do projeto no Infisical (ver `infisical-setup.md`)

**Pré-requisitos no host:** as três vars abaixo precisam estar no `~/.zshrc` ou `~/.bashrc` da máquina local (não do container) antes de abrir o devcontainer:
```bash
export ANTHROPIC_API_KEY=sk-ant-...
export INFISICAL_CLIENT_ID=...
export INFISICAL_CLIENT_SECRET=...
```
O devcontainer lê elas via `${localEnv:...}` e passa para dentro. Sem elas, o container abre mas nenhum secret carrega.

---

## Template Estendido — Com CLIs Adicionais

Use quando o projeto precisa de CLIs do Douravita-cli ou de terceiros.

### `.devcontainer/devcontainer.json`

```json
{
  "name": "[Nome do Projeto]",
  "build": {
    "dockerfile": "Dockerfile"
  },
  "customizations": {
    "vscode": {
      "extensions": [
        "anthropic.claude-code",
        "eamodio.gitlens"
      ],
      "settings": {
        "terminal.integrated.defaultProfile.linux": "zsh",
        "terminal.integrated.profiles.linux": {
          "zsh": { "path": "zsh" }
        }
      }
    }
  },
  "remoteUser": "node",
  "mounts": [
    "source=[nome-do-projeto]-history-${devcontainerId},target=/commandhistory,type=volume",
    "source=${localEnv:HOME}/.claude,target=/home/node/.claude,type=bind,consistency=cached"
  ],
  "containerEnv": {
    "NODE_OPTIONS": "--max-old-space-size=4096",
    "CLAUDE_CONFIG_DIR": "/home/node/.claude",
    "ANTHROPIC_API_KEY": "${localEnv:ANTHROPIC_API_KEY}",
    "INFISICAL_CLIENT_ID": "${localEnv:INFISICAL_CLIENT_ID}",
    "INFISICAL_CLIENT_SECRET": "${localEnv:INFISICAL_CLIENT_SECRET}"
  },
  "workspaceMount": "source=${localWorkspaceFolder},target=/workspace,type=bind,consistency=delegated",
  "workspaceFolder": "/workspace",
  "postStartCommand": "infisical run --projectId=YOUR_PROJECT_ID --env=dev --domain=https://sec.douravita.com.br/api -- sh -c 'env | grep -v \"^INFISICAL_CLIENT\" > /home/node/.infisical.env' && grep -qF 'source /home/node/.infisical.env' /home/node/.zshrc || echo 'source /home/node/.infisical.env' >> /home/node/.zshrc && echo 'Secrets carregados'"
}
```

### `.devcontainer/Dockerfile`

```dockerfile
FROM ghcr.io/ianfr13/douravita-base:latest

# ─── CLIs Douravita (adicione os necessários) ────────────────────────────────
# RUN pip3 install --break-system-packages \
#     "git+https://github.com/Ianfr13/Douravita-cli.git#subdirectory=meta-ads" \
#     "git+https://github.com/Ianfr13/Douravita-cli.git#subdirectory=google-tag-manager" \
#     "git+https://github.com/Ianfr13/Douravita-cli.git#subdirectory=redtrack" \
#     "git+https://github.com/Ianfr13/Douravita-cli.git#subdirectory=railway"

# ─── CLIs de terceiros (adicione os necessários) ─────────────────────────────
# RUN npm install -g supabase
# RUN npm install -g wrangler
# RUN npm install -g playwright && playwright install --with-deps chromium
```

**Como usar:** descomente apenas os CLIs que o projeto precisa. Consulte `cli-catalog.md` para saber qual usar.

---

## Variáveis de Ambiente Extras

Se o projeto precisar de envs além das padrão, adicione no `containerEnv`:

```json
"containerEnv": {
  "NODE_OPTIONS": "--max-old-space-size=4096",
  "CLAUDE_CONFIG_DIR": "/home/node/.claude",
  "ANTHROPIC_API_KEY": "${localEnv:ANTHROPIC_API_KEY}",
  "INFISICAL_CLIENT_ID": "${localEnv:INFISICAL_CLIENT_ID}",
  "INFISICAL_CLIENT_SECRET": "${localEnv:INFISICAL_CLIENT_SECRET}",
  "MINHA_VAR": "${localEnv:MINHA_VAR}"
}
```

As variáveis do projeto (chaves de API, tokens) devem vir do Infisical, não hardcoded aqui.

---

## Extensões VS Code por Tipo de Projeto

| Tipo | Extensões adicionais sugeridas |
|------|-------------------------------|
| Qualquer projeto | `anthropic.claude-code`, `eamodio.gitlens` (já no template) |
| Node/TypeScript | `dbaeumer.vscode-eslint`, `esbenp.prettier-vscode` |
| Python | `ms-python.python`, `ms-python.black-formatter` |
| HTML/CSS/Landing page | `ritwickdey.liveserver`, `bradlc.vscode-tailwindcss` |
| Banco de dados | `mtxr.sqltools` |

Adicione na lista `extensions` do `devcontainer.json`.
