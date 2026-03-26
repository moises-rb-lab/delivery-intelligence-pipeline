# Configuração do Supabase

## 1. Criar conta e projeto

1. Acesse https://supabase.com e crie uma conta gratuita
2. Clique em **New Project**
3. Nome sugerido: `delivery-intelligence-pipeline`
4. Anote a **URL** e a **anon key** — vão para o `.env`

---

## 2. Criar as tabelas

Execute os scripts abaixo no **SQL Editor** do Supabase.

### Bronze

```sql
CREATE TABLE bronze_deliveries (
  id               UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  order_id         INTEGER,
  order_date       DATE,
  ship_date        DATE,
  days_scheduled   INTEGER,
  days_real        INTEGER,
  delivery_status  VARCHAR(50),
  late_delivery_risk INTEGER,
  order_region     VARCHAR(100),
  order_country    VARCHAR(100),
  category_name    VARCHAR(100),
  damage_flag      BOOLEAN DEFAULT FALSE,
  return_flag      BOOLEAN DEFAULT FALSE,
  ingested_at      TIMESTAMP DEFAULT NOW(),
  source           VARCHAR(20)
);
```

### Silver

```sql
CREATE TABLE silver_deliveries (
  id              UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  bronze_id       UUID REFERENCES bronze_deliveries(id),
  order_id        INTEGER,
  order_date      DATE,
  delay_days      INTEGER,
  is_late         BOOLEAN,
  delivery_status VARCHAR(50),
  order_region    VARCHAR(100),
  damage_flag     BOOLEAN,
  return_flag     BOOLEAN,
  processed_at    TIMESTAMP DEFAULT NOW()
);
```

### Gold — OTD

```sql
CREATE TABLE gold_otd (
  id                 UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  period             DATE,
  region             VARCHAR(100),
  total_deliveries   INTEGER,
  on_time            INTEGER,
  otd_pct            NUMERIC(5,2),
  updated_at         TIMESTAMP DEFAULT NOW()
);
```

### Gold — Sigma

```sql
CREATE TABLE gold_sigma (
  id                    UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  period                DATE,
  total_opportunities   INTEGER,
  total_defects         INTEGER,
  dpmo                  NUMERIC(10,2),
  sigma_level           NUMERIC(4,2),
  updated_at            TIMESTAMP DEFAULT NOW()
);
```

---

## 3. Habilitar Realtime

No painel do Supabase:
1. Vá em **Database → Replication**
2. Habilite Realtime para as tabelas: `gold_otd` e `gold_sigma`

---

## 4. Variáveis de ambiente

Copie `.env.example` para `.env` e preencha:

```
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=your-anon-key
```
