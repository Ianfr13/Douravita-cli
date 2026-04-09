# Automation Rules — Referencia Completa

## Conceito

Regras automaticas que executam acoes baseadas em condicoes de performance.
Exemplo: pausar ad se ROAS < 1 nos ultimos 7 dias.

## Componentes de uma Regra

### 1. Rule Object
O que a regra controla:
- Campaign
- Ad group / Adset
- Ad / Creative
- Placement

Depende do traffic channel — cada fonte suporta niveis diferentes.

### 2. Action
O que fazer quando a condicao e atendida:
- **Pause** — pausar o objeto
- **Resume** — reativar
- **Adjust budget** — mudar orcamento (+ ou - %, ou valor fixo)
- **Modify bid** — mudar lance

Ate 5 acoes por regra, cada uma com ate 5 condicoes.

### 3. Condition
Quando executar a acao:
- **Metrica:** Revenue, Cost, Profit, ROI, ROAS, CPA, Conversion Rate, Clicks, Impressions
- **Operador:** >, <, >=, <=, =
- **Valor:** numero (ex: 1.5 para ROAS)
- **Periodo:** last 1/3/7/14/30 days

Exemplos:
```
Total Revenue < $100 for last 7 days
ROAS < 1.5 for last 3 days
Cost per conversion > $50 for last 7 days
Conversion rate < 2% for last 14 days
Clicks > 500 AND Conversions = 0 for last 3 days
```

### 4. Schedule
Quando verificar a regra:
- **Frequency:** 5, 15 ou 30 minutos (5/15 requerem upgrade)
- **Dias especificos:** Segunda a Sexta, 9h-18h
- **Date range:** periodo definido (ex: Black Friday)

### 5. Notifications
Como ser notificado:
- **Email:** notificacao simples
- **Webhook:** GET ou POST para URL externa (integrar com Slack, etc.)

## CLI — Gerenciar Regras

```bash
# Listar regras
cli-anything-redtrack rule list

# Ver detalhes
cli-anything-redtrack rule get <ID>

# Criar regra
cli-anything-redtrack rule create \
  --name "Pausar ROAS baixo" \
  --condition "roas < 1" \
  --action "pause"

# Ativar/pausar
cli-anything-redtrack rule update <ID> --status active
cli-anything-redtrack rule update <ID> --status paused

# Deletar
cli-anything-redtrack rule delete <ID>
```

## Suporte por Traffic Channel

| Canal | Campaign | Adset/Group | Ad | Placement |
|-------|----------|-------------|-----|-----------|
| Meta | Sim | Sim | Sim | Sim |
| Google Ads | Sim | Sim | Sim | Nao |
| TikTok | Sim | Sim | Sim | Nao |
| Bing | Sim | Sim | Sim | Nao |
| Outbrain | Sim | Nao | Sim | Nao |
| Taboola | Sim | Nao | Sim | Nao |

## Stream Optimization (Auto-Optimize)

Alem de regras manuais, RedTrack tem otimizacao automatica de streams:
- Distribui trafego entre offers/landers baseado em performance
- Pausa automaticamente variantes com baixo desempenho
- Redireciona trafego para as melhores variantes

### Configuracao
- Na campanha, setar weights iniciais para landers/offers
- Ativar stream optimization
- Definir metrica de otimizacao (conversoes, revenue, ROI)
- Definir periodo de warmup (minimo de dados antes de otimizar)

## Exemplos de Regras Uteis

### 1. Kill Switch — Pausar ads sem conversao
```
Condition: Clicks > 200 AND Conversions = 0 (last 3 days)
Action: Pause ad
Schedule: Every 30 min
```

### 2. Scale Winners — Aumentar budget
```
Condition: ROAS > 2.0 AND Conversions > 5 (last 7 days)
Action: Increase budget +20%
Schedule: Daily at 9 AM
```

### 3. Cut Losers — Pausar campaigns deficitarias
```
Condition: Cost > $100 AND Revenue < $50 (last 7 days)
Action: Pause campaign
Schedule: Every 30 min, Mon-Fri
```

### 4. Budget Cap — Limitar gasto diario
```
Condition: Cost > $500 (last 1 day)
Action: Pause campaign
Schedule: Every 15 min
Notification: Email + Webhook
```

## Troubleshooting

1. **Regra nao executa:**
   - Verificar se status e "active"
   - Verificar se o traffic channel suporta o rule object
   - Verificar se o schedule esta no horario certo
   - Verificar se a API do traffic channel esta conectada

2. **Regra executa demais:**
   - Condicoes muito sensíveis (threshold muito baixo)
   - Periodo muito curto (last 1 day pode ter picos)
   - Frequencia muito alta (5 min pode causar flip-flop)

3. **Conflito entre regras:**
   - Uma regra pausa, outra resume o mesmo objeto
   - Resolver priorizando uma ou ajustando condicoes

4. **Webhook nao dispara:**
   - Verificar URL acessivel
   - Verificar metodo (GET vs POST)
   - Testar URL manualmente
