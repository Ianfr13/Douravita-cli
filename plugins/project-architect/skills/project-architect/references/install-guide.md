# Guia de Instalação — Máquina do Zero

Setup completo para usar o workflow Douravita. Cobre macOS e Windows.

---

## O que precisa estar instalado

| Ferramenta | Por quê |
|-----------|---------|
| **Git** | Versionamento de código |
| **VS Code** | IDE + Dev Containers |
| **Docker runtime** | Rodar devcontainers (Colima no Mac, Docker Desktop no Windows) |
| **GitHub CLI (gh)** | Criar repos, PRs, auth |
| **Node.js 22+** | Runtime + npx para ferramentas |
| **Claude Code** | Agente AI |
| **Claude Code auth** | OAuth login (via `claude` CLI) |
| **2 variáveis de ambiente** | INFISICAL_CLIENT_ID, INFISICAL_CLIENT_SECRET |

---

## macOS

### Detecção — rode estes comandos para ver o que já existe

```bash
# Git
git --version 2>/dev/null && echo "OK: Git instalado" || echo "FALTA: Git"

# Homebrew
brew --version 2>/dev/null && echo "OK: Homebrew instalado" || echo "FALTA: Homebrew"

# VS Code
code --version 2>/dev/null && echo "OK: VS Code instalado" || echo "FALTA: VS Code"

# Docker/Colima
docker --version 2>/dev/null && echo "OK: Docker CLI instalado" || echo "FALTA: Docker CLI"
colima status 2>/dev/null && echo "OK: Colima rodando" || echo "INFO: Colima não rodando ou não instalado"

# GitHub CLI
gh --version 2>/dev/null && echo "OK: gh instalado" || echo "FALTA: gh"

# Node.js
node --version 2>/dev/null && echo "OK: Node $(node --version)" || echo "FALTA: Node.js"

# Claude Code
claude --version 2>/dev/null && echo "OK: Claude Code instalado" || echo "FALTA: Claude Code"

# Variáveis
[ -n "$ANTHROPIC_API_KEY" ] && echo "OK: ANTHROPIC_API_KEY definida" || echo "FALTA: ANTHROPIC_API_KEY"
[ -n "$INFISICAL_CLIENT_ID" ] && echo "OK: INFISICAL_CLIENT_ID definida" || echo "FALTA: INFISICAL_CLIENT_ID"
[ -n "$INFISICAL_CLIENT_SECRET" ] && echo "OK: INFISICAL_CLIENT_SECRET definida" || echo "FALTA: INFISICAL_CLIENT_SECRET"
```

### Instalação passo a passo

#### 1. Homebrew (se não tiver)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Após instalar, siga as instruções que aparecem no terminal para adicionar ao PATH.

#### 2. Git (se não tiver)

```bash
# Geralmente já vem com macOS via Xcode Command Line Tools
xcode-select --install
# Ou via Homebrew:
brew install git
```

Configurar identidade:
```bash
git config --global user.name "Nome Sobrenome"
git config --global user.email "email@douravita.com.br"
```

#### 3. VS Code

```bash
brew install --cask visual-studio-code
```

Instalar extensões essenciais:
```bash
code --install-extension ms-vscode-remote.remote-containers
code --install-extension anthropic.claude-code
code --install-extension eamodio.gitlens
```

#### 4. Docker via Colima (recomendado para Mac)

Colima é mais leve que Docker Desktop e não requer licença comercial.

```bash
brew install colima docker docker-compose docker-credential-helper
```

Iniciar Colima:
```bash
colima start --cpu 4 --memory 8 --disk 60
```

Verificar:
```bash
docker ps
# Deve mostrar lista vazia sem erros
```

Para iniciar automaticamente no boot:
```bash
brew services start colima
```

#### 5. GitHub CLI

```bash
brew install gh
gh auth login --web
# Seguir o fluxo no browser
```

#### 6. Node.js 22

```bash
brew install node@22
```

Ou via nvm (recomendado se vai trabalhar com múltiplas versões):
```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
# Reabrir terminal
nvm install 22
nvm use 22
```

#### 7. Claude Code

```bash
npm install -g @anthropic-ai/claude-code
```

Fazer login via OAuth (abre browser):
```bash
claude
# Na primeira execução, abre o browser para autenticar
# Faça login com sua conta Anthropic
```

**Persistência no devcontainer:** O login fica salvo em `~/.claude/` no host. Como o devcontainer monta `~/.claude` via bind mount (`source=${localEnv:HOME}/.claude,target=/home/node/.claude`), o login feito no host persiste automaticamente dentro de qualquer container. Faça login uma vez no host e nunca mais precisa refazer.

#### 8. Infisical CLI

```bash
brew install infisical/get-cli/infisical
```

Verificar: `infisical --version`

#### 9. Configurar Infisical (a skill faz tudo, só pede acesso no browser)

O Infisical (sec.douravita.com.br) é onde ficam os secrets de todos os projetos. Cada pessoa da equipe precisa de conta + Machine Identity para seus devcontainers.

