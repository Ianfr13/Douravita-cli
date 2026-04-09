---
name: redtrack
description: "Configuracao completa, manutencao e operacao do RedTrack para afiliados. Cobre setup de campanhas, offers, landers, traffic channels, conversion tracking, cost tracking, automacao e reports. Usa a CLI cli-anything-redtrack para todas as operacoes. Use esta skill sempre que o usuario mencionar RedTrack, tracking de conversoes, postback, campanhas de afiliado, ROAS, atribuicao de trafego, criar campanha, configurar tracking, custom domain, landing page tracking, pixel de conversao, auto-rules, ou qualquer operacao relacionada a rastreamento de performance de campanhas de marketing digital."
---

# RedTrack — Gestao Completa para Afiliados

Skill para configurar, operar e manter o RedTrack como tracker de afiliados.
Cobre todo o ciclo: setup inicial, campanhas, tracking, custos, automacao e reports.

## CLI: cli-anything-redtrack

Todas as operacoes usam a CLI. Sempre usar `--json` quando precisar parsear output.

### Comandos Principais

```
# Conta
cli-anything-redtrack account info

# Dominios
cli-anything-redtrack domain list
cli-anything-redtrack domain add --domain "track.exemplo.com"
cli-anything-redtrack domain ssl-renew <ID>
cli-anything-redtrack domain delete <ID> --confirm

# Offer Sources (redes de afiliados)
cli-anything-redtrack offer-source list
cli-anything-redtrack offer-source create --name "Rede X" --postback-url "URL" --click-id-param "clickid" --payout-param "sum"
cli-anything-redtrack offer-source get <ID>
cli-anything-redtrack offer-source update <ID> --name "Novo Nome"
cli-anything-redtrack offer-source delete <ID>

# Offers
cli-anything-redtrack offer list
cli-anything-redtrack offer create --name "Oferta Y" --offer-source-id <ID> --url "https://oferta.com?sub={clickid}" --payout 50.0
cli-anything-redtrack offer update <ID> --url "nova-url" --payout 60.0
cli-anything-redtrack offer status-update <ID1> <ID2> --status paused
cli-anything-redtrack offer delete <ID>

# Traffic Channels
cli-anything-redtrack traffic list
cli-anything-redtrack traffic create --name "Facebook" --template "facebook"
cli-anything-redtrack traffic create --name "Custom Source" 
cli-anything-redtrack traffic get <ID>
cli-anything-redtrack traffic update <ID> --name "Google Ads"
cli-anything-redtrack traffic delete <ID>

# Landing Pages
cli-anything-redtrack lander list
cli-anything-redtrack lander create --name "LP Creatina" --url "https://lp.exemplo.com" --tracking-type direct
cli-anything-redtrack lander update <ID> --url "nova-url" --status active
cli-anything-redtrack lander delete <ID>

# Campanhas
cli-anything-redtrack campaign list
cli-anything-redtrack campaign list --date-from 2026-01-01 --date-to 2026-04-09
cli-anything-redtrack campaign create --name "FB - Creatina BR" --traffic-channel-id <ID> --domain "track.exemplo.com" --cost-type cpc --cost-value 0.15
cli-anything-redtrack campaign get <ID>
cli-anything-redtrack campaign update <ID> --status paused
cli-anything-redtrack campaign status-update <ID1> <ID2> --status archived
cli-anything-redtrack campaign links <ID>
cli-anything-redtrack campaign delete <ID> --confirm

# Conversoes
cli-anything-redtrack conversion list --date-from 2026-04-01 --date-to 2026-04-09
cli-anything-redtrack conversion list --campaign-id <ID> --status approved
cli-anything-redtrack conversion upload --click-id "abc123" --status approved --payout 50.0 --type "purchase"
cli-anything-redtrack conversion export --date-from 2026-04-01 --date-to 2026-04-09
cli-anything-redtrack conversion types

# Reports
cli-anything-redtrack report general --date-from 2026-04-01 --date-to 2026-04-09 --group-by campaign
cli-anything-redtrack report general --group-by offer --date-from 2026-04-01 --date-to 2026-04-09
cli-anything-redtrack report campaigns --date-from 2026-04-01 --date-to 2026-04-09
cli-anything-redtrack report clicks --date-from 2026-04-01 --campaign-id <ID>
cli-anything-redtrack report stream --date-from 2026-04-01 --date-to 2026-04-09

# Custos
cli-anything-redtrack cost list --date-from 2026-04-01 --date-to 2026-04-09
cli-anything-redtrack cost list --campaign-id <ID>

# Regras de Automacao
cli-anything-redtrack rule list
cli-anything-redtrack rule create --name "Pausar ROAS < 1" --condition "roas < 1" --action "pause"
cli-anything-redtrack rule update <ID> --status active
cli-anything-redtrack rule delete <ID>

# Lookups (sem auth)
cli-anything-redtrack lookup list
cli-anything-redtrack lookup get countries
cli-anything-redtrack lookup get browsers
```

