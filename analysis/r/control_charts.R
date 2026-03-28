# ============================================================
# Cartas de Controle - CEP
# ProcessSigma - Delivery Intelligence Pipeline
# ============================================================

library(httr2)
library(jsonlite)
library(tidyverse)
library(qcc)
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
        select = "order_id,order_date,delay_days,is_late,order_region",
        limit  = limit,
        offset = offset
      ) |>
      req_perform()

    lote <- resp_body_json(resposta, simplifyVector = TRUE)

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

dir.create("analysis/r/exports", recursive = TRUE, showWarnings = FALSE)

# ── Agregar por periodo ──────────────────────────────────────
df_mensal <- df |>
  group_by(period) |>
  summarise(
    total     = n(),
    atrasados = sum(is_late, na.rm = TRUE),
    prop      = atrasados / total
  ) |>
  arrange(period)

cat("\nResumo mensal:\n")
print(df_mensal)

# ============================================================
# CARTA P — Proporcao de defeitos (atrasos)
# Equivalente ao p-chart do Minitab
# ============================================================
cat("\nGerando Carta P...\n")

png("analysis/r/exports/04_carta_p_atrasos.png",
    width = 1200, height = 700, res = 120)

carta_p <- qcc(
  data      = df_mensal$atrasados,
  sizes     = df_mensal$total,
  type      = "p",
  title     = "Carta P — Proporcao de Entregas com Atraso",
  xlab      = "Periodo (mes)",
  ylab      = "Proporcao de Atrasos",
  labels    = format(df_mensal$period, "%b/%y")
)

dev.off()
cat("Carta P salva.\n")

# ── Resumo da Carta P ────────────────────────────────────────
cat("\nEstatisticas da Carta P:\n")
cat(sprintf("  Media (CL):  %.4f (%.1f%%)\n",
    carta_p$center, carta_p$center * 100))
cat(sprintf("  LSC (UCL):   %.4f (%.1f%%)\n",
    max(carta_p$limits), max(carta_p$limits) * 100))
cat(sprintf("  LIC (LCL):   %.4f (%.1f%%)\n",
    min(carta_p$limits), min(carta_p$limits) * 100))

pontos_fora <- length(carta_p$violations$beyond.limits)
cat(sprintf("  Pontos fora: %d\n", pontos_fora))

if (pontos_fora > 0) {
  cat("  ATENCAO: Processo com pontos fora de controle!\n")
  cat(sprintf("  Periodos criticos: %s\n",
      paste(format(df_mensal$period[carta_p$violations$beyond.limits], "%b/%y"),
            collapse = ", ")))
} else {
  cat("  Processo sob controle estatistico.\n")
  cat("  POREM: Media de 57% de atrasos indica processo FORA das especificacoes.\n")
}

# ============================================================
# CARTA XBAR — Variabilidade do delay_days por periodo
# Mostra se o desvio medio esta estavel mes a mes
# ============================================================
cat("\nGerando Carta XBar...\n")

# Agrupar em subgrupos mensais — amostra de 30 por mes para XBar
set.seed(42)
subgrupos <- df |>
  group_by(period) |>
  slice_sample(n = 30, replace = FALSE) |>
  summarise(valores = list(delay_days)) |>
  pull(valores)

# Converter para matriz
min_size <- min(sapply(subgrupos, length))
mat <- do.call(rbind, lapply(subgrupos, function(x) x[1:min_size]))

png("analysis/r/exports/05_carta_xbar_delay.png",
    width = 1200, height = 900, res = 120)

carta_xbar <- qcc(
  data  = mat,
  type  = "xbar",
  title = "Carta XBar — Desvio Medio do Lead Time por Periodo",
  xlab  = "Periodo (mes)",
  ylab  = "Desvio Medio (dias)"
)

dev.off()
cat("Carta XBar salva.\n")

# ============================================================
# ANALISE DE CAPABILIDADE
# Cp e Cpk — o processo e capaz de cumprir o prazo?
# Especificacao: delay_days deve estar entre -1 e +1 dia
# ============================================================
cat("\nGerando Analise de Capabilidade...\n")

png("analysis/r/exports/06_capabilidade.png",
    width = 1200, height = 800, res = 120)

capabilidade <- process.capability(
  carta_xbar,
  spec.limits = c(-1, 1),
  target      = 0,
)

dev.off()
cat("Analise de Capabilidade salva.\n")

# ── Resumo da Capabilidade ───────────────────────────────────
cat("\nIndices de Capabilidade:\n")
cat(sprintf("  Cp:  %.2f\n", capabilidade$indices[1]))
cat(sprintf("  Cpk: %.2f\n", capabilidade$indices[2]))

if (capabilidade$indices[2] < 1.0) {
  cat("  PROCESSO NAO CAPAZ (Cpk < 1.0)\n")
  cat("  O processo nao consegue cumprir o prazo de entrega de forma consistente.\n")
} else if (capabilidade$indices[2] < 1.33) {
  cat("  PROCESSO MARGINALMENTE CAPAZ (1.0 <= Cpk < 1.33)\n")
} else {
  cat("  PROCESSO CAPAZ (Cpk >= 1.33)\n")
}

cat("\nCEP concluido! Graficos salvos em analysis/r/exports/\n")