**A skill executa os comandos e guia o usuário nos passos que precisam de browser.**

**Passo 9.1 — Criar conta:**
Pergunte: "Já tem conta no Infisical (sec.douravita.com.br)?"

Se não:
> "Abra https://sec.douravita.com.br e clique em 'Continue with Google'. Use seu email @douravita.com.br (é obrigatório o domínio Douravita). Me avise quando terminar."

Se sim: prossiga.

**Passo 9.2 — Criar organização:**
Pergunte: "Já tem uma organização no Infisical?"

Se não:
> "No Infisical, após login, clique em 'Create Organization'. Dê o nome que quiser (ex: seu nome ou 'Douravita - [Seu Nome]'). Me avise o nome."

Se sim: prossiga.

**Passo 9.3 — Criar Machine Identity (Universal Auth):**

Instrua o usuário passo a passo:

> 1. No Infisical, vá em **Organization Settings → Access Control → Machine Identities**
> 2. Clique **Create Identity**
> 3. **Name:** `devcontainer-local`
> 4. **Role:** Admin (ou Member se preferir acesso restrito)
> 5. Clique **Create**
> 6. Na identity criada, vá na aba **Authentication → Universal Auth**
> 7. Clique **Create Client Secret**
> 8. Deixe os defaults (sem TTL, sem limite de uso)
> 9. **IMPORTANTE:** Copie o **Client ID** e o **Client Secret** agora — o secret só aparece uma vez.
> 10. Cole os dois valores aqui pra mim.

Aguarde o usuário colar os valores.

**Passo 9.4 — Salvar as 2 variáveis no shell do host:**

```bash
read -sp "Cole seu INFISICAL_CLIENT_ID: " INFISICAL_CLIENT_ID && echo
read -sp "Cole seu INFISICAL_CLIENT_SECRET: " INFISICAL_CLIENT_SECRET && echo

SHELL_RC="$HOME/.zshrc"
[ -f "$HOME/.bashrc" ] && [ ! -f "$HOME/.zshrc" ] && SHELL_RC="$HOME/.bashrc"

grep -q "INFISICAL_CLIENT_ID" "$SHELL_RC" 2>/dev/null || echo "export INFISICAL_CLIENT_ID=$INFISICAL_CLIENT_ID" >> "$SHELL_RC"
grep -q "INFISICAL_CLIENT_SECRET" "$SHELL_RC" 2>/dev/null || echo "export INFISICAL_CLIENT_SECRET=$INFISICAL_CLIENT_SECRET" >> "$SHELL_RC"

source "$SHELL_RC"
echo "Variáveis salvas em $SHELL_RC"
```

**Nota:** O Claude Code usa OAuth (login via browser no primeiro uso), não precisa de API key no shell.

**Passo 9.5 — Verificar:**
```bash
echo "INFISICAL_CLIENT_ID: $(echo $INFISICAL_CLIENT_ID | head -c 10)..."
echo "INFISICAL_CLIENT_SECRET: $(echo $INFISICAL_CLIENT_SECRET | head -c 10)..."
infisical --version
```

**Passo 9.7 — Adicionar Machine Identity ao primeiro projeto (quando criar):**

Quando o usuário criar seu primeiro projeto no Infisical, a identity precisa ter acesso:
> Em **Project Settings → Access Control → Machine Identities → Add Identity**
> Selecione `devcontainer-local` e dê role **Admin** (ou **Developer** para acesso read-only).

Isso é feito depois, no modo BUILD, quando o projeto é criado. Aqui no INSTALL, só criamos a identity.

---

## Windows

### Detecção — rode no PowerShell

```powershell
# Git
git --version 2>$null; if ($?) { "OK: Git" } else { "FALTA: Git" }

# VS Code
code --version 2>$null; if ($?) { "OK: VS Code" } else { "FALTA: VS Code" }

# Docker Desktop
docker --version 2>$null; if ($?) { "OK: Docker" } else { "FALTA: Docker" }

# WSL
wsl --status 2>$null; if ($?) { "OK: WSL" } else { "FALTA: WSL" }

# GitHub CLI
gh --version 2>$null; if ($?) { "OK: gh" } else { "FALTA: gh" }

# Node
node --version 2>$null; if ($?) { "OK: Node" } else { "FALTA: Node" }
```

### Instalação passo a passo

#### 1. WSL2 (obrigatório para devcontainers no Windows)

Abrir PowerShell como Administrador:
```powershell
wsl --install
# Reiniciar o computador quando pedido
```

Após reiniciar, abrir o terminal Ubuntu que aparece e criar usuário/senha.

#### 2. Docker Desktop

Baixar e instalar: https://www.docker.com/products/docker-desktop/

Após instalar:
1. Abrir Docker Desktop
2. Settings → General → marcar "Use the WSL 2 based engine"
3. Settings → Resources → WSL Integration → habilitar para a distro Ubuntu
4. Apply & Restart

Verificar no terminal Ubuntu (WSL):
```bash
docker ps
```

#### 3. VS Code

