# Landing Pages — Referencia Completa

## Tipos de Landing Page

### 1. Landing Page (padrao)
- Uma pagina, um CTA, uma oferta
- Tipo mais comum para afiliados
- Click URL: `dominio.com/click`

### 2. Listicle Landing
- Uma pagina com multiplas ofertas (tipo "Top 5 Creatinas")
- Cada oferta tem seu botao e click URL numerado
- Click URLs: `/click/1`, `/click/2`, `/click/3`
- **Ordem dos click URLs DEVE coincidir com ordem das offers no funil**

### 3. Prelanding Page
- Pagina de aquecimento antes da LP principal (VSL, quiz, artigo)
- Click URL para a LP: `dominio.com/preclick`
- Requer script especifico de prelanding

## Criacao via CLI

```bash
# Landing page padrao
cli-anything-redtrack lander create \
  --name "LP Creatina V2" \
  --url "https://lp.dominio.com/creatina" \
  --tracking-type direct

# Com redirect tracking
cli-anything-redtrack lander create \
  --name "LP Magnesio" \
  --url "https://lp.dominio.com/magnesio" \
  --tracking-type redirect
```

### Tracking Types
- `direct` — no-redirect (Meta, Google, TikTok)
- `redirect` — com redirect (fontes que aceitam)

## Scripts de Tracking

### Para Redirect Tracking
1. **LP Views script** — no `<head>` da pagina
   - Conta visualizacoes da LP
2. **LP Click URL** — no botao CTA
   - Redireciona para a offer: `dominio.com/click`

### Para No-Redirect Tracking
1. **Universal Script ou No-redirect Script** — no final do `<body>`
   - Rastreia visitas e identifica campanhas
2. **LP Click URL** — no botao CTA
   - Redireciona para a offer: `dominio.com/click`

### Regras de Posicionamento
- Scripts de tracking: **final do `<body>`**, nunca no `<head>`
- LP Views script (redirect): **`<head>`**
- Nunca colocar Universal Script E No-redirect Script na mesma pagina

## Click URLs

### LP padrao → Offer
```
https://track.dominio.com/click
```

### Listicle → Offers multiplas
```
https://track.dominio.com/click/1  → Offer 1
https://track.dominio.com/click/2  → Offer 2
https://track.dominio.com/click/3  → Offer 3
```

### Prelander → LP
```
https://track.dominio.com/preclick
```

### Parametros adicionais no Click URL
Possivel adicionar sub parametros:
```
https://track.dominio.com/click?sub15=variacao1
```

## Dynamic Parameters na URL da LP

A URL da LP pode conter parametros dinamicos do RedTrack:

```
https://lp.dominio.com/creatina?city={city}&country={country}&device={device}
```

Parametros disponiveis:
| Parametro | Descricao |
|-----------|-----------|
| `{city}` | Cidade do visitante |
| `{country}` | Pais |
| `{region}` | Regiao/estado |
| `{device}` | Tipo de dispositivo |
| `{os}` | Sistema operacional |
| `{browser}` | Navegador |
| `{isp}` | Provedor de internet |
| `{language}` | Idioma |
| `{traffic_channel}` | Nome do traffic channel |

## Landing Page Protection

Proteger a LP contra acesso nao autorizado:
- **Referrer check:** so permitir acessos vindos de fontes conhecidas
- **Bot protection:** bloquear bots conhecidos
- **Country filter:** restringir por pais
- Configurar no painel: Lander → Protection

## Multi-Step Funnel (Prelander + Lander + Offer)

### Scripts do Prelander
Para no-redirect com prelander, usar script especifico:
```html
<!-- Prelander tracking -->
<script src="https://track.dominio.com/pretrack.js?rtkcmpid=CAMP_ID"></script>
```

### Fluxo completo
1. Visitante chega no prelander (via parametros de tracking)
2. Script do prelander registra a visita
3. CTA do prelander usa `/preclick` → redireciona para lander
4. Script do lander registra visita na LP
5. CTA do lander usa `/click` → redireciona para offer
6. Offer source registra conversao → postback para RedTrack

### Configuracao na campanha
- Funnel type: "Pre-landing – Landing – Offer"
- Adicionar prelander, lander e offer nessa ordem
- Weights opcionais para split test entre variantes

## Troubleshooting

1. **LP Views nao registram:** script no lugar errado (deve ser no head para redirect, body para no-redirect)
2. **Click URL nao redireciona:** dominio errado ou campanha pausada
3. **Listicle com offer errada:** ordem dos click URLs nao corresponde a ordem das offers
4. **Prelander nao rastreia:** usando script de LP ao inves de pretrack.js
5. **Dynamic params nao substituem:** sintaxe errada (usar chaves, nao colchetes)
