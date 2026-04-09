# Traffic Channels — Referencia Completa

## Meta (Facebook + Instagram)

### Restricoes
- **Redirect NAO permitido** — usar no-redirect obrigatoriamente
- **Custom tracking domain obrigatorio**
- Traffic filtering limitado ao nivel de Offer
- Conversoes podem levar ate 24h para aparecer

### Setup Completo

1. **Dominio custom** ja configurado (CNAME + SSL)
2. **Offer Source** com parametro External ID role
3. **Offer/Website** com parametros PII:
   - Email, Phone, First name, Last name, City, Country, State
   - Birthday, Gender, Zip, IP, User Agent
4. **Traffic Channel:** template Facebook
5. **Conectar conta Meta** (OAuth) — reconectar a cada 2-3 meses
6. **Campanha** com no-redirect tracking
7. **Ads no Meta** com parametros de tracking

### Parametros Obrigatorios (API)
```
sub1={{ad.id}}        → Aid role
sub2={{adset.id}}     → Gid role
sub3={{campaign.id}}  → Cid role
sub19=fbp             → Browser ID (HARDCODED, nao editar)
sub20=fbc             → Meta Click ID (HARDCODED, nao editar)
```

**fbclid DEVE ser o ultimo parametro** — nada depois dele.

### URL de Tracking Completa (exemplo)
```
https://lp.dominio.com/creatina?cmpid=CAMP_ID&sub1={{ad.id}}&sub2={{adset.id}}&sub3={{campaign.id}}&sub4={{ad.name}}&sub5={{adset.name}}&sub6={{campaign.name}}&sub7={{placement}}&utm_source=facebook&fbclid={{fbclid}}
```

### Redirect com fbc/fbp (caso especial)
Se precisar usar redirect com Meta:
1. Ativar "Redirect for Meta" toggle
2. Adicionar script na LP:
```html
<script src="https://track.dominio.com/clickupd_fbp_fbc.js" defer></script>
```

### Meta CAPI
1. Event Manager → Pixel → Settings → Generate Access Token
2. RedTrack: CAPI Integrations → Meta → Add
3. Mapear: RedTrack conversion type → Meta event name
4. Atribuir pixel ao traffic channel ou offer

### PII enviado ao Meta via CAPI
Email, phone, first name, last name, birthday, gender, zip, IP, user agent, city, country, state, event ID, event name, event time, revenue, content category, content IDs, product name, contents, order ID

---

## Google Ads

### Restricoes
- **No-redirect recomendado** (parallel tracking nao recomendado)
- **Custom tracking domain obrigatorio**
- Parametros em locais diferentes por tipo de campanha

### Onde colocar parametros por tipo de campanha
| Tipo | Local |
|------|-------|
| Regular | Settings → Account → Tracking → Tracking template |
| Merchant Center / PMax | Settings → Account → Tracking → Final URL suffix (remover `{lpurl}?`) |
| YouTube | Somente no nivel de Ad |

### Parametros Obrigatorios (API)
```
sub1={creative}      → Aid role
sub2={adgroupid}     → Gid role  
sub3={campaignid}    → Cid role
```

### Parametros Especiais
```
gclid                → Google Click ID (automatico)
{wbraid}             → iOS web-to-app (remover se in-app)
{gbraid}             → iOS app-to-app
```

### Setup
1. Dominio custom configurado
2. Encontrar Google Ads Customer ID (e MCC ID se aplicavel)
3. Traffic channel template: "Google Ads (No-redirect tracking)"
4. Conectar conta Google (OAuth)
5. Adicionar Customer ID e MCC ID
6. Campanha com no-redirect
7. Mapear conversoes (case-sensitive)

### Conversion Mapping
- **Conversion type:** evento custom do RedTrack
- **Conversion name:** nome exibido no Google Ads
- **Category:** categoria de evento Google
- **Include in conversions:** sim/nao para coluna Conversions do Google

### Cost Update por Tipo
| Tipo de Campanha | Campaign | Adset | Ad |
|-----------------|----------|-------|-----|
| Regular | Sim | Sim | Sim |
| PMax | Sim | Nao | Nao |

### Timing
- Conversoes aparecem no Google Ads em ~24h
- iOS sem clickid: ~48h
- Retries a cada 4h por 36h se falhar

---

## TikTok

### Setup
1. Dominio custom configurado
2. Criar tipos de conversao (case-sensitive, coincidir com TikTok)
3. Offer/Website com parametros PII (phone, email)
4. Traffic channel template: TikTok
5. Conectar conta TikTok (OAuth)
6. Adicionar TikTok Pixel ID e Access Token
7. Campanha com no-redirect

### Pixel Setup
1. TikTok Event Manager → Connect data source → Web → Events API
2. Copiar Pixel ID de Data Sources
3. Gerar Access Token em Pixel Settings

### TikTok CAPI
1. RedTrack: CAPI Integrations → TikTok → Add
2. Mapear conversion types → TikTok event names
3. Atribuir pixel ao traffic channel ou offer

### Dados enviados ao TikTok
PixelId, PixelKey, EventName, EventTime, ClickId, page, referrer, phone (hash), email (hash), IP, UserAgent, ContentType, Contents, Currency (USD), Revenue

### Testar ANTES de lancar
1. Gerar test click no TikTok (fornece tt_test_id)
2. Verificar tt_test_id no parametro ref_id do RedTrack
3. Gerar test conversion no RedTrack
4. Validar tudo antes de rodar trafego real

### Onde colocar URL + parametros
Ad → Ad details → URL

---

## Traffic Channel Custom (sem template)

Para fontes sem template pre-configurado no RedTrack:

1. New from scratch
2. Preencher:
   - **Nome** da fonte
   - **Dynamic parameters:** parametros que a fonte suporta (sub1, sub2, etc.)
   - **S2S Postback URL:** se a fonte aceitar postback
3. Macro do RedTrack para click ID do canal: `{ref_id}`
   - Na postback: `channel_macro={ref_id}`
   - No link da campanha: `ref_id={channel_macro}`

---

## Traffic Filtering

Filtrar trafego indesejado por:
- **Bot blacklist:** bloquear bots conhecidos
- **IP blacklist:** bloquear IPs especificos
- **Referrer filter:** filtrar por dominio de referencia
- **Device/OS/Browser:** filtrar por tipo de dispositivo

Configurar em: Traffic Channel → Filtering

## A/B Testing

Distribuir trafego entre multiplas variantes:
- Configurar weights no funil da campanha
- Cada lander/offer recebe uma porcentagem
- RedTrack distribui automaticamente

## Default Fallback URL

URL de fallback quando o tracking domain e acessado diretamente:
- Configurar no dominio
- Redireciona visitantes que nao vem de uma campanha