Baixar e instalar: https://code.visualstudio.com/

Instalar extensões (no terminal Windows ou WSL):
```bash
code --install-extension ms-vscode-remote.remote-containers
code --install-extension ms-vscode-remote.remote-wsl
code --install-extension anthropic.claude-code
code --install-extension eamodio.gitlens
```

#### 4. Git (geralmente já vem com WSL Ubuntu)

No terminal WSL:
```bash
sudo apt update && sudo apt install -y git
git config --global user.name "Nome Sobrenome"
git config --global user.email "email@douravita.com.br"
```

#### 5. GitHub CLI

No terminal WSL:
```bash
(type -p wget >/dev/null || (sudo apt update && sudo apt-get install wget -y)) \
  && sudo mkdir -p -m 755 /etc/apt/keyrings \
  && out=$(mktemp) && wget -nv -O$out https://cli.github.com/packages/githubcli-archive-keyring.gpg \
  && cat $out | sudo tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null \
  && sudo chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg \
  && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
  && sudo apt update \
  && sudo apt install gh -y

gh auth login --web
```

#### 6. Node.js 22

No terminal WSL:
```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
# Reabrir terminal
nvm install 22
nvm use 22
```

#### 7. Claude Code

No terminal WSL:
```bash
npm install -g @anthropic-ai/claude-code
```

#### 8. Infisical CLI

No terminal WSL:
```bash
curl -1sLf 'https://artifacts-cli.infisical.com/setup.deb.sh' | sudo -E bash
sudo apt-get update && sudo apt-get install -y infisical
```

#### 9. Configurar Infisical + variáveis de ambiente

Mesmo fluxo do macOS (passos 9.1 a 9.7 acima). No WSL, o `SHELL_RC` vai apontar para `~/.bashrc` automaticamente pelo script do passo 9.5.
```

---

## Checklist de Verificação Final

Rode tudo de uma vez (no terminal macOS ou WSL Ubuntu):

```bash
echo "=== Verificação Completa ==="

echo -n "Git: " && git --version 2>/dev/null && echo "OK" || echo "FALHOU"
echo -n "Docker: " && docker ps >/dev/null 2>&1 && echo "OK" || echo "FALHOU — Docker não está rodando"
echo -n "VS Code: " && code --version >/dev/null 2>&1 && echo "OK" || echo "FALHOU"
echo -n "gh: " && gh auth status >/dev/null 2>&1 && echo "OK (logado)" || echo "FALHOU — rode 'gh auth login'"
echo -n "Node: " && node --version 2>/dev/null || echo "FALHOU"
echo -n "Claude Code: " && claude --version 2>/dev/null || echo "FALHOU"

echo ""
echo "=== Variáveis Infisical ==="
[ -n "$INFISICAL_CLIENT_ID" ] && echo "INFISICAL_CLIENT_ID: OK" || echo "INFISICAL_CLIENT_ID: FALTA"
[ -n "$INFISICAL_CLIENT_SECRET" ] && echo "INFISICAL_CLIENT_SECRET: OK" || echo "INFISICAL_CLIENT_SECRET: FALTA"

echo ""
echo "=== Extensões VS Code ==="
code --list-extensions 2>/dev/null | grep -q "ms-vscode-remote.remote-containers" && echo "Dev Containers: OK" || echo "Dev Containers: FALTA"
code --list-extensions 2>/dev/null | grep -q "anthropic.claude-code" && echo "Claude Code ext: OK" || echo "Claude Code ext: FALTA"

echo ""
echo "=== Teste Docker ==="
docker run --rm hello-world >/dev/null 2>&1 && echo "Docker run: OK" || echo "Docker run: FALHOU"
```

Se tudo OK, a máquina está pronta. Próximo passo: rodar **BUILD** para criar o primeiro projeto.

---

## Troubleshooting

### macOS: "colima start" trava ou dá erro
```bash
colima delete
colima start --cpu 4 --memory 8 --disk 60 --vm-type vz --vz-rosetta
```

### Claude Code: OAuth não funciona no terminal
```bash
# Se o browser não abre automaticamente:
claude --no-browser
# Copie a URL que aparece e abra manualmente
```

### macOS: Docker socket não encontrado
```bash
# Verificar se o socket existe
ls -la ~/.colima/default/docker.sock
# Criar symlink se necessário
sudo ln -sf ~/.colima/default/docker.sock /var/run/docker.sock
```

### Windows: Docker Desktop não inicia
1. Verificar que virtualização está habilitada na BIOS
2. PowerShell Admin: `bcdedit /set hypervisorlaunchtype auto`
3. Reiniciar

### Windows: VS Code não conecta ao WSL
```bash
# No WSL, garantir que code está no PATH
which code || echo "Instale VS Code pelo Windows primeiro, depois reabra o terminal WSL"
```

### Qualquer OS: Claude Code não funciona
```bash
# Verificar se está instalado
claude --version

# Se não está logado:
claude
# Siga o fluxo OAuth no browser

# Testar
claude "olá, teste rápido"
```
