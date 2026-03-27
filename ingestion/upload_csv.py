import pandas as pd
from supabase import create_client
from dotenv import load_dotenv
from loguru import logger
import os

load_dotenv()

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

COLUNAS = {
    "Order Id"                      : "order_id",
    "order date (DateOrders)"       : "order_date",
    "shipping date (DateOrders)"    : "ship_date",
    "Days for shipment (scheduled)" : "days_scheduled",
    "Days for shipping (real)"      : "days_real",
    "Delivery Status"               : "delivery_status",
    "Late_delivery_risk"            : "late_delivery_risk",
    "Order Region"                  : "order_region",
    "Order Country"                 : "order_country",
    "Category Name"                 : "category_name",
}

def carregar_csv(caminho: str, batch_size: int = 500):
    logger.info(f"Lendo arquivo: {caminho}")
    df = pd.read_csv(caminho, encoding="latin1", usecols=COLUNAS.keys())
    df = df.rename(columns=COLUNAS)

    # Padronizar datas
    df["order_date"] = pd.to_datetime(df["order_date"]).dt.strftime("%Y-%m-%d")
    df["ship_date"]  = pd.to_datetime(df["ship_date"]).dt.strftime("%Y-%m-%d")

    # Colunas ausentes no CSV
    df["damage_flag"] = False
    df["return_flag"] = False
    df["source"]      = "csv_upload"

    # Remover nulos
    df = df.dropna(subset=["order_id", "order_date", "delivery_status"])

    logger.info(f"Total de registros a inserir: {len(df)}")

    # Inserir em lotes
    registros = df.to_dict(orient="records")
    total = 0

    for i in range(0, len(registros), batch_size):
        lote = registros[i : i + batch_size]
        supabase.table("bronze_deliveries").insert(lote).execute()
        total += len(lote)
        logger.info(f"Inseridos: {total}/{len(registros)}")

    logger.success(f"✅ Ingestão concluída — {total} registros na tabela bronze_deliveries")

if __name__ == "__main__":
    carregar_csv("data/raw/DataCoSupplyChainDataset.csv")