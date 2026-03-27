# ⚡ ProcessSigma — Delivery Intelligence Pipeline

> **Business Case Black Belt** — Inteligência Operacional aplicada à cadeia de suprimentos  
> Unindo Lean Six Sigma · Engenharia de Dados · Process Mining

---

## 🎯 Objetivo

Transformar dados brutos de uma cadeia de suprimentos em decisões estratégicas que reduzam a variabilidade e aumentem a lucratividade — entregando um pipeline completo de inteligência de dados com monitoramento em tempo real.

---

## 🔍 Cenário de Ataque (O Problema Real)

O projeto foca na otimização do fluxo **Order-to-Shipping** utilizando o dataset DataCo Smart Supply Chain. As dores identificadas:

| Problema | Impacto |
|----------|---------|
| Instabilidade no Lead Time | Alta variabilidade entre envio agendado e realizado |
| Risco de Atraso (Late Delivery) | Comprometimento do SLA e satisfação do cliente |
| Baixo Nível Sigma | DPMO elevado indicando necessidade de melhoria contínua |

---

## 🏗️ Arquitetura

```
[Ingestão de Dados]
    CSV/Excel Upload ──┐
    Formulário Web  ───┴──► Supabase (PostgreSQL)
                                    │
                        ┌───────────┴───────────┐
                        ▼                       ▼
                  🥉 Bronze               Pipeline ETL
                  (dados brutos)               │
                        │               ┌──────┴──────┐
                        ▼               ▼             ▼
                  🥈 Silver          🔬 R          🔍 PM4Py
                  (dados limpos)   Estatística   Process Mining
                        │               │             │
                        ▼               └──────┬──────┘
                  🥇 Gold                      │
                  (indicadores)         Evidências &
                        │               Análise Causa Raiz
              ┌─────────┴─────────┐
              ▼                   ▼
        [Streamlit]          [Power BI]
      App interativo        Painel executivo
      (tempo real)          (stakeholders)
```

---

## 🛠️ Stack Tecnológica

| Camada | Tecnologia | Função |
|--------|-----------|--------|
| Banco de dados | Supabase (PostgreSQL) | Armazenamento + Realtime |
| ETL / Pipeline | Python + pandas | Transformações Medalhão |
| Análise estatística | R + tidyverse + ggplot2 | EDA, testes, cartas de controle |
| Process Mining | PM4Py + GraphViz | Mapeamento de processos críticos |
| App interativo | Streamlit | Dashboard público com ingestão |
| Painel executivo | Power BI | Relatório para stakeholders |

---

## 🗂️ Estrutura do Projeto

```
processsigma-delivery-intelligence/
│
├── data/
│   ├── raw/                         # Dataset original (não versionado)
│   ├── bronze/                      # Camada Bronze
│   ├── silver/                      # Camada Silver
│   └── gold/                        # Camada Gold
│
├── ingestion/
│   ├── upload_csv.py                # Ingestão via CSV/Excel
│   └── form_ingest.py               # Ingestão via formulário
│
├── pipeline/
│   ├── bronze_to_silver.py          # Limpeza e padronização
│   └── silver_to_gold.py            # Indicadores + Process Mining
│
├── analysis/
│   ├── r/                           # Análises estatísticas em R
│   │   ├── eda.R                    # Análise Exploratória
│   │   ├── control_charts.R         # Cartas de Controle (CEP)
│   │   ├── hypothesis_tests.R       # Testes de hipótese
│   │   └── sigma_level.R            # Nível Sigma / DPMO
│   └── process_mining/              # Outputs do Process Mining
│       ├── process_events_delay_analysis.csv
│       ├── process_events_delay_analysis.json
│       ├── process_map_delay_analysis.png
│       └── process_mining_debug.py
│
├── app/
│   └── streamlit/
│       ├── main.py                  # Entry point
│       ├── db.py                    # Conexão Supabase
│       └── pages/
│           ├── visao_geral.py       # KPIs principais
│           ├── otd_regiao.py        # OTD por região
│           ├── sigma_dpmo.py        # Sigma e DPMO
│           ├── process_mining.py    # Mapa de processos
│           └── injecao_dados.py     # Upload + formulário
│
├── powerbi/
│   └── docs/
│       ├── model_schema.md          # Esquema do modelo
│       └── narrative_guide.md       # Guia da narrativa
│
├── docs/
│   ├── architecture.md              # Decisões arquiteturais
│   ├── supabase_setup.md            # Configuração Supabase
│   ├── data_dictionary.md           # Dicionário de dados
│   └── PROCESS_MINING_GUIDE.md      # Guia Process Mining
│
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 📊 Dataset

**DataCo Smart Supply Chain** — Kaggle  
180.519 registros brutos → 65.752 pedidos únicos processados

---

## 📈 Indicadores Monitorados

| Indicador | Descrição | Meta |
|-----------|-----------|------|
| **OTD %** | On-Time Delivery | ≥ 95% |
| **DPMO** | Defeitos Por Milhão de Oportunidades | ≤ 6.210 (4σ) |
| **Sigma Level** | Nível Sigma do processo | ≥ 4σ |
| **Lead Time** | Variabilidade do tempo de entrega | Estável (CEP) |

---

## 🎓 Evidências para Certificação Black Belt

```
✅ Event log estruturado (CSV/JSON)      → analysis/process_mining/
✅ Mapa de processo visual (PNG)         → analysis/process_mining/
✅ Cartas de Controle (CEP)              → analysis/r/
✅ Testes de hipótese documentados       → analysis/r/
✅ Pipeline de dados reproduzível        → pipeline/
✅ Dashboard interativo publicado        → Streamlit Cloud
✅ Painel executivo                      → Power BI Service
```

---

## 🚀 Como Executar

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/processsigma-delivery-intelligence.git
cd processsigma-delivery-intelligence

# 2. Ambiente virtual Python
python -m venv .venv
.venv\Scripts\activate       # Windows
source .venv/bin/activate    # Linux/Mac

# 3. Dependências
pip install -r requirements.txt

# 4. Variáveis de ambiente
cp .env.example .env
# Preencha SUPABASE_URL e SUPABASE_KEY

# 5. Executar pipeline completo
python ingestion/upload_csv.py
python pipeline/bronze_to_silver.py
python pipeline/silver_to_gold.py

# 6. App Streamlit
streamlit run app/streamlit/main.py
```

---

## 📁 Ambiente R

```r
# Restaurar dependências R
renv::restore()

# Executar análises
source("analysis/r/eda.R")
source("analysis/r/control_charts.R")
```

---

## 📌 Status do Projeto

| Entrega | Status |
|---------|--------|
| Arquitetura Medalhão (Supabase) | ✅ Concluído |
| Pipeline Bronze → Silver → Gold | ✅ Concluído |
| Process Mining (PM4Py) | ✅ Concluído |
| App Streamlit (4 páginas) | ✅ Concluído |
| Análise Estatística em R | 🔄 Em andamento |
| Dashboard Power BI | ⏳ Aguardando |
| Deploy Streamlit Cloud | ⏳ Aguardando |

---

*ProcessSigma — Where Data Meets Process Excellence*
