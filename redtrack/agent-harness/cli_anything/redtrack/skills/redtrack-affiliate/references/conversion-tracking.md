# Conversion Tracking — Referencia Completa

## Metodos de Tracking

| Metodo | Precisao | Cookie-dependente | Melhor para |
|--------|----------|-------------------|-------------|
| S2S Postback | Alta | Nao | Redes de afiliados |
| API | Mais alta | Nao | ClickBank, Shopify, WooCommerce |
| Pixel/Script | Media | Sim (3rd party) | Thank you page propria |
| CAPI | Alta | Nao | Meta, Google, TikTok |

## S2S Postback (Server-to-Server)

O metodo mais comum para afiliados. A rede de afiliados envia uma requisicao HTTP ao RedTrack quando uma conversao acontece.

### Setup
1. Criar Offer Source no RedTrack (template ou custom)
2. Copiar a Postback URL gerada
3. Colar na configuracao de postback da rede de afiliados
4. Substituir macros pelos valores da rede

### Formato da Postback URL
```
https://dominio.rdtk.io/postback?clickid=MACRO_REDE&sum=MACRO_PAYOUT
```

### Com eventos multiplos
```
https://dominio.rdtk.io/postback?clickid=MACRO_REDE&sum=MACRO_PAYOUT&type=purchase
https://dominio.rdtk.io/postback?clickid=MACRO_REDE&sum=0&type=lead
https://dominio.rdtk.io/postback?clickid=MACRO_REDE&sum=MACRO_PAYOUT&type=upsell
```

### Custom Offer Source (sem template)
Quando a rede nao tem template no RedTrack:
1. New from scratch
2. Identificar as macros da rede para:
   - **clickid:** parametro que a rede usa para receber o click ID
   - **sum/payout:** parametro para o valor da conversao
3. Adicionar no Offer Source
4. Copiar postback URL gerada

## No-Redirect Tracking

Obrigatorio para Meta, Google, TikTok (redirect nao permitido).

### Duas opcoes:

#### 1. No-Redirect Script (simples)
- Uma campanha por landing page
- Mais simples de implementar
- Gerar em: Campaign → Tracking links → No-redirect

#### 2. Universal Script (avancado)
- Multiplas campanhas/fontes na mesma landing page
- Atribuicao cross-channel (organic + paid)
- Gerar em: Tools → Scripts → New

### Implementacao No-Redirect
1. Criar campanha no RedTrack
2. Copiar script de: Tracking links and parameters → No-redirect
3. Adicionar script no `<body>` da LP (final do body, NAO no head)
4. Usar LP Click URL no botao CTA: `dominio.com/click`
5. Adicionar parametros de tracking na URL da LP no traffic channel

### Implementacao Universal Script
1. Criar campanha para trafego organico (default)
2. Tools → Scripts → New
3. Configurar:
   - **Script type:** default | /click support | /pre-click support
   - **Domain:** dominio custom de tracking
   - **Default campaign:** campanha organica
   - **Attribution:** Last paid click (RECOMENDADO)
   - **Attribution window:** 7, 14 ou 30 dias
   - **Cookie domain:** dominio raiz (ex: `exemplo.com`, sem https://)
4. Copiar script gerado para o `<body>` da LP

### Diferencas entre scripts
| Feature | No-redirect | Universal |
|---------|-------------|-----------|
| Campanhas por pagina | 1 | Multiplas |
| Trafego organico | Nao | Sim |
| Atribuicao cross-channel | Nao | Sim |
| Setup | Mais simples | Mais complexo |

**NUNCA colocar ambos os scripts na mesma pagina** — causa conflito.

## Pixel/Script (First-Party)

Para tracking de conversao em thank you page propria.

### Metodo Cookie (First-Party)
1. Landing page deve ter Universal Script instalado
2. O script grava cookie `rtkclickid-store` com o click ID
3. Na thank you page, ler o cookie e disparar postback:

```javascript
// Le o cookie rtkclickid-store
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
}

const clickId = getCookie('rtkclickid-store');
if (clickId) {
  fetch(`https://track.dominio.com/postback?clickid=${clickId}&sum=97&type=purchase`);
}
```

## CAPI (Conversion API)

Integracao server-side com Meta, Google e TikTok. Mais precisa que pixels.

### Meta CAPI
1. Pegar Pixel ID e Access Token no Meta Event Manager
2. No RedTrack: CAPI Integrations → Meta → Add
3. Mapear tipos de conversao do RedTrack para eventos Meta
4. Atribuir pixel ao traffic channel ou offer

### Google CAPI
1. Conectar conta Google Ads no traffic channel
2. Mapear conversoes (nomes case-sensitive)
3. Configurar: conversion type, conversion name, category
4. Include in "conversions": sim/nao

### TikTok CAPI
1. Criar pixel no TikTok Event Manager (Events API)
2. Copiar Pixel ID e gerar Access Token
3. No RedTrack: CAPI Integrations → TikTok → Add
4. Mapear eventos (case-sensitive)
5. **Testar antes de lancar:** gerar test click com tt_test_id

## Tipos de Conversao

```bash
# Ver tipos disponiveis
cli-anything-redtrack conversion types
```

Tipos comuns: `purchase`, `lead`, `upsell`, `downsell`, `add_to_cart`, `initiate_checkout`

### Criar tipo custom
No painel: Tools → Conversion Tracking → Conversion Types
- Nome deve coincidir EXATAMENTE com o que a rede envia
- Case-sensitive

### Duplicate Postback Mode
Configura como lidar com postbacks duplicados por tipo de evento:
- **Ignore:** ignora duplicatas
- **Override:** substitui a conversao anterior
- **Add:** soma ao valor anterior

## Upload Manual de Conversao

```bash
cli-anything-redtrack conversion upload \
  --click-id "rt_abc123" \
  --status approved \
  --payout 97.0 \
  --type "purchase"
```

Status possiveis: `approved`, `pending`, `declined`, `fired`

## Postback Protection

Proteger contra postbacks falsos/fraudulentos:
- **IP Whitelist:** so aceitar postbacks de IPs da rede
- No painel: Offer Source → Postback Protection → Add IPs

## Click Expiration

Filtrar conversoes de cliques muito antigos:
- Configurar no Offer Source
- Exemplo: ignorar conversoes de cliques > 30 dias

## Troubleshooting Conversoes

1. **Conversao nao aparece:**
   - Verificar se postback URL esta correta na rede
   - Verificar se clickid esta sendo passado
   - Checar logs: Report → Logs
   - Testar postback manualmente no browser

2. **Conversao duplicada:**
   - Verificar duplicate postback mode
   - Verificar se a rede nao esta enviando multiplos postbacks

3. **Valor errado:**
   - Verificar macro de payout na postback URL
   - Verificar se a rede envia o valor no formato correto (ponto, nao virgula)

4. **Discrepancia RedTrack vs Rede:**
   - Verificar click expiration
   - Verificar timezone (RedTrack usa UTC)
   - Verificar se ha conversoes com status pending/declined
