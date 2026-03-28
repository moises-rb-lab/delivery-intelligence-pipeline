# ============================================================
# Nivel Sigma - Relatorio Consolidado
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

# ── Conversao DPMO para Sigma ────────────────────────────────
dpmo_para_sigma <- function(dpmo) {
  if (dpmo <= 0)      return(6.0)
  if (dpmo >= 999999) return(0.5)

  # Tabela de referencia direta para DPMO alto
  if (dpmo >= 500000) return(1.5)
  if (dpmo >= 308538) return(2.0)
  if (dpmo >= 66807)  return(3.0)
  if (dpmo >= 6210)   return(4.0)
  if (dpmo >= 233)    return(5.0)
  if (dpmo >= 3.4)    return(6.0)

  x <- 29.37 - 2.221 * log(dpmo)
  if (x <= 0) return(0.5)
  round(0.8406 + sqrt(x), 2)
}

# ── Classificacao do nivel sigma ─────────────────────────────
classificar <- function(sigma) {
  case_when(
    sigma >= 6.0 ~ "Classe Mundial",
    sigma >= 5.0 ~ "Excelente",
    sigma >= 4.0 ~ "Bom",
    sigma >= 3.0 ~ "Atencao",
    TRUE         ~ "Critico"
  )
}

# ── Carregar dados ───────────────────────────────────────────
df <- buscar_silver()

dir.create("analysis/r/exports", recursive = TRUE, showWarnings = FALSE)

# ============================================================
# CALCULO GLOBAL
# ============================================================
cat("\n============================================================\n")
cat("RELATORIO CONSOLIDADO DE NIVEL SIGMA\n")
cat("============================================================\n")

total_oportunidades <- nrow(df)
total_defeitos <- sum(df$is_late, na.rm = TRUE) +
                 sum(df$damage_flag, na.rm = TRUE) +
                 sum(df$return_flag, na.rm = TRUE)

dpmo_global   <- round(total_defeitos / total_oportunidades * 1000000, 2)
sigma_global  <- dpmo_para_sigma(dpmo_global)
classe_global <- classificar(sigma_global)

cat(sprintf("\nOportunidades totais: %d\n",   total_oportunidades))
cat(sprintf("Defeitos totais:      %d\n",   total_defeitos))
cat(sprintf("DPMO global:          %.2f\n", dpmo_global))
cat(sprintf("Nivel Sigma global:   %.2f\n", sigma_global))
cat(sprintf("Classificacao:        %s\n",   classe_global))

# ── Referencia Six Sigma ─────────────────────────────────────
cat("\nReferencia Six Sigma:\n")
cat("  6 sigma = 3.4   DPMO  (Classe Mundial)\n")
cat("  5 sigma = 233   DPMO  (Excelente)\n")
cat("  4 sigma = 6.210 DPMO  (Bom — meta minima)\n")
cat("  3 sigma = 66.807 DPMO (Atencao)\n")
cat(sprintf("  Processo atual = %.0f DPMO — META: reduzir para 6.210\n", dpmo_global))

# ============================================================
# CALCULO POR REGIAO
# ============================================================
cat("\n============================================================\n")
cat("NIVEL SIGMA POR REGIAO\n")
cat("============================================================\n")

df_regiao <- df |>
  group_by(order_region) |>
  summarise(
    oportunidades = n(),
    defeitos      = sum(is_late, na.rm = TRUE) +
                    sum(damage_flag, na.rm = TRUE) +
                    sum(return_flag, na.rm = TRUE),
    .groups = "drop"
  ) |>
  mutate(
    dpmo        = round(defeitos / oportunidades * 1000000, 2),
    sigma_level = sapply(dpmo, dpmo_para_sigma),
    classe      = classificar(sigma_level)
  ) |>
  arrange(desc(dpmo))

print(df_regiao, n = Inf)

# ============================================================
# CALCULO POR PERIODO
# ============================================================
cat("\n============================================================\n")
cat("EVOLUCAO DO NIVEL SIGMA MENSAL\n")
cat("============================================================\n")

