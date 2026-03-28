import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from db import get_client

def buscar_gold_otd() -> pd.DataFrame:
    supabase = get_client()
    response = supabase.table("gold_otd").select("*").execute()
    return pd.DataFrame(response.data)

def buscar_gold_sigma() -> pd.DataFrame:
    supabase = get_client()
    response = supabase.table("gold_sigma").select("*").execute()
    return pd.DataFrame(response.data)

def render():
    st.title("📊 Visão Geral")
    st.markdown("Indicadores consolidados de desempenho logístico.")
    st.markdown("---")

    with st.spinner("Carregando dados..."):
        df_otd   = buscar_gold_otd()
        df_sigma = buscar_gold_sigma()

    if df_otd.empty or df_sigma.empty:
        st.warning("Nenhum dado disponível ainda.")
        return

    df_otd["period"]   = pd.to_datetime(df_otd["period"])
    df_sigma["period"] = pd.to_datetime(df_sigma["period"])

    # ── KPIs ──────────────────────────────────────────────────────
    otd_geral      = round(df_otd["on_time"].sum() / df_otd["total_deliveries"].sum() * 100, 2)
    total_entregas = int(df_otd["total_deliveries"].sum())
    sigma_atual    = df_sigma.sort_values("period").iloc[-1]["sigma_level"]
    dpmo_atual     = df_sigma.sort_values("period").iloc[-1]["dpmo"]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total de Entregas",  f"{total_entregas:,}".replace(",", "."))
    col2.metric("OTD Geral",          f"{otd_geral}%")
    col3.metric("Nível Sigma Atual",  f"{sigma_atual}σ")
    col4.metric("DPMO Atual",         f"{dpmo_atual:,.0f}".replace(",", "."))

    st.markdown("---")

    # ── OTD ao longo do tempo ─────────────────────────────────────
    df_tempo = df_otd.groupby("period", as_index=False).apply(
        lambda x: pd.Series({
            "total_deliveries": x["total_deliveries"].sum(),
            "on_time"         : x["on_time"].sum(),
        }), include_groups=False
    )
    df_tempo["otd_pct"] = round(df_tempo["on_time"] / df_tempo["total_deliveries"] * 100, 2)

    fig_otd = px.line(
        df_tempo,
        x="period",
        y="otd_pct",
        title="OTD Mensal (%)",
        labels={"period": "Período", "otd_pct": "OTD (%)"},
        markers=True
    )
    fig_otd.add_hline(y=95, line_dash="dash", line_color="red", annotation_text="Meta 95%")
    st.plotly_chart(fig_otd, use_container_width=True)

    st.markdown("---")

    # ── Top e Bottom regiões ──────────────────────────────────────
    df_regiao = df_otd.groupby("region", as_index=False).apply(
        lambda x: pd.Series({
            "total_deliveries": x["total_deliveries"].sum(),
            "on_time"         : x["on_time"].sum(),
        }), include_groups=False
    )
    df_regiao["otd_pct"] = round(df_regiao["on_time"] / df_regiao["total_deliveries"] * 100, 2)
    df_regiao = df_regiao.sort_values("otd_pct", ascending=False)

    col_top, col_bot = st.columns(2)

    with col_top:
        st.subheader("🏆 Top 5 Regiões")
        st.dataframe(
            df_regiao.head(5)[["region", "otd_pct", "total_deliveries"]],
            use_container_width=True,
            hide_index=True
        )

    with col_bot:
        st.subheader("⚠️ Bottom 5 Regiões")
        st.dataframe(
            df_regiao.tail(5)[["region", "otd_pct", "total_deliveries"]],
            use_container_width=True,
            hide_index=True
        )