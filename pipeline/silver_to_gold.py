import pandas as pd
from supabase import create_client
from dotenv import load_dotenv
from loguru import logger
import math
import os
import pm4py
from pm4py.objects.log.util import dataframe_utils
from pm4py.algo.discovery.heuristics import algorithm as heuristics
from datetime import timedelta
import json

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
    if dpmo <= 0:        return 6.0
    if dpmo >= 999999:   return 0.5
    if dpmo >= 500000:   return 1.5
    if dpmo >= 308538:   return 2.0
    if dpmo >= 66807:    return 3.0
    if dpmo >= 6210:     return 4.0
    if dpmo >= 233:      return 5.0
    x = 29.37 - 2.221 * math.log(dpmo)
    if x <= 0: return 0.5
    return round(0.8406 + math.sqrt(x), 2)

def gerar_gold_otd(df: pd.DataFrame):
    logger.info("Calculando Gold OTD...")

    resultado = []
    periodos = set()
    
    for (period, region), grupo in df.groupby(["period", "order_region"]):
        total    = len(grupo)
        on_time  = int((grupo["is_late"] == False).sum())
        otd_pct  = round(on_time / total * 100, 2) if total > 0 else 0.0
        period_str = period.strftime("%Y-%m-%d")
        periodos.add(period_str)
        resultado.append({
            "period"          : period_str,
            "region"          : str(region),
            "total_deliveries": int(total),
            "on_time"         : on_time,
            "otd_pct"         : float(otd_pct)
        })

    # Upsert: deletar registros existentes para os períodos antes de inserir
    for periodo in periodos:
        supabase.table("gold_otd") \
            .delete() \
            .eq("period", periodo) \
            .execute()
    
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
    
    # Upsert: deletar registros existentes para os períodos antes de inserir
    periodos = [r["period"] for r in registros]
    for periodo in periodos:
        supabase.table("gold_sigma") \
            .delete() \
            .eq("period", periodo) \
            .execute()
    
    supabase.table("gold_sigma").insert(registros).execute()
    logger.success(f"✅ Gold Sigma — {len(registros)} registros inseridos")

def gerar_evidencia_process_mining(df: pd.DataFrame):
    """Gera mapa de processo para casos críticos (atrasos) usando pm4py."""
    try:
        logger.info("Gerando evidência Process Mining para análise de atrasos...")
        
        # Filtrar apenas casos críticos (is_late == True)
        df_criticos = df[df["is_late"] == True].copy()
        
        if df_criticos.empty:
            logger.warning("⚠️ Nenhum caso crítico encontrado para Process Mining.")
            return
        
        logger.info(f"Casos críticos encontrados: {len(df_criticos)}")
        
        # Construir event log "empilhado" com dois eventos por caso
        eventos = []
        for idx, row in df_criticos.iterrows():
            case_id = row.get("id") or str(idx)
            
            # Evento 1: "Pedido Registrado"
            eventos.append({
                "case:concept:name": case_id,
                "concept:name": "Pedido Registrado",
                "time:timestamp": row["order_date"],
                "region": row.get("order_region", "Unknown"),
                "status": "registered"
            })
            
            # Evento 2: "Envio Concluído" (calculado com days_real)
            dias_real = row.get("days_real", 0)
            data_envio = row["order_date"] + timedelta(days=dias_real)
            eventos.append({
                "case:concept:name": case_id,
                "concept:name": "Envio Concluído",
                "time:timestamp": data_envio,
                "region": row.get("order_region", "Unknown"),
                "status": "delivered"
            })
        
        # Criar DataFrame com o event log
        log_df = pd.DataFrame(eventos)
        log_df = log_df.sort_values(["case:concept:name", "time:timestamp"]).reset_index(drop=True)
        
        logger.info(f"Event log criado com {len(log_df)} eventos")
        
        # Criar diretório se não existir
        output_dir = "analysis"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            logger.info(f"Diretório criado: {output_dir}")
        
        # Salvar como CSV
        csv_path = os.path.join(output_dir, "process_events_delay_analysis.csv")
        log_df_export = log_df.copy()
        log_df_export["time:timestamp"] = log_df_export["time:timestamp"].astype(str)
        log_df_export.to_csv(csv_path, index=False)
        logger.success(f"✅ Event Log CSV — salvo em {csv_path}")
        
        # Salvar como JSON
        json_path = os.path.join(output_dir, "process_events_delay_analysis.json")
        log_df_export.to_json(json_path, orient="records", indent=2)
        logger.success(f"✅ Event Log JSON — salvo em {json_path}")
        
        # Tentar gerar visualização PNG com GraphViz
        try:
            logger.info("Tentando gerar visualização PNG com GraphViz...")
            log_df["time:timestamp"] = pd.to_datetime(log_df["time:timestamp"])
            event_log = dataframe_utils.convert_timestamp_columns_in_df(log_df)
            
            logger.info("Descobrindo heuristics net (pode levar alguns minutos)...")
            heur_net = pm4py.discover_heuristics_net(event_log)
            
            png_path = os.path.join(output_dir, "process_map_delay_analysis.png")
            logger.info(f"Salvando mapa de processo em {png_path}...")
            pm4py.vis.save_vis_heuristics_net(heur_net, png_path)
            logger.success(f"✅ Mapa de Processo PNG — salvo em {png_path}")
            
        except Exception as viz_error:
            logger.warning(f"⚠️ Não foi possível gerar PNG: {type(viz_error).__name__}")
            logger.warning("   Motivo: GraphViz não está instalado ou não está no PATH")
            logger.info("   ℹ️  Event logs foram salvos em CSV e JSON para análise")
            logger.info("")
            logger.info("   Para instalar GraphViz e gerar visualizações:")
            logger.info("   📦 Windows: Download em https://graphviz.org/download/")
            logger.info("      Ou use: choco install graphviz (com Chocolatey)")
            logger.info("   📦 Linux: sudo apt-get install graphviz")
            logger.info("   📦 Mac: brew install graphviz")
        
        # Estatísticas do processo
        stats = {
            "total_casos": log_df["case:concept:name"].nunique(),
            "total_eventos": len(log_df),
            "atividades": sorted(log_df["concept:name"].unique().tolist()),
            "regioes": sorted(log_df["region"].unique().tolist()),
            "eventos_por_caso": len(log_df) // log_df["case:concept:name"].nunique()
        }
        
        logger.info("📊 Estatísticas do Processo de Atrasos:")
        logger.info(f"   • Total de casos críticos: {stats['total_casos']}")
        logger.info(f"   • Total de eventos: {stats['total_eventos']}")
        logger.info(f"   • Atividades: {', '.join(stats['atividades'])}")
        logger.info(f"   • Regiões afetadas: {', '.join(stats['regioes'])}")
        logger.info(f"   • Eventos por caso: {stats['eventos_por_caso']}")
        
    except Exception as e:
        logger.error(f"❌ Erro ao gerar Process Mining: {str(e)}")
        logger.error(f"Tipo de erro: {type(e).__name__}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    df = buscar_silver()
    gerar_gold_otd(df)
    gerar_gold_sigma(df)
    gerar_evidencia_process_mining(df)
    logger.success("🏆 Pipeline completo — Bronze → Silver → Gold + Process Mining")