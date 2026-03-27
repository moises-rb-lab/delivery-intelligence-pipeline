import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from db import get_client

def buscar_gold_sigma() -> pd.DataFrame:
    supabase = get_client()
    response = supabase.table("gold_sigma").select("*").execute()
    return pd.DataFrame(response.data)

def classificar_sigma(sigma: float) -> str:
    if sigma >= 6.0: return "🏆 Classe Mundial"
    if sigma >= 5.0: return "✅ Excelente"
    if sigma >= 4.0: return "👍 Bom"
    if sigma >= 3.0: return "⚠️ Atenção"
    return "🔴 Crítico"

def render():
    st.title("📈 Sigma e DPMO")
    st.markdown("Análise do nível de qualidade do processo logístico.")
    st.markdown("---")

    with st.spinner("Carregando dados..."):
        df = buscar_gold_sigma()

    if df.empty:
        st.warning("Nenhum dado disponível ainda.")
        return

    df["period"] = pd.to_datetime(df["period"])
    df = df.sort_values("period")

    # ── KPIs do período mais recente ──────────────────────────────
    ultimo = df.iloc[-1]
    primeiro = df.iloc[0]

    delta_sigma = round(float(ultimo["sigma_level"]) - float(primeiro["sigma_level"]), 2)
    delta_dpmo  = round(float(ultimo["dpmo"]) - float(primeiro["dpmo"]), 0)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        "Nível Sigma Atual",
        f"{ultimo['sigma_level']}σ",
        delta=f"{delta_sigma:+.2f}σ vs início"
    )
    col2.metric(
        "DPMO Atual",
        f"{ultimo['dpmo']:,.0f}".replace(",", "."),
        delta=f"{delta_dpmo:+,.0f} vs início".replace(",", "."),
        delta_color="inverse"
    )
    col3.metric(
        "Total de Defeitos",
        f"{int(df['total_defects'].sum()):,}".replace(",", ".")
    )
    col4.metric(
        "Classificação",
        classificar_sigma(float(ultimo["sigma_level"]))
    )

    st.markdown("---")

    # ── Referência Sigma ──────────────────────────────────────────
    with st.expander("📖 Tabela de Referência Six Sigma"):
        ref = pd.DataFrame({
            "Nível Sigma": ["2σ", "3σ", "4σ", "5σ", "6σ"],
            "DPMO"       : ["308.537", "66.807", "6.210", "233", "3,4"],
            "Qualidade"  : ["69,1%", "93,3%", "99,4%", "99,98%", "99,9997%"],
            "Classificação": ["Crítico", "Atenção", "Bom", "Excelente", "Classe Mundial"]
        })
        st.dataframe(ref, use_container_width=True, hide_index=True)

    # ── Evolução do Nível Sigma ───────────────────────────────────
    fig_sigma = px.line(
        df,
        x="period",
        y="sigma_level",
        title="Evolução do Nível Sigma",
        labels={"period": "Período", "sigma_level": "Nível Sigma"},
        markers=True
    )
    fig_sigma.add_hline(y=4.0, line_dash="dash", line_color="green",
                        annotation_text="Meta 4σ")
    fig_sigma.add_hline(y=3.0, line_dash="dash", line_color="orange",
                        annotation_text="Atenção 3σ")
    fig_sigma.update_traces(line_color="#4fc3f7")
    st.plotly_chart(fig_sigma, use_container_width=True)

    # ── Evolução do DPMO ──────────────────────────────────────────
    fig_dpmo = px.bar(
        df,
        x="period",
        y="dpmo",
        title="DPMO Mensal",
        labels={"period": "Período", "dpmo": "DPMO"},
        color="dpmo",
        color_continuous_scale=["green", "yellow", "red"]
    )
    fig_dpmo.add_hline(y=6210, line_dash="dash", line_color="green",
                       annotation_text="Meta 4σ (6.210 DPMO)")
    st.plotly_chart(fig_dpmo, use_container_width=True)

    # ── Tabela detalhada ──────────────────────────────────────────
    st.subheader("Detalhamento Mensal")
    st.dataframe(
        df[["period", "total_opportunities", "total_defects", "dpmo", "sigma_level"]]
        .rename(columns={
            "period"              : "Período",
            "total_opportunities" : "Oportunidades",
            "total_defects"       : "Defeitos",
            "dpmo"                : "DPMO",
            "sigma_level"         : "Nível Sigma"
        }),
        use_container_width=True,
        hide_index=True
    )