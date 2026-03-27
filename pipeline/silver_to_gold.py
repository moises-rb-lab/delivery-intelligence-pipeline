import pandas as pd
from supabase import create_client
from dotenv import load_dotenv
from loguru import logger
import math
import os

load_dotenv()

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def buscar_silver() -> pd.DataFrame:
    logger.info("Buscando registros do Silver...")
    todos = []
    offset = 0
    batch_size = 1000

    while True:
        response = supabase.table("silver_deliveries") \
            .select("*") \
            .range(offset, offset + batch_size - 1) \
            .execute()

        lote = response.data
        if not lote:
            break

        todos.extend(lote)
        offset += batch_size
        logger.info(f"Lidos: {len(todos)} registros")

    df = pd.DataFrame(todos)
    df["order_date"] = pd.to_datetime(df["order_date"])
    df["period"]     = df["order_date"].dt.to_period("M").dt.to_timestamp()
    logger.info(f"Total Silver carregado: {len(df)}")
    return df

def calcular_sigma(dpmo: float) -> float:
    """Converte DPMO em Nível Sigma aproximado."""
    if dpmo <= 0:
        return 6.0
    if dpmo >= 1_000_000:
        return 0.0
    # Aproximação padrão Six Sigma
    x = 29.37 - 2.221 * math.log(dpmo)
    if x <= 0:
        return 0.0
    return round(0.8406 + math.sqrt(x), 2)

def gerar_gold_otd(df: pd.DataFrame):
    logger.info("Calculando Gold OTD...")

    resultado = []
    for (period, region), grupo in df.groupby(["period", "order_region"]):
        total    = len(grupo)
        on_time  = int((grupo["is_late"] == False).sum())
        otd_pct  = round(on_time / total * 100, 2) if total > 0 else 0.0
        resultado.append({
            "period"          : period.strftime("%Y-%m-%d"),
            "region"          : str(region),
            "total_deliveries": int(total),
            "on_time"         : on_time,
            "otd_pct"         : float(otd_pct)
        })

    supabase.table("gold_otd").insert(resultado).execute()
    logger.success(f"✅ Gold OTD — {len(resultado)} registros inseridos")

def gerar_gold_sigma(df: pd.DataFrame):
    logger.info("Calculando Gold Sigma...")

    if df is None or df.empty:
        logger.warning("DataFrame vazio. Nenhum registro gerado para gold_sigma.")
        return

    required = ["period", "is_late", "damage_flag", "return_flag"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Colunas ausentes em silver_deliveries: {missing}")

    df = df.copy()
    df["damage_flag"] = df["damage_flag"].fillna(0).astype(int)
    df["return_flag"] = df["return_flag"].fillna(0).astype(int)

    gold = df.groupby("period", sort=False).apply(
        lambda x: pd.Series({
            "total_opportunities": len(x),
            "total_defects": int(
                (x["is_late"] == True).sum() +
                x["damage_flag"].sum() +
                x["return_flag"].sum()
            ),
        }),
        include_groups=False
    ).reset_index(drop=False)

    gold["dpmo"] = (gold["total_defects"] / gold["total_opportunities"] * 1_000_000).round(2)
    gold["sigma_level"] = gold["dpmo"].apply(calcular_sigma)
    gold["period"] = gold["period"].dt.strftime("%Y-%m-%d")

    registros = gold.to_dict(orient="records")
    supabase.table("gold_sigma").insert(registros).execute()
    logger.success(f"✅ Gold Sigma — {len(registros)} registros inseridos")

if __name__ == "__main__":
    df = buscar_silver()
    gerar_gold_otd(df)
    gerar_gold_sigma(df)
    logger.success("🏆 Pipeline completo — Bronze → Silver → Gold")