df_periodo <- df |>
  group_by(period) |>
  summarise(
    oportunidades = n(),
    defeitos      = sum(is_late, na.rm = TRUE) +
                    sum(damage_flag, na.rm = TRUE) +
                    sum(return_flag, na.rm = TRUE),
    .groups = "drop"
  ) |>
  mutate(
    dpmo        = round(defeitos / oportunidades * 1000000, 2),
    sigma_level = sapply(dpmo, dpmo_para_sigma),
    classe      = classificar(sigma_level)
  ) |>
  arrange(period)

print(df_periodo, n = Inf)

# ── Grafico: Evolucao do Sigma mensal ────────────────────────
p_sigma <- ggplot(df_periodo, aes(x = period, y = sigma_level)) +
  geom_line(color = "#4fc3f7", linewidth = 1.2) +
  geom_point(aes(color = classe), size = 3) +
  geom_hline(yintercept = 4, linetype = "dashed",
             color = "green", linewidth = 0.8) +
  geom_hline(yintercept = 3, linetype = "dashed",
             color = "orange", linewidth = 0.8) +
  annotate("text", x = min(df_periodo$period),
           y = 4.05, label = "Meta 4 sigma",
           color = "green", size = 3.5, hjust = 0) +
  annotate("text", x = min(df_periodo$period),
           y = 3.05, label = "Limite critico 3 sigma",
           color = "orange", size = 3.5, hjust = 0) +
  scale_color_manual(values = c(
    "Classe Mundial" = "#69f0ae",
    "Excelente"      = "#4fc3f7",
    "Bom"            = "#fff176",
    "Atencao"        = "#f9a825",
    "Critico"        = "#f4511e"
  )) +
  scale_y_continuous(limits = c(0, 6)) +
  labs(
    title    = "Evolucao Mensal do Nivel Sigma",
    subtitle = paste0("Processo atual: ", sigma_global,
                      " sigma (", classe_global, ")"),
    x        = "Periodo",
    y        = "Nivel Sigma",
    color    = "Classificacao"
  ) +
  theme_minimal()

ggsave("analysis/r/exports/08_evolucao_sigma.png", p_sigma,
       width = 12, height = 7, dpi = 150)
cat("\nGrafico 08 salvo.\n")

# ── Grafico: Sigma por regiao ────────────────────────────────
p_regiao <- df_regiao |>
  ggplot(aes(x = reorder(order_region, sigma_level),
             y = sigma_level,
             fill = classe)) +
  geom_col() +
  geom_hline(yintercept = 4, linetype = "dashed",
             color = "white", linewidth = 0.8) +
  coord_flip() +
  scale_fill_manual(values = c(
    "Classe Mundial" = "#69f0ae",
    "Excelente"      = "#4fc3f7",
    "Bom"            = "#fff176",
    "Atencao"        = "#f9a825",
    "Critico"        = "#f4511e"
  )) +
  labs(
    title    = "Nivel Sigma por Regiao",
    subtitle = "Linha branca = meta minima 4 sigma",
    x        = "Regiao",
    y        = "Nivel Sigma",
    fill     = "Classificacao"
  ) +
  theme_minimal()

ggsave("analysis/r/exports/09_sigma_por_regiao.png", p_regiao,
       width = 12, height = 9, dpi = 150)
cat("Grafico 09 salvo.\n")

# ============================================================
# RESUMO EXECUTIVO
# ============================================================
cat("\n============================================================\n")
cat("RESUMO EXECUTIVO — BUSINESS CASE\n")
cat("============================================================\n")
cat(sprintf("\n  Nivel Sigma atual:    %.2f sigma\n",  sigma_global))
cat(sprintf("  DPMO atual:           %.0f\n",          dpmo_global))
cat(sprintf("  Meta (4 sigma):       6.210 DPMO\n"))
cat(sprintf("  Reducao necessaria:   %.0f defeitos/MM\n",
            dpmo_global - 6210))
cat(sprintf("  Gap percentual:       %.1f%%\n",
            (dpmo_global - 6210) / dpmo_global * 100))
cat("\n  RECOMENDACAO:\n")
cat("  Redesenho do processo central de agendamento de envios.\n")
cat("  Causa raiz: sistemica — afeta todas as 23 regioes igualmente.\n")
cat("  Evidencia: testes qui-quadrado, ANOVA e Teste T nao rejeitam H0.\n")
cat("\n============================================================\n")
cat("Analise R concluida! Todos os graficos em analysis/r/exports/\n")
cat("============================================================\n")