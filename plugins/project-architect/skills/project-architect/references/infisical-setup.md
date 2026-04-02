# Infisical Setup — Por Projeto

Cada projeto Douravita tem seu próprio projeto no Infisical. Siga este guia ao configurar um projeto novo.

**Infisical self-hosted:** `https://sec.douravita.com.br`

---

## Pré-requisito — Variáveis locais no host

Antes de abrir qualquer devcontainer, estas 3 variáveis precisam estar no `~/.zshrc` ou `~/.bashrc` da **máquina local** (não do container):

```bash
export ANTHROPIC_API_KEY=sk-ant-...
export INFISICAL_CLIENT_ID=...
export INFISICAL_CLIENT_SECRET=...
```

O devcontainer lê elas via `${localEnv:...}` e passa para dentro. Sem elas, o container abre mas nenhum secret carrega.

---

## Passo 1 — Criar o projeto no Infisical

1. Acesse `https://sec.douravita.com.br`
2. Crie um novo projeto com o nome do repositório
3. Copie o **Project ID** (aparece na URL ou nas configurações do projeto)
4. Configure os secrets no ambiente `dev` (e `prod` se aplicável)

---

## Passo 2 — Atualizar o devcontainer

Substitua `YOUR_PROJECT_ID` no `postStartCommand` do `devcontainer.json`:

```json
"postStartCommand": "infisical run --projectId=SEU_PROJECT_ID_AQUI --env=dev --domain=https://sec.douravita.com.br/api -- sh -c 'env | grep -v INFISICAL > /home/node/.infisical.env' && echo 'source /home/node/.infisical.env' >> /home/node/.zshrc && echo 'Secrets carregados'"
```

---

## Passo 3 — Garantir as credenciais locais

O devcontainer lê `INFISICAL_CLIENT_ID` e `INFISICAL_CLIENT_SECRET` do ambiente local via:

```json
"INFISICAL_CLIENT_ID": "${localEnv:INFISICAL_CLIENT_ID}",
"INFISICAL_CLIENT_SECRET": "${localEnv:INFISICAL_CLIENT_SECRET}"
```

Essas vars precisam estar no `~/.zshrc` ou `~/.bashrc` da máquina host. Se não estiverem, o container vai abrir mas os secrets não vão carregar.

---

## Como o carregamento funciona

Quando o container inicia, o `postStartCommand`:
1. Chama `infisical run` com as credenciais de machine identity
2. Captura todas as variáveis de ambiente — exceto as de autenticação do Infisical (`^INFISICAL_CLIENT*`) — em `/home/node/.infisical.env`
3. Adiciona `source /home/node/.infisical.env` ao `.zshrc` do container (idempotente — não duplica se o container reiniciar)
4. A partir daí, qualquer terminal novo no container tem os secrets disponíveis como variáveis de ambiente

---

## Convenção de Nomes de Secrets

Use `SCREAMING_SNAKE_CASE`. Prefixe por serviço quando relevante:

| Padrão | Exemplo |
|--------|---------|
| `NOME_DO_SERVICO_API_KEY` | `STRIPE_API_KEY` |
| `NOME_DO_SERVICO_SECRET` | `META_APP_SECRET` |
| `DATABASE_URL` | `DATABASE_URL` |
| `WEBHOOK_SECRET` | `WEBHOOK_SECRET` |

Evite nomes genéricos como `API_KEY` ou `SECRET` — colide entre projetos se alguém rodar dois containers.

---

## Verificar se está funcionando

Dentro do container, após abrir um terminal:

```bash
# Deve mostrar o valor do secret
echo $NOME_DO_SEU_SECRET

# Lista todos os secrets carregados
cat /home/node/.infisical.env
```

Se vazio: verifique se `INFISICAL_CLIENT_ID` e `INFISICAL_CLIENT_SECRET` estão no host, e se o `projectId` no devcontainer está correto.
