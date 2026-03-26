# Arquitetura — delivery-intelligence-pipeline

## Visão Geral

Este projeto implementa uma arquitetura Medalhão (Medallion Architecture)
para processamento de dados logísticos com atualização em tempo real.

---

## Camadas Medalhão

### 🥉 Bronze — Ingestão bruta
- Dados chegam via upload CSV/Excel ou formulário Streamlit
- Gravados no Supabase sem nenhuma transformação
- Tabela: `bronze_deliveries`
- Objetivo: preservar o dado original, sempre rastreável

### 🥈 Silver — Limpeza e padronização
- Remoção de nulos e duplicatas
- Padronização de tipos (datas, categorias, numéricos)
- Cálculo do campo `delay_days` (real - planejado)
- Flag `is_late` (boolean)
- Tabela: `silver_deliveries`

### 🥇 Gold — Indicadores prontos
- Agregações por região, período e transportadora
- Cálculo de OTD, DPMO e Nível Sigma
- Tabelas: `gold_otd`, `gold_sigma`, `gold_region_summary`
- Consumido diretamente pelo Streamlit e Power BI

---

## Fluxo de dados

```
[Usuário]
    │
    ├── Upload CSV/Excel ──────────────────┐
    └── Formulário Streamlit ──────────────┤
                                           ▼
                              [Supabase — tabela bronze]
                                           │
                                    trigger / scheduler
                                           │
                                           ▼
                              [Python — bronze_to_silver.py]
                                           │
                                           ▼
                              [Supabase — tabela silver]
                                           │
                                    trigger / scheduler
                                           │
                                           ▼
                              [Python — silver_to_gold.py]
                                           │
                                           ▼
                              [Supabase — tabelas gold]
                                           │
                              ┌────────────┴────────────┐
                              ▼                         ▼
                       [Streamlit]               [Power BI]
                    (app interativo)          (painel executivo)
                              │
                              ▼
                    [R — análise estatística]
                    EDA, testes, cartas de controle
```

---

## Decisões Técnicas

| Decisão | Escolha | Motivo |
|---------|---------|--------|
| Banco de dados | Supabase (PostgreSQL) | Gratuito, Realtime nativo, fácil integração Python |
| Ingestão | CSV upload + formulário | Flexibilidade para dados históricos e novos registros |
| Transformação | Python (pandas) | Familiaridade, ecossistema rico |
| Análise estatística | R | Superior para EDA e testes Six Sigma |
| Visualização interativa | Streamlit | Deploy simples, sem frontend |
| Painel executivo | Power BI | Padrão de mercado para stakeholders |

---

## Realtime — Como funciona

O Supabase expõe um canal WebSocket por tabela.
O Streamlit se inscreve nesse canal e reage a cada INSERT/UPDATE na tabela gold,
atualizando os indicadores automaticamente sem necessidade de refresh manual.

```python
# Exemplo conceitual
supabase.table("gold_otd").on("INSERT", callback).subscribe()
```
