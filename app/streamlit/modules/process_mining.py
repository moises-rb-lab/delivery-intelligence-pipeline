import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from db import get_client

CAMINHO_CSV  = "analysis/process_mining/process_events_delay_analysis.csv"
CAMINHO_JSON = "analysis/process_mining/process_events_delay_analysis.json"
CAMINHO_PNG  = "analysis/process_mining/process_map_delay_analysis.png"

TOTAL_BRONZE = 180519
TOTAL_SILVER = 65752

def buscar_silver() -> pd.DataFrame:
    supabase = get_client()
    todos = []
    offset = 0
    while True:
        response = supabase.table("silver_deliveries") \
            .select("order_id, order_date, is_late, delay_days, order_region") \
            .range(offset, offset + 999) \
            .execute()
        if not response.data:
            break
        todos.extend(response.data)
        offset += 1000
    df = pd.DataFrame(todos)
    df["order_date"] = pd.to_datetime(df["order_date"])
    df["period"] = df["order_date"].dt.to_period("M").dt.to_timestamp()
    return df

def render():
    st.title("🔍 Process Mining")
    st.markdown("Investigação dos desvios no fluxo **Order-to-Shipping** — onde os números não batem e por quê.")
    st.markdown("---")

    with st.spinner("Carregando dados..."):
        df = buscar_silver()
        df_events = pd.read_csv(CAMINHO_CSV) if os.path.exists(CAMINHO_CSV) else pd.DataFrame()

    total_criticos = int(df["is_late"].sum())
    total_silver   = len(df)

    # ── FUNIL DE DADOS ────────────────────────────────────────────

    st.subheader("📉 Funil de Dados — Do Bruto ao Crítico")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🥉 Bronze",         f"{TOTAL_BRONZE:,}".replace(",", "."), "Total ingerido")
    col2.metric("🥈 Silver",         f"{TOTAL_SILVER:,}".replace(",", "."),
                f"-{TOTAL_BRONZE - TOTAL_SILVER:,} linhas removidas".replace(",", "."))
    col3.metric("⚠️ Casos Críticos", f"{total_criticos:,}".replace(",", "."),
                f"{round(total_criticos / TOTAL_SILVER * 100, 1)}% do Silver")
    col4.metric("✅ No Prazo",
                f"{TOTAL_SILVER - total_criticos:,}".replace(",", "."),
                f"{round((TOTAL_SILVER - total_criticos) / TOTAL_SILVER * 100, 1)}% do Silver")

    fig_funil = go.Figure(go.Funnel(
        y=["🥉 Bronze (Bruto)", "🥈 Silver (Únicos)", "⚠️ Casos Críticos"],
        x=[TOTAL_BRONZE, TOTAL_SILVER, total_criticos],
        textinfo="value+percent previous",
        marker=dict(color=["#4fc3f7", "#f9a825", "#f4511e"])
    ))
    fig_funil.update_layout(title="Funil de Dados — Rastreabilidade Bronze → Silver → Críticos")
    st.plotly_chart(fig_funil, use_container_width=True)

    # ── NARRATIVA DO FUNIL ────────────────────────────────────────
    reducao_pct = round((1 - TOTAL_SILVER / TOTAL_BRONZE) * 100, 1)

    st.info(f"""
    **📖 O que este funil está dizendo?**

    De **{TOTAL_BRONZE:,}** registros brutos ingeridos, apenas **{TOTAL_SILVER:,}** chegaram à camada Silver — 
    uma redução de **{reducao_pct}%**. Isso pode indicar **duas hipóteses distintas**:
    """.replace(",", "."))

    col_h1, col_h2 = st.columns(2)

    with col_h1:
        st.warning("""
        **📦 Hipótese 1 — Modelo de Negócio**

        O dataset registra uma linha por *item do pedido*, não por *pedido único*.
        Um pedido com 3 produtos gera 3 linhas no Bronze — comportamento esperado
        em sistemas ERP e WMS.

        ✅ **Conclusão:** Não é um problema. É o design do sistema.
        A camada Silver corretamente consolida por `order_id`.
        """)

    with col_h2:
        st.error("""
        **🚨 Hipótese 2 — Problema Estrutural**

        Se o sistema deveria registrar apenas um evento por pedido,
        então temos **duplicidade real de dados** — sintoma de integrações
        mal configuradas, processos manuais duplicados ou falha de governança.

        ⚠️ **Ação recomendada:** Auditoria com equipe de DBAs para validar
        a origem de cada registro e eliminar redundâncias na entrada.
        """)

    st.markdown("""
    > 💡 **Para o cliente:** Independente da hipótese correta, o pipeline já trata
    > este cenário automaticamente. A recomendação é validar com a equipe técnica
    > qual das duas hipóteses se aplica — e documentar como decisão arquitetural.
    """)

    st.markdown("---")

    # ── ATRASOS POR REGIÃO ────────────────────────────────────────
    st.subheader("🗺️ Atrasos por Região")
    st.caption("Percentual de casos críticos sobre o total de pedidos por região.")

    df_reg = df.groupby("order_region").agg(
        total=("order_id", "count"),
        criticos=("is_late", "sum")
    ).reset_index()
    df_reg["pct_atraso"] = round(df_reg["criticos"] / df_reg["total"] * 100, 2)
    df_reg = df_reg.sort_values("pct_atraso", ascending=True)

    fig_reg = px.bar(
        df_reg,
        x="pct_atraso",
        y="order_region",
        orientation="h",
        title="% de Atrasos por Região",
        labels={"pct_atraso": "% Atrasos", "order_region": "Região"},
        color="pct_atraso",
        color_continuous_scale=["green", "yellow", "red"],
        text="pct_atraso"
    )
    fig_reg.update_traces(texttemplate="%{text}%", textposition="outside")
    media = round(df_reg["pct_atraso"].mean(), 1)
    fig_reg.add_vline(
        x=df_reg["pct_atraso"].mean(),
        line_dash="dash",
        line_color="white",
        line_width=2,
        annotation=dict(
            text=f"<b>Média: {media}%</b>",
            font=dict(size=13, color="white"),
            bgcolor="rgba(0,0,0,0.6)",
            bordercolor="white",
            borderwidth=1,
            borderpad=6,
            yref="paper",
            y=1.12
        )
    )
    st.plotly_chart(fig_reg, use_container_width=True)

    st.markdown("---")

    # ── EVOLUÇÃO MENSAL ───────────────────────────────────────────
    st.subheader("📅 Evolução Mensal — Críticos vs Total")
    st.caption("Comparação mês a mês entre total de pedidos e casos críticos de atraso.")

    df_mensal = df.groupby("period").agg(
        total=("order_id", "count"),
        criticos=("is_late", "sum")
    ).reset_index()
    df_mensal["no_prazo"] = df_mensal["total"] - df_mensal["criticos"]

    fig_mensal = go.Figure()
    fig_mensal.add_trace(go.Bar(
        x=df_mensal["period"], y=df_mensal["no_prazo"],
        name="No Prazo", marker_color="#69f0ae"
    ))
    fig_mensal.add_trace(go.Bar(
        x=df_mensal["period"], y=df_mensal["criticos"],
        name="Críticos (Atraso)", marker_color="#f4511e"
    ))
    fig_mensal.update_layout(
        barmode="stack",
        title="Pedidos Mensais — No Prazo vs Críticos",
        xaxis_title="Período",
        yaxis_title="Quantidade"
    )
    st.plotly_chart(fig_mensal, use_container_width=True)

    st.markdown("---")

    # ── LEAD TIME REAL vs PLANEJADO ───────────────────────────────
    st.subheader("⏱️ Lead Time — Real vs Planejado")
    st.caption("Desvio médio entre o tempo planejado e o realizado por região.")

    df_silver_full = buscar_silver_completo()

    if not df_silver_full.empty:
        df_lead = df_silver_full.groupby("order_region").agg(
            desvio_medio=("delay_days", "mean"),
            desvio_max=("delay_days", "max"),
            desvio_min=("delay_days", "min")
        ).reset_index()
        df_lead["desvio_medio"] = df_lead["desvio_medio"].round(2)
        df_lead = df_lead.sort_values("desvio_medio", ascending=False)

        fig_lead = px.bar(
            df_lead,
            x="order_region",
            y="desvio_medio",
            title="Desvio Médio do Lead Time por Região (dias)",
            labels={"order_region": "Região", "desvio_medio": "Desvio Médio (dias)"},
            color="desvio_medio",
            color_continuous_scale=["green", "yellow", "red"],
            text="desvio_medio"
        )
        fig_lead.add_hline(y=0, line_dash="dash", line_color="white", annotation_text="Sem desvio")
        fig_lead.update_traces(texttemplate="%{text} dias", textposition="outside")
        st.plotly_chart(fig_lead, use_container_width=True)

    st.markdown("---")

    # ── DOWNLOADS ─────────────────────────────────────────────────
    st.subheader("📥 Evidências para o Business Case")
    col_csv, col_json, col_png = st.columns(3)

    with col_csv:
        if os.path.exists(CAMINHO_CSV):
            with open(CAMINHO_CSV, "rb") as f:
                st.download_button("📄 Event Log CSV", f,
                    file_name="process_events_delay_analysis.csv", mime="text/csv")

    with col_json:
        if os.path.exists(CAMINHO_JSON):
            with open(CAMINHO_JSON, "rb") as f:
                st.download_button("📋 Event Log JSON", f,
                    file_name="process_events_delay_analysis.json", mime="application/json")

    with col_png:
        if os.path.exists(CAMINHO_PNG):
            with open(CAMINHO_PNG, "rb") as f:
                st.download_button("🗺️ Mapa PNG", f,
                    file_name="process_map_delay_analysis.png", mime="image/png")

def buscar_silver_completo() -> pd.DataFrame:
    supabase = get_client()
    todos = []
    offset = 0
    while True:
        response = supabase.table("silver_deliveries") \
            .select("order_region, delay_days") \
            .range(offset, offset + 999) \
            .execute()
        if not response.data:
            break
        todos.extend(response.data)
        offset += 1000
    return pd.DataFrame(todos)