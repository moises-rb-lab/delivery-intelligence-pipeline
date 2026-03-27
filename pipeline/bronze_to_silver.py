import pandas as pd
from supabase import create_client
from dotenv import load_dotenv
from loguru import logger
import os

load_dotenv()

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def buscar_bronze(batch_size: int = 1000) -> list:
    logger.info("Buscando registros do Bronze...")
    todos = []
    offset = 0

    while True:
        response = supabase.table("bronze_deliveries") \
            .select("*") \
            .range(offset, offset + batch_size - 1) \
            .execute()

        lote = response.data
        if not lote:
            break

        todos.extend(lote)
        offset += batch_size
        logger.info(f"Lidos: {len(todos)} registros")

    logger.info(f"Total Bronze carregado: {len(todos)}")
    return todos

def transformar(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Aplicando transformações Silver...")

    # Renomear bronze_id
    df = df.rename(columns={"id": "bronze_id"})

    # Calcular delay e flag de atraso
    df["delay_days"] = df["days_real"] - df["days_scheduled"]
    df["is_late"]    = df["delay_days"] > 0

    # Padronizar strings
    df["delivery_status"] = df["delivery_status"].str.strip().str.title()
    df["order_region"]    = df["order_region"].str.strip().str.upper()

    # Remover duplicatas por order_id
    df = df.drop_duplicates(subset=["order_id"])

    # Remover nulos críticos
    df = df.dropna(subset=["order_id", "order_date", "delay_days"])

    # Selecionar apenas colunas do Silver
    colunas = [
        "bronze_id", "order_id", "order_date",
        "delay_days", "is_late", "delivery_status",
        "order_region", "damage_flag", "return_flag"
    ]
    df = df[colunas]

    logger.info(f"Registros após transformação: {len(df)}")
    return df

def inserir_silver(df: pd.DataFrame, batch_size: int = 500):
    registros = df.to_dict(orient="records")
    total = 0

    for i in range(0, len(registros), batch_size):
        lote = registros[i : i + batch_size]
        supabase.table("silver_deliveries").insert(lote).execute()
        total += len(lote)
        logger.info(f"Silver inseridos: {total}/{len(registros)}")

    logger.success(f"✅ Bronze → Silver concluído — {total} registros")

if __name__ == "__main__":
    dados   = buscar_bronze()
    df      = pd.DataFrame(dados)
    df      = transformar(df)
    inserir_silver(df)