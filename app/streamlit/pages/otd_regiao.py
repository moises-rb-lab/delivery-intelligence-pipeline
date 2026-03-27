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

def render():
    st.title("🗺️ OTD por Região")
    st.markdown("Desempenho de entregas no prazo por região e período.")
    st.markdown("---")

    with st.spinner("Carregando dados..."):
        df = buscar_gold_otd()

    if df.empty:
        st.warning("Nenhum dado disponível ainda.")
        return

    df["period"] = pd.to_datetime(df["period"])

    # ── Filtros ───────────────────────────────────────────────────
    col_f1, col_f2 = st.columns(2)

    with col_f1:
        regioes = sorted(df["region"].unique().tolist())
        regioes_sel = st.multiselect(
            "Filtrar por Região",
            options=regioes,
            default=regioes
        )

    with col_f2:
        periodo_min = df["period"].min().date()
        periodo_max = df["period"].max().date()
        periodo_sel = st.date_input(
            "Período",
            value=(periodo_min, periodo_max),
            min_value=periodo_min,
            max_value=periodo_max
        )

    # Aplicar filtros
    if len(periodo_sel) == 2:
        df = df[
            (df["region"].isin(regioes_sel)) &
            (df["period"].dt.date >= periodo_sel[0]) &
            (df["period"].dt.date <= periodo_sel[1])
        ]

    st.markdown("---")

    # ── KPIs do filtro ────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)
    col1.metric("Regiões selecionadas", len(regioes_sel))
    col2.metric("Total de Entregas",    f"{int(df['total_deliveries'].sum()):,}".replace(",", "."))
    col3.metric("OTD Médio",            f"{round(df['on_time'].sum() / df['total_deliveries'].sum() * 100, 2)}%")

    st.markdown("---")

    # ── Gráfico de barras por região ──────────────────────────────
    df_regiao = df.groupby("region", as_index=False).apply(
        lambda x: pd.Series({
            "total_deliveries": x["total_deliveries"].sum(),
            "on_time"         : x["on_time"].sum(),
        }), include_groups=False
    )
    df_regiao["otd_pct"] = round(
        df_regiao["on_time"] / df_regiao["total_deliveries"] * 100, 2
    )
    df_regiao = df_regiao.sort_values("otd_pct", ascending=True)

    fig_bar = px.bar(
        df_regiao,
        x="otd_pct",
        y="region",
        orientation="h",
        title="OTD (%) por Região",
        labels={"otd_pct": "OTD (%)", "region": "Região"},
        color="otd_pct",
        color_continuous_scale=["red", "yellow", "green"],
        range_color=[50, 100]
    )
    fig_bar.add_vline(x=95, line_dash="dash", line_color="red", annotation_text="Meta 95%")
    st.plotly_chart(fig_bar, use_container_width=True)

    # ── Evolução temporal por região ──────────────────────────────
    st.subheader("Evolução Mensal por Região")

    fig_line = px.line(
        df.sort_values("period"),
        x="period",
        y="otd_pct",
        color="region",
        title="OTD Mensal por Região (%)",
        labels={"period": "Período", "otd_pct": "OTD (%)", "region": "Região"},
        markers=True
    )
    fig_line.add_hline(y=95, line_dash="dash", line_color="red", annotation_text="Meta 95%")
    st.plotly_chart(fig_line, use_container_width=True)

    # ── Tabela detalhada ──────────────────────────────────────────
    st.subheader("Detalhamento")
    st.dataframe(
        df[["period", "region", "total_deliveries", "on_time", "otd_pct"]]
        .sort_values(["period", "otd_pct"])
        .rename(columns={
            "period"          : "Período",
            "region"          : "Região",
            "total_deliveries": "Total Entregas",
            "on_time"         : "No Prazo",
            "otd_pct"         : "OTD (%)"
        }),
        use_container_width=True,
        hide_index=True
    )