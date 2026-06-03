# Secrets — Infisical via Agent Vault

A Douravita guarda secrets no **Infisical self-hosted** (`https://sec.douravita.com.br`) e os entrega aos agentes via **Agent Vault** — o proxy de credenciais da Infisical. O agente **nunca recebe o secret**: ele faz a chamada normal (ex: para `api.stripe.com`) e o Agent Vault, um proxy HTTPS transparente, anexa a credencial real na saída. Mesmo sob prompt injection, não há secret no contexto para vazar.

```
Agente ──HTTPS_PROXY──▶ Agent Vault ──injeta credencial──▶ API externa
                            │
                            └── credential store: Infisical (sec.douravita.com.br)
```

## Modelo de duas camadas

| Camada | Papel |
|--------|-------|
| **Infisical** (`sec.douravita.com.br`) | Onde os secrets ficam guardados — store por projeto/ambiente |
| **Agent Vault** | Proxy que brokera o acesso — o agente roteia tudo por ele e nunca toca no secret |

---

## Pré-requisito — credenciais locais no host

Estas variáveis precisam estar no `~/.zshrc`/`~/.bashrc` da **máquina local** (são a machine identity que o Agent Vault usa para autenticar no Infisical como credential store):

```bash
export ANTHROPIC_API_KEY=sk-ant-...
export INFISICAL_CLIENT_ID=...
export INFISICAL_CLIENT_SECRET=...
```

---

## Passo 1 — Projeto + machine identity no Infisical

1. Acesse `https://sec.douravita.com.br` e crie um projeto com o nome do repositório
2. Copie o **Project ID** (na URL ou nas configurações)
3. Configure os secrets no ambiente `dev` (e `prod` se aplicável)
4. A machine identity (Organization Settings → Access Control → Machine Identities) fornece o `INFISICAL_CLIENT_ID`/`SECRET` e precisa ter acesso ao projeto

---

## Passo 2 — Instalar o Agent Vault (se não tiver)

Detecte e instale só se faltar:

```bash
command -v agent-vault >/dev/null 2>&1 \
  && echo "OK: agent-vault já instalado ($(agent-vault --version 2>/dev/null))" \
  || curl --proto '=https' --proto-redir '=https' --tlsv1.2 -fsSL https://get.agent-vault.dev | sh
```

Suporta macOS (Intel + Apple Silicon) e Linux (x86_64 + ARM64). No Windows, instale dentro do **WSL**. Alternativa em container: imagem `infisical/agent-vault` (portas `14321` API / `14322` proxy).

---

## Passo 3 — Subir o servidor e criar o vault (backed by Infisical)

```bash
# servidor — uma vez por máquina/container
export AGENT_VAULT_MASTER_PASSWORD=<senha-forte>
agent-vault server -d                 # daemon: 14321 (API) / 14322 (proxy)
```

Crie um vault **apoiado no Infisical** (em vez do store local encriptado), apontando para o Infisical da Douravita:

```bash
export INFISICAL_URL=https://sec.douravita.com.br
agent-vault vault create <nome-do-projeto> --credential-store=infisical
```

O fluxo exato de mapear os secrets do projeto Infisical → serviços/hosts está em `https://docs.agent-vault.dev` (Installation / Tutorial).

---

## Passo 4 — Rodar o agente através do proxy

Em vez de chamar `claude` direto, rode por baixo do Agent Vault — ele bootstrapa `HTTPS_PROXY`/`HTTP_PROXY`, `AGENT_VAULT_TOKEN`, CA-trust e os env vars abaixo:

```bash
agent-vault run -- claude
```

No código, use **placeholders** em vez de secrets reais — o Agent Vault substitui na saída:

```bash
ANTHROPIC_API_KEY=__anthropic_api_key__   # dummy; trocado pela credencial real no proxy
```

Variáveis que o Agent Vault define no ambiente do agente:

| Var | O que é |
|-----|---------|
| `AGENT_VAULT_ADDR` | URL do servidor (ex: `http://127.0.0.1:14321`) |
| `AGENT_VAULT_TOKEN` | token do agente (mintado pelo `agent-vault run`) |
| `AGENT_VAULT_VAULT` | nome do vault em uso |

As skills `agent-vault-cli` e `agent-vault-http` ensinam o agente a operar o vault (discover, proposals, audit log).

---

## Carregamento de env no devcontainer (não-sensível / legado)

Para variáveis **não sensíveis** (ou setups que ainda não migraram para o Agent Vault), o devcontainer pode carregar env via `infisical run` no `postStartCommand`:

```json
"postStartCommand": "infisical run --projectId=SEU_PROJECT_ID --env=dev --domain=https://sec.douravita.com.br/api -- sh -c 'env | grep -v INFISICAL > /home/node/.infisical.env' && echo 'source /home/node/.infisical.env' >> /home/node/.zshrc && echo 'Secrets carregados'"
```

> **Regra:** credenciais sensíveis usadas por agentes (API keys de LLM, tokens de pagamento, PATs) devem ir pelo **Agent Vault**, não pro ambiente. O `infisical run` é para config não sensível e contextos sem agente. As credenciais locais (`INFISICAL_CLIENT_ID`/`SECRET`) chegam ao container via `${localEnv:...}` no `devcontainer.json` — sem elas, nem o `infisical run` nem o vault backed-by-Infisical carregam.

---

## Convenção de Nomes de Secrets

Use `SCREAMING_SNAKE_CASE`. Prefixe por serviço quando relevante:

| Padrão | Exemplo |
|--------|---------|
| `NOME_DO_SERVICO_API_KEY` | `STRIPE_API_KEY` |
| `NOME_DO_SERVICO_SECRET` | `META_APP_SECRET` |
| `DATABASE_URL` | `DATABASE_URL` |
| `WEBHOOK_SECRET` | `WEBHOOK_SECRET` |

Evite nomes genéricos como `API_KEY` ou `SECRET` — colidem entre projetos.

---

## Verificar se está funcionando

```bash
command -v agent-vault && agent-vault --version          # binário instalado
# dentro de um `agent-vault run -- ...`:
[ -n "$AGENT_VAULT_TOKEN" ] && echo "OK: token presente" || echo "FALTA: AGENT_VAULT_TOKEN"
agent-vault vault discover --json                        # hosts com credencial configurada
```

Se falhar: confirme o servidor (`agent-vault server`), o `AGENT_VAULT_MASTER_PASSWORD`, e que o vault está backed pelo Infisical (`INFISICAL_URL` + machine identity com acesso ao projeto).
