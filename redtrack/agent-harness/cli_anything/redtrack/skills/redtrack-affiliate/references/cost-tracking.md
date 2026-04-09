# Cost Tracking — Referencia Completa

## Metodos de Rastreamento de Custos

### 1. Auto Update (API)
- Puxa ad spend automaticamente via API da fonte de trafego
- Requer integracao API (Meta, Google, TikTok, Bing, Outbrain, etc.)
- Modelo de custo DEVE ser CPC ou CPM (nao funciona com CPA/RevShare)

### 2. Dynamic Cost (via macro)
- Custo passado pela fonte via parametro na URL
- Exemplo: `&cost={cost}` onde `{cost}` e a macro da fonte
- Funciona com qualquer fonte que suporte macros de custo

### 3. Manual Cost Update
- Inserir custos manualmente no RedTrack
- Util para fontes sem API e sem macro de custo
- Atualizar periodicamente

## Auto Update — Setup

### Requisitos
1. Traffic channel com integracao API ativa
2. Modelo de custo: CPC ou CPM na campanha
3. Toggle "Auto update costs" ativado

### Configuracao no Traffic Channel
- **Cost update depth:** Campaign, Adset ou Ad level
  - Niveis mais profundos podem requerer upgrade do plano
- **Cost update frequency:** 5, 15 ou 30 minutos
  - 5 e 15 min requerem upgrade (padrao: 30 min)

### Configuracao na Campanha
1. Selecionar traffic channel com cost update
2. Escolher CPC ou CPM como cost model
3. Toggle "Auto update costs" ativa automaticamente

### Refresh de Dados
- Updates: a cada 5-60 min dependendo do plano
- Nao e real-time — "varias vezes por dia"
- UTC+14:00: dados recirculados diariamente para precisao
- Reconciliacao final pode levar ate 24h

## CLI — Consultar Custos

```bash
# Custos por campanha (via report endpoint)
cli-anything-redtrack cost list --date-from 2026-04-01 --date-to 2026-04-09

# Custos de campanha especifica
cli-anything-redtrack cost list --campaign-id <ID> --date-from 2026-04-01 --date-to 2026-04-09

# Report geral com custos
cli-anything-redtrack report general --date-from 2026-04-01 --date-to 2026-04-09 --group-by campaign
```

O report geral retorna metricas de custo junto com performance:
- `cost` — custo total
- `revenue` — receita total
- `profit` — lucro (revenue - cost)
- `roi` — retorno sobre investimento
- `cpc` — custo por clique
- `cpa` — custo por acao

## Manual Cost Update

```bash
# Nao ha endpoint dedicado na CLI
# Custos manuais devem ser atualizados no painel:
# Campaign → Cost → Manual update
```

## Modelos de Custo

| Modelo | Descricao | Auto-update | Uso |
|--------|-----------|-------------|-----|
| CPC | Custo por clique | Sim | Fontes de busca, display |
| CPM | Custo por mil impressoes | Sim | Display, video |
| CPA | Custo por acao | Nao | Afiliados, performance |
| RevShare | % da receita | Nao | Modelos de revenue share |
| auto | Detecta do traffic channel | Depende | Quando nao tem certeza |
| daily_budget | Orcamento diario fixo | Nao | Orcamento controlado |

## Troubleshooting

### Custos nao atualizam
1. Verificar se traffic channel tem API conectada
2. Verificar se cost model e CPC ou CPM (nao CPA/RevShare)
3. Verificar se toggle "Auto update costs" esta ligado
4. Verificar logs de erro da integracao API
5. Reconectar conta do traffic channel (OAuth pode ter expirado)

### Discrepancia de custos
1. **Timezone:** RedTrack usa UTC, fontes podem usar timezone local
2. **Delay:** dados podem levar ate 24h para reconciliar
3. **Modelo errado:** CPA/RevShare com auto-update nao funciona
4. **Profundidade:** cost depth no traffic channel pode estar diferente do nivel do report
5. **Moeda:** verificar se moedas coincidem entre fonte e RedTrack

### Custo zerado
1. Verificar se a campanha rodou no periodo
2. Verificar se auto-update esta ativo
3. Verificar se a integracao API nao tem erros
4. Para manual: verificar se o custo foi inserido no periodo correto
