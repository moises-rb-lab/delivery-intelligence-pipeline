# ============================================================
# Testes de Hipotese
# ProcessSigma - Delivery Intelligence Pipeline
# ============================================================

library(httr2)
library(jsonlite)
library(tidyverse)
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
  cat(sprintf("Total carregado: %d registros\n", nrow(df)))
  return(df)
}

df <- buscar_silver()

dir.create("analysis/r/exports", recursive = TRUE, showWarnings = FALSE)

# ============================================================
# TESTE 1 — Qui-Quadrado
# Pergunta: A taxa de atraso e diferente entre as regioes?
# Hipotese nula (H0): proporcao de atrasos e igual em todas
# ============================================================
cat("\n============================================================\n")
cat("TESTE 1 — Qui-Quadrado: atraso vs regiao\n")
cat("H0: a taxa de atraso e igual em todas as regioes\n")
cat("H1: existe pelo menos uma regiao com taxa diferente\n")
cat("============================================================\n")

tabela_contingencia <- table(df$order_region, df$is_late)
teste_qui <- chisq.test(tabela_contingencia)

cat(sprintf("\nQui-quadrado: %.2f\n", teste_qui$statistic))
cat(sprintf("p-valor:      %.6f\n", teste_qui$p.value))

if (teste_qui$p.value < 0.05) {
  cat("CONCLUSAO: Rejeita H0 — as taxas de atraso SAO diferentes entre regioes (p < 0.05)\n")
  cat("Implicacao: existe causa regional contribuindo para os atrasos.\n")
} else {
  cat("CONCLUSAO: Nao rejeita H0 — taxas similares entre regioes.\n")
  cat("Implicacao: o problema e sistemico, nao regional.\n")
}

# ============================================================
# TESTE 2 — ANOVA
# Pergunta: O delay_days medio e diferente entre regioes?
# H0: media do delay_days e igual em todas as regioes
# ============================================================
cat("\n============================================================\n")
cat("TESTE 2 — ANOVA: delay_days por regiao\n")
cat("H0: media do desvio de lead time e igual em todas as regioes\n")
cat("H1: pelo menos uma regiao tem media diferente\n")
cat("============================================================\n")

modelo_anova <- aov(delay_days ~ order_region, data = df)
resultado_anova <- summary(modelo_anova)
print(resultado_anova)

p_anova <- resultado_anova[[1]]$`Pr(>F)`[1]

if (p_anova < 0.05) {
  cat("CONCLUSAO: Rejeita H0 — o desvio mediano difere entre regioes (p < 0.05)\n")
} else {
  cat("CONCLUSAO: Nao rejeita H0 — desvios similares entre regioes.\n")
}

# ── Post-hoc: quais regioes diferem entre si? ────────────────
cat("\nPost-hoc Tukey — Top 10 pares mais diferentes:\n")
tukey <- TukeyHSD(modelo_anova)
df_tukey <- as.data.frame(tukey$order_region)
df_tukey$par <- rownames(df_tukey)
df_tukey |>
  filter(`p adj` < 0.05) |>
  arrange(`p adj`) |>
  head(10) |>
  select(par, diff, `p adj`) |>
  print()

# ============================================================
# TESTE 3 — Teste T
# Pergunta: O delay_days do pior vs melhor regiao
# e estatisticamente diferente?
# ============================================================
cat("\n============================================================\n")
cat("TESTE 3 — Teste T: pior vs melhor regiao\n")
cat("============================================================\n")

taxa_regiao <- df |>
  group_by(order_region) |>
  summarise(taxa = mean(is_late, na.rm = TRUE)) |>
  arrange(desc(taxa))

pior  <- taxa_regiao$order_region[1]
melhor <- taxa_regiao$order_region[nrow(taxa_regiao)]

cat(sprintf("Pior regiao:  %s\n", pior))
cat(sprintf("Melhor regiao: %s\n", melhor))

grupo_pior   <- df$delay_days[df$order_region == pior]
grupo_melhor <- df$delay_days[df$order_region == melhor]

teste_t <- t.test(grupo_pior, grupo_melhor)

cat(sprintf("\nMedia pior:   %.3f dias\n", mean(grupo_pior)))
cat(sprintf("Media melhor: %.3f dias\n", mean(grupo_melhor)))
cat(sprintf("p-valor:      %.6f\n", teste_t$p.value))

if (teste_t$p.value < 0.05) {
  cat("CONCLUSAO: Diferenca estatisticamente significativa (p < 0.05)\n")
} else {
  cat("CONCLUSAO: Diferenca NAO significativa — variacao pode ser ruido.\n")
}

# ── Grafico: boxplot delay_days por regiao ───────────────────
cat("\nGerando grafico de boxplot...\n")

p_box <- df |>
  group_by(order_region) |>
  mutate(taxa = mean(is_late)) |>
  ungroup() |>
  mutate(order_region = reorder(order_region, taxa)) |>
  ggplot(aes(x = order_region, y = delay_days, fill = order_region)) +
  geom_boxplot(outlier.alpha = 0.3, outlier.size = 0.8) +
  geom_hline(yintercept = 0, linetype = "dashed",
             color = "red", linewidth = 0.8) +
  coord_flip() +
  labs(
    title    = "Distribuicao do Desvio de Lead Time por Regiao",
    subtitle = "Linha vermelha = sem desvio | ordenado por taxa de atraso",
    x        = "Regiao",
    y        = "Desvio (dias)",
  ) +
  theme_minimal() +
  theme(legend.position = "none")

ggsave("analysis/r/exports/07_boxplot_regiao.png", p_box,
       width = 12, height = 9, dpi = 150)
cat("Grafico 07 salvo.\n")

cat("\nTestes de hipotese concluidos!\n")