## Workflow: Setup Completo de Afiliado

O setup segue esta ordem. Cada passo depende do anterior.

### 1. Dominio Custom de Tracking

Antes de qualquer coisa, configurar o dominio CNAME:

1. No registrador DNS, criar CNAME: `track.seudominio.com` → `xxx.rdtk.io` (dominio padrao do RT)
2. No RedTrack: `cli-anything-redtrack domain add --domain "track.seudominio.com"`
3. Ativar SSL gratuito no painel (ou `domain ssl-renew <ID>`)

**Cloudflare:** usar DNS Only (nuvem cinza), NAO proxied.

### 2. Offer Source + Offer

Offer Source = a rede de afiliados. Offer = a oferta especifica.

```bash
# Criar offer source
cli-anything-redtrack offer-source create \
  --name "Hotmart" \
  --click-id-param "clickid" \
  --payout-param "sum"

# Copiar a postback URL gerada e colar na rede

# Criar offer com macro de clickid na URL
cli-anything-redtrack offer create \
  --name "Creatina Turbo" \
  --offer-source-id <OS_ID> \
  --url "https://hotmart.com/oferta?src={clickid}" \
  --payout 97.0
```

**Regra critica:** a URL da offer DEVE conter `{clickid}` (ou a macro da rede) para passar o click ID do RedTrack.

### 3. Traffic Channel

```bash
# De template (Meta, Google, TikTok)
cli-anything-redtrack traffic create --name "Facebook" --template "facebook"

# Custom (fonte sem template)
cli-anything-redtrack traffic create --name "Taboola"
```

Apos criar, conectar a API da fonte no painel do RedTrack (OAuth para Meta/Google/TikTok).

### 4. Landing Page (opcional)

```bash
cli-anything-redtrack lander create \
  --name "LP Creatina V2" \
  --url "https://lp.exemplo.com/creatina" \
  --tracking-type direct
```

Para detalhes sobre scripts de tracking, tipos de lander e click URLs, consultar `references/landing-pages.md`.

### 5. Campanha

```bash
cli-anything-redtrack campaign create \
  --name "FB - Creatina BR" \
  --traffic-channel-id <TC_ID> \
  --domain "track.exemplo.com" \
  --cost-type cpc \
  --cost-value 0.15
```

Apos criar, configurar no painel:
- **Funnel:** Offer only, Landing+Offer, ou Prelanding+Landing+Offer
- **S2S Postback:** preenchido automaticamente do traffic channel
- **Auto update costs:** ativar toggle

Para detalhes sobre tipos de funil, redirect types e configuracao avancada, consultar `references/campaigns.md`.

### 6. Tracking Script (se no-redirect)

Se usar tracking sem redirect (obrigatorio para Meta/Google/TikTok):
- Gerar script no painel: Tools → Scripts → New
- Tipo: default, /click support, ou /pre-click support
- Atribuicao: Last paid click (recomendado)
- Copiar script para o `<body>` da landing page

Para detalhes sobre scripts, atribuicao e implementacao, consultar `references/conversion-tracking.md`.

### 7. Postback na Rede

```bash
# Pegar a postback URL do offer source
cli-anything-redtrack --json offer-source get <OS_ID>
```

