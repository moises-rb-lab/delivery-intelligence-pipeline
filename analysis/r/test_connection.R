library(httr2)
library(jsonlite)
library(dotenv)

load_dot_env(".env")

url <- Sys.getenv("SUPABASE_URL")
key <- Sys.getenv("SUPABASE_KEY")

# Teste: buscar 5 registros do Silver
resposta <- request(paste0(url, "/rest/v1/silver_deliveries")) |>
  req_headers(
    "apikey"        = key,
    "Authorization" = paste("Bearer", key)
  ) |>
  req_url_query(limit = 5) |>
  req_perform()

dados <- resp_body_json(resposta, simplifyVector = TRUE)

cat("Conexao via API REST: OK\n")
cat(sprintf("Registros retornados: %d\n", nrow(dados)))
print(head(dados))