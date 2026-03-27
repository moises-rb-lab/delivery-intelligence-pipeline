# Arquitetura — ProcessSigma Delivery Intelligence

## Visão Geral

Pipeline de inteligência operacional que combina **Lean Six Sigma**, **Engenharia de Dados** e **Process Mining** para análise e melhoria contínua de processos logísticos.

---

## Camadas Medalhão

### 🥉 Bronze — Ingestão bruta
- Dados chegam via upload CSV/Excel ou formulário Streamlit
- Gravados no Supabase sem nenhuma transformação
- Tabela: `bronze_deliveries`
- Objetivo: preservar o dado original, sempre rastreável

### 🥈 Silver — Limpeza e padronização
- Remoção de nulos e duplicatas por `order_id`
- Cálculo do campo `delay_days` (real - planejado)
- Flag `is_late` (boolean)
- Padronização de regiões e status
- Tabela: `silver_deliveries`

### 🥇 Gold — Indicadores prontos
- OTD por região e período
- DPMO e Nível Sigma mensais
- Consumido pelo Streamlit (Realtime) e Power BI
- Tabelas: `gold_otd`, `gold_sigma`

---

## Fluxo Completo de Dados

```
[Usuário]
    │
    ├── Upload CSV/Excel ──────────────────┐
    └── Formulário Streamlit ──────────────┤
                                           ▼
                              [Supabase — bronze_deliveries]
                                           │
                                    bronze_to_silver.py
                                           │
                                           ▼
                              [Supabase — silver_deliveries]
                                           │
                         ┌─────────────────┴─────────────────┐
                         ▼                                   ▼
                silver_to_gold.py                     analysis/r/
                         │                            eda.R
                         │                            control_charts.R
                ┌────────┴────────┐                   hypothesis_tests.R
                ▼                 ▼                         │
          gold_otd          gold_sigma                      ▼
          gold_sigma              │                  Cartas de Controle
                │                 └──► Process Mining      CEP / DPMO
                │                      (PM4Py)
                │                      event_log.csv
                │                      process_map.png
                │
    ┌───────────┴───────────┐
    ▼                       ▼
[Streamlit]            [Power BI]
Visão Geral            Modelo DAX
OTD por Região         Narrativa
Sigma e DPMO           Painel Executivo
Process Mining
Injeção de Dados
```

---

## Camada de Análise — R + Process Mining

### R (análise estatística)
Atua sobre os dados da camada Silver e Gold para validação estatística:

| Script | Função |
|--------|--------|
| `eda.R` | Distribuições, correlações, outliers |
| `control_charts.R` | Cartas XBar, p-chart — estabilidade do processo |
| `hypothesis_tests.R` | Teste t, ANOVA — diferenças entre regiões/períodos |
| `sigma_level.R` | Cálculo e validação do Nível Sigma |

### Process Mining (PM4Py)
Atua sobre os casos críticos da camada Silver (`is_late = True`):

| Output | Formato | Uso |
|--------|---------|-----|
| Event log | CSV / JSON | Análise em ferramentas externas |
| Heuristics Net | PNG | Evidência visual do fluxo desviante |
| Estatísticas | Log terminal | Documentação do Business Case |

---

## Realtime — Como funciona

O Supabase expõe um canal WebSocket por tabela.
O Streamlit se inscreve nas tabelas `gold_otd` e `gold_sigma` e reage
a cada INSERT/UPDATE atualizando os indicadores automaticamente.

---

## Decisões Técnicas

| Decisão | Escolha | Motivo |
|---------|---------|--------|
| Banco de dados | Supabase (PostgreSQL) | Gratuito, Realtime nativo |
| ETL | Python (pandas) | Familiaridade, ecossistema rico |
| Análise estatística | R | Superior para EDA e Six Sigma |
| Process Mining | PM4Py + GraphViz | Padrão acadêmico e industrial |
| Visualização interativa | Streamlit | Deploy simples, sem frontend |
| Painel executivo | Power BI | Padrão de mercado corporativo |

---

## Evidências para Black Belt

O projeto gera automaticamente todas as evidências necessárias:

```
analysis/
├── r/
│   ├── Cartas de Controle (CEP)
│   ├── Testes de Hipótese
│   └── Análise de Capability
└── process_mining/
    ├── Event Log (CSV/JSON)
    └── Mapa de Processo (PNG)
```
