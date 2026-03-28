# ============================================================
# EDA - Analise Exploratoria de Dados
# ProcessSigma - Delivery Intelligence Pipeline
# ============================================================

library(httr2)
library(jsonlite)
library(tidyverse)
library(ggplot2)
library(dotenv)

load_dot_env(".env")

url <- Sys.getenv("SUPABASE_URL")
key <- Sys.getenv("SUPABASE_KEY")

# ── Funcao de busca paginada ─────────────────────────────────
buscar_silver <- function() {
  cat("Buscando dados do Silver...\n")
  todos <- list()
  offset <- 0
  limit  <- 1000

  repeat {
    resposta <- request(paste0(url, "/rest/v1/silver_deliveries")) |>
      req_headers(
        "apikey"        = key,
        "Authorization" = paste("Bearer", key)
      ) |>
      req_url_query(
        select = "order_id,order_date,delay_days,is_late,order_region,damage_flag,return_flag",
        limit  = limit,
        offset = offset
      ) |>
      req_perform()

    lote <- resp_body_json(resposta, simplifyVector = TRUE)

    # Verificacao correta para lista vazia ou data frame vazio
    if (length(lote) == 0 || (is.data.frame(lote) && nrow(lote) == 0)) break

    todos[[length(todos) + 1]] <- as.data.frame(lote)
    offset <- offset + limit
    cat(sprintf("Lidos: %d registros\n", offset))
  }

  df <- bind_rows(todos)
  df$order_date <- as.Date(df$order_date)
  df$period     <- as.Date(format(df$order_date, "%Y-%m-01"))
  cat(sprintf("Total carregado: %d registros\n", nrow(df)))
  return(df)
}

# ── Carregar dados ───────────────────────────────────────────
df <- buscar_silver()

# ── Estrutura ────────────────────────────────────────────────
cat("\nEstrutura dos dados:\n")
glimpse(df)

# ── Resumo estatistico do delay_days ─────────────────────────
cat("\nResumo do desvio de lead time (delay_days):\n")
df |>
  summarise(
    media   = round(mean(delay_days, na.rm = TRUE), 2),
    mediana = median(delay_days, na.rm = TRUE),
    desvio  = round(sd(delay_days, na.rm = TRUE), 2),
    minimo  = min(delay_days, na.rm = TRUE),
    maximo  = max(delay_days, na.rm = TRUE)
  ) |>
  print()

# ── Taxa de atraso por regiao ────────────────────────────────
cat("\nTaxa de atraso por regiao:\n")
df |>
  group_by(order_region) |>
  summarise(
    total       = n(),
    atrasados   = sum(is_late, na.rm = TRUE),
    taxa_atraso = round(atrasados / total * 100, 2)
  ) |>
  arrange(desc(taxa_atraso)) |>
  print(n = Inf)

# ── Criar pasta de exports ───────────────────────────────────
dir.create("analysis/r/exports", recursive = TRUE, showWarnings = FALSE)

# ── Grafico 1: Distribuicao do delay_days ────────────────────
p1 <- ggplot(df, aes(x = delay_days)) +
  geom_histogram(binwidth = 1, fill = "#4fc3f7", color = "white", alpha = 0.8) +
  geom_vline(xintercept = 0, linetype = "dashed", color = "red", linewidth = 1) +
  labs(
    title    = "Distribuicao do Desvio de Lead Time",
    subtitle = "Linha vermelha = sem desvio (prazo cumprido)",
    x        = "Desvio (dias reais - dias planejados)",
    y        = "Frequencia"
  ) +
  theme_minimal()

ggsave("analysis/r/exports/01_distribuicao_delay.png", p1,
       width = 10, height = 6, dpi = 150)
cat("Grafico 01 salvo.\n")

# ── Grafico 2: Taxa de atraso por regiao ─────────────────────
media_geral <- mean(df$is_late, na.rm = TRUE) * 100

p2 <- df |>
  group_by(order_region) |>
  summarise(taxa_atraso = round(sum(is_late) / n() * 100, 2)) |>
  arrange(desc(taxa_atraso)) |>
  ggplot(aes(x = reorder(order_region, taxa_atraso),
             y = taxa_atraso,
             fill = taxa_atraso)) +
  geom_col() +
  geom_hline(yintercept = media_geral,
             linetype = "dashed", color = "red", linewidth = 1) +
  coord_flip() +
  scale_fill_gradient(low = "#69f0ae", high = "#f4511e") +
  labs(
    title    = "Taxa de Atraso por Regiao (%)",
    subtitle = paste0("Linha vermelha = media geral (",
                      round(media_geral, 1), "%)"),
    x        = "Regiao",
    y        = "Taxa de Atraso (%)",
    fill     = "Taxa (%)"
  ) +
  theme_minimal()

ggsave("analysis/r/exports/02_atraso_por_regiao.png", p2,
       width = 10, height = 8, dpi = 150)
cat("Grafico 02 salvo.\n")

# ── Grafico 3: Evolucao mensal de atrasos ────────────────────
p3 <- df |>
  group_by(period) |>
  summarise(
    total     = n(),
    atrasados = sum(is_late, na.rm = TRUE),
    taxa      = round(atrasados / total * 100, 2)
  ) |>
  ggplot(aes(x = period, y = taxa)) +
  geom_line(color = "#f4511e", linewidth = 1) +
  geom_point(color = "#f4511e", size = 2) +
  geom_hline(yintercept = media_geral,
             linetype = "dashed", color = "gray50") +
  labs(
    title = "Evolucao Mensal da Taxa de Atraso (%)",
    x     = "Periodo",
    y     = "Taxa de Atraso (%)"
  ) +
  theme_minimal()

ggsave("analysis/r/exports/03_evolucao_mensal.png", p3,
       width = 10, height = 6, dpi = 150)
cat("Grafico 03 salvo.\n")

cat("\nEDA concluida! Graficos salvos em analysis/r/exports/\n")