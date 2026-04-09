# Campanhas RedTrack — Referencia Completa

## Tipos de Funil

### 1. Offer Only (Direct Linking)
Trafego vai direto para a oferta, sem landing page.
- Usar quando a fonte aceita redirect
- Mais simples de configurar
- Funnel: selecionar apenas o Offer

### 2. Landing + Offer
Trafego → Landing Page → Offer
- Caso mais comum para afiliados
- Requer: lander criado + offer criado
- CTA da LP usa Click URL: `dominio.com/click`

### 3. Prelanding + Landing + Offer (Multi-step)
Trafego → Prelander → Lander → Offer
- Para funis com aquecimento (VSL, quiz, artigo)
- Prelander usa: `dominio.com/preclick`
- Lander usa: `dominio.com/click`
- Cada etapa precisa do script de tracking correto

## Configuracao da Campanha

### Aba General
- **Nome:** descritivo (ex: "FB - Creatina BR - Interesse")
- **Traffic Channel:** fonte ja criada
- **Tracking Domain:** dominio custom (CNAME)
- **Cost Model:** CPC, CPM, CPA, RevShare, auto, daily_budget
- **Cost Value:** valor unitario (ex: 0.15 para CPC)

### Aba Funnels
- Selecionar tipo de funil
- Adicionar elementos (offer, lander, prelander)
- **Weights:** se multiplos landers/offers, definir peso (%) para split test
- Ordem dos elementos importa para listicles

### Aba S2S Postback
- Preenchido automaticamente com dados do traffic channel
- Nao editar a menos que saiba o que esta fazendo
- Se o traffic channel mudar, a campanha precisa ser atualizada

### Aba Auto Update Costs
- **Toggle:** ligar para fontes com API (Meta, Google, TikTok)
- Requer cost model CPC ou CPM
- Frequencia: 5, 15 ou 30 min (depende do plano)

### Extra Settings
- **Creatives:** para tracking de criativos individuais
- **Custom Payouts:** sobrescrever payout da offer por campanha
- **Impression forwarding:** enviar impressoes para a rede
- **Click forwarding:** forward de cliques
- **Throttling:** limitar cliques por segundo

## Tracking Links

Apos criar a campanha, obter links:

```bash
cli-anything-redtrack campaign links <CAMP_ID>
```

Retorna:
- **Redirect URL:** `https://track.dominio.com/CAMP_HASH` — para fontes que aceitam redirect
- **No-redirect params:** parametros para adicionar a URL da LP
- **Universal script params:** para usar com script universal

### Parametros de Tracking (No-redirect)
Exemplo para Meta:
```
?cmpid=CAMP_ID&sub1={{ad.id}}&sub2={{adset.id}}&sub3={{campaign.id}}&sub4={{ad.name}}&utm_source=facebook&fbclid={{fbclid}}
```

**fbclid SEMPRE por ultimo** — nenhum parametro depois dele.

## Redirect Types

### Regular Redirect (302)
- Mais rapido, feito no browser
- Padrao para maioria das fontes
- URL visivel na barra por fracao de segundo

### Server Redirect (302 + hidden referrer)
- Feito no servidor, esconde o referrer
- Bom para quando nao quer que o offer source veja a origem

### Meta Refresh (hidden referrer)
- Client-side, via tag meta
- Mais lento que 302
- Usado quando server redirect nao funciona

### Double Meta Refresh
- Dois redirecionamentos
- Mascara completamente a fonte de trafego original
- Mais lento, usar apenas quando necessario

## Conditional Postback

Permite enviar postback para o traffic channel apenas se certas condicoes forem atendidas:
- Converter apenas se payout > X
- Converter apenas para eventos especificos
- Util para otimizacao de campanhas

## Erros Comuns

1. **Postback URL muda ao trocar traffic channel** — sempre verificar
2. **Weights nao somam 100%** — RedTrack normaliza mas melhor garantir
3. **Auto-update costs com CPA** — nao funciona, usar CPC ou CPM
4. **Missing cmpid** — sem esse parametro, trafego cai na campanha organica
5. **fbclid nao e o ultimo parametro** — quebra atribuicao Meta
