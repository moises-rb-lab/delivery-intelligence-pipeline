# Dicionário de Dados

Baseado no dataset **DataCo Smart Supply Chain** (Kaggle).

---

## Tabela: bronze_deliveries

Dados brutos ingeridos sem transformação.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | uuid | Chave primária gerada pelo Supabase |
| `order_id` | integer | ID do pedido original |
| `order_date` | date | Data do pedido |
| `ship_date` | date | Data de envio |
| `days_scheduled` | integer | Prazo planejado de entrega (dias) |
| `days_real` | integer | Prazo real de entrega (dias) |
| `delivery_status` | varchar | Status: Advance, Late, On Time, Shipping Canceled |
| `late_delivery_risk` | integer | Flag de risco (0 = sem risco, 1 = com risco) |
| `order_region` | varchar | Região do pedido |
| `order_country` | varchar | País do pedido |
| `category_name` | varchar | Categoria do produto |
| `damage_flag` | boolean | Avaria registrada (true/false) |
| `return_flag` | boolean | Devolução registrada (true/false) |
| `ingested_at` | timestamp | Data/hora da ingestão no sistema |
| `source` | varchar | Origem: 'csv_upload' ou 'form' |

---

## Tabela: silver_deliveries

Dados limpos e enriquecidos.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | uuid | Chave primária |
| `bronze_id` | uuid | FK para bronze_deliveries |
| `order_id` | integer | ID do pedido |
| `order_date` | date | Data do pedido |
| `delay_days` | integer | days_real - days_scheduled (negativo = adiantado) |
| `is_late` | boolean | true se delay_days > 0 |
| `delivery_status` | varchar | Padronizado e validado |
| `order_region` | varchar | Padronizado (uppercase, sem espaços extras) |
| `damage_flag` | boolean | Avaria |
| `return_flag` | boolean | Devolução |
| `processed_at` | timestamp | Data/hora do processamento Silver |

---

## Tabelas: gold_*

### gold_otd — On-Time Delivery por período e região

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | uuid | Chave primária |
| `period` | date | Mês de referência |
| `region` | varchar | Região |
| `total_deliveries` | integer | Total de entregas no período |
| `on_time` | integer | Entregas no prazo |
| `otd_pct` | numeric | OTD em % |
| `updated_at` | timestamp | Última atualização |

### gold_sigma — Nível Sigma por período

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | uuid | Chave primária |
| `period` | date | Mês de referência |
| `total_opportunities` | integer | Total de oportunidades |
| `total_defects` | integer | Total de defeitos (atrasos + avarias) |
| `dpmo` | numeric | Defeitos Por Milhão de Oportunidades |
| `sigma_level` | numeric | Nível Sigma equivalente |
| `updated_at` | timestamp | Última atualização |

---

## Definição de "Defeito" (Six Sigma)

Para este projeto, um **defeito** é qualquer entrega que apresente ao menos uma das condições:
- `is_late = true` (entrega fora do prazo)
- `damage_flag = true` (avaria registrada)
- `return_flag = true` (devolução registrada)
