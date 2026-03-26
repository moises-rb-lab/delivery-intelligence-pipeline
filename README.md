# 🚚 delivery-intelligence-pipeline

Pipeline de inteligência de dados para análise de qualidade em logística de entregas,
aplicando metodologia Six Sigma com arquitetura Medalhão (Bronze → Silver → Gold).

---

## 🎯 Objetivo

Monitorar em tempo real os indicadores de desempenho logístico — atrasos, avarias e devoluções —
permitindo ingestão contínua de dados e atualização automática dos dashboards.

---

## 🗂️ Arquitetura do Projeto

```
delivery-intelligence-pipeline/
│
├── data/                        # Camadas Medalhão
│   ├── raw/                     # Dados brutos originais (não tocar)
│   ├── bronze/                  # Ingestão bruta no banco (1:1 com raw)
│   ├── silver/                  # Dados limpos e padronizados
│   └── gold/                    # Indicadores prontos para consumo
│
├── ingestion/                   # Scripts de ingestão de dados
│   ├── upload_csv.py            # Upload via arquivo CSV/Excel
│   └── form_ingest.py           # Ingestão via formulário Streamlit
│
├── pipeline/                    # Transformações Bronze → Silver → Gold
│   ├── bronze_to_silver.py      # Limpeza e padronização
│   ├── silver_to_gold.py        # Cálculo de indicadores Six Sigma
│   └── scheduler.py             # Agendamento e trigger de pipeline
│
├── analysis/
│   └── r/                       # Análises estatísticas em R
│       ├── eda.R                # Análise Exploratória de Dados
│       ├── hypothesis_tests.R   # Testes de hipótese (t-test, ANOVA)
│       ├── control_charts.R     # Cartas de Controle (CEP)
│       └── sigma_level.R        # Cálculo do Nível Sigma / DPMO
│
├── app/
│   └── streamlit/               # Aplicação web interativa
│       ├── main.py              # Entry point do app
│       ├── pages/               # Páginas do dashboard
│       └── components/          # Componentes reutilizáveis
│
├── powerbi/
│   └── docs/                    # Documentação do modelo Power BI
│       ├── model_schema.md      # Esquema do modelo de dados
│       └── narrative_guide.md   # Guia da narrativa do dashboard
│
├── docs/                        # Documentação geral
│   ├── architecture.md          # Decisões arquiteturais
│   ├── supabase_setup.md        # Configuração do Supabase
│   └── data_dictionary.md       # Dicionário de dados
│
├── .env.example                 # Variáveis de ambiente (template)
├── .gitignore                   # Arquivos ignorados pelo Git
├── requirements.txt             # Dependências Python
└── README.md                    # Este arquivo
```

---

## 🛠️ Stack Tecnológica

| Camada | Tecnologia | Função |
|--------|-----------|--------|
| Banco de dados | Supabase (PostgreSQL) | Armazenamento + Realtime |
| Análise estatística | R + tidyverse + ggplot2 | EDA, testes, cartas de controle |
| Pipeline / ETL | Python + pandas | Transformações Medalhão |
| App interativo | Streamlit | Dashboard público com ingestão |
| Painel executivo | Power BI | Relatório para stakeholders |

---

## 📊 Dataset

**DataCo Smart Supply Chain**
- Fonte: Kaggle
- Registros: ~180.000
- Colunas principais: `Days_for_shipping_real`, `Days_for_shipment_scheduled`,
  `Late_delivery_risk`, `Delivery_Status`, `Order_Region`

---

## 📈 Indicadores Six Sigma monitorados

- **OTD** — On-Time Delivery (% de entregas no prazo)
- **DPMO** — Defeitos Por Milhão de Oportunidades
- **Sigma Level** — Nível Sigma do processo
- **Taxa de Avarias** — % de pedidos com avaria registrada
- **Taxa de Devolução** — % de pedidos devolvidos por região

---

## 🚀 Como executar

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/delivery-intelligence-pipeline.git
cd delivery-intelligence-pipeline

# 2. Crie o ambiente virtual Python
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Configure as variáveis de ambiente
cp .env.example .env
# Edite o .env com suas credenciais do Supabase

# 5. Execute o app Streamlit
streamlit run app/streamlit/main.py
```

---

## 📁 Ambientes R

Este projeto usa `renv` para isolar as dependências R.

```r
# Restaurar ambiente R
renv::restore()
```

---

## 🔐 Variáveis de Ambiente

Copie `.env.example` para `.env` e preencha:

```
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=your-anon-key
```

> ⚠️ Nunca suba o `.env` para o repositório.

---

## 📌 Status do Projeto

| Fase | Status |
|------|--------|
| Estrutura do repositório | ✅ Concluído |
| Modelagem do banco (Supabase) | 🔄 Em andamento |
| Pipeline Bronze → Silver → Gold | ⏳ Aguardando |
| Análise estatística em R | ⏳ Aguardando |
| App Streamlit | ⏳ Aguardando |
| Dashboard Power BI | ⏳ Aguardando |