Copiar a postback URL e adicionar na rede de afiliados. Formato com eventos:
```
https://domain/postback?clickid=MACRO_REDE&sum=MACRO_PAYOUT&type=purchase
```

### 8. Iniciar Trafego

- **Redirect:** copiar link de tracking da campanha
- **No-redirect:** usar URL da LP + parametros de tracking

```bash
# Ver links de tracking
cli-anything-redtrack campaign links <CAMP_ID>
```

### 9. Monitorar

```bash
# Report geral
cli-anything-redtrack report general --date-from 2026-04-01 --date-to 2026-04-09 --group-by campaign

# Conversoes
cli-anything-redtrack conversion list --date-from 2026-04-01 --status approved

# Custos
cli-anything-redtrack cost list --date-from 2026-04-01 --date-to 2026-04-09
```

## Operacoes de Manutencao

### Pausar/Ativar Campanhas em Lote

```bash
cli-anything-redtrack campaign status-update <ID1> <ID2> <ID3> --status paused
cli-anything-redtrack campaign status-update <ID1> <ID2> --status active
```

### Exportar Dados

```bash
# Conversoes
cli-anything-redtrack conversion export --date-from 2026-04-01 --date-to 2026-04-30

# Offers
cli-anything-redtrack offer export --status active
```

### Renovar SSL de Dominio

```bash
cli-anything-redtrack domain ssl-renew <DOMAIN_ID>
```

### Upload Manual de Conversao

```bash
cli-anything-redtrack conversion upload \
  --click-id "rt_click_abc123" \
  --status approved \
  --payout 97.0 \
  --type "purchase"
```

## Macros e Parametros Importantes

| Macro RedTrack | Descricao |
|---------------|-----------|
| `{clickid}` | ID unico do clique |
| `{cmpid}` | ID da campanha |
| `{ref_id}` | Click ID do traffic channel |
| `{sum}` | Valor do payout |
| `{sub1}`-`{sub20}` | Parametros customizaveis |

### Parametros por Fonte de Trafego

| Fonte | Ad ID | Adset/Group ID | Campaign ID | Especiais |
|-------|-------|----------------|-------------|-----------|
| Meta | `{{ad.id}}` | `{{adset.id}}` | `{{campaign.id}}` | `fbclid` (sempre ultimo), `sub19`=fbp, `sub20`=fbc |
| Google | `{creative}` | `{adgroupid}` | `{campaignid}` | `gclid`, `{wbraid}`, `{gbraid}` |
| TikTok | `__CID__` | `__AID__` | `__CAMPAIGN_ID__` | `ttclid` |

## Modelos de Custo

| Tipo | Descricao | Auto-update |
|------|-----------|-------------|
| CPC | Custo por clique | Sim |
| CPM | Custo por mil impressoes | Sim |
| CPA | Custo por acao | Nao (manual) |
| RevShare | Porcentagem da receita | Nao |
| auto | Detecta automaticamente | Depende |
| daily_budget | Orcamento diario | Nao |

## Tipos de Redirect

| Tipo | Velocidade | Uso |
|------|-----------|-----|
| Regular 302 | Rapido (browser) | Padrao para fontes que aceitam redirect |
| Server 302 | Rapido (server) | Esconde referrer |
| Meta refresh | Medio (client) | Esconde referrer, client-side |
| Double meta refresh | Lento | Mascara fonte de trafego original |
| JS refresh | Lento | Nao recomendado para SEO |

## References

Para detalhes especificos de cada area, consultar os arquivos de referencia:

| Topico | Arquivo | Quando consultar |
|--------|---------|-----------------|
| Campanhas | `references/campaigns.md` | Tipos de funil, redirect types, configuracao avancada |
| Conversion Tracking | `references/conversion-tracking.md` | Postback, scripts, pixel, no-redirect, CAPI |
| Traffic Channels | `references/traffic-channels.md` | Meta, Google, TikTok — setup API e parametros |
| Landing Pages | `references/landing-pages.md` | Lander, prelander, listicle, scripts, click URLs |
| Cost Tracking | `references/cost-tracking.md` | Auto-update, modelos, troubleshoot |
| Automation Rules | `references/automation-rules.md` | Regras, condicoes, schedule, notificacoes |
