import streamlit as st

st.set_page_config(
    page_title="Delivery Intelligence Pipeline",
    page_icon="🚚",
    layout="wide"
)

st.sidebar.title("🚚 Delivery Intelligence")
st.sidebar.markdown("---")

pagina = st.sidebar.radio(
    "Navegação",
    [
        "📊 Visão Geral",
        "🗺️ OTD por Região",
        "📈 Sigma e DPMO",
        "📥 Injeção de Dados"
    ]
)

st.sidebar.markdown("---")
st.sidebar.caption("delivery-intelligence-pipeline v1.0")

if pagina == "📊 Visão Geral":
    from pages import visao_geral
    visao_geral.render()
elif pagina == "🗺️ OTD por Região":
    from pages import otd_regiao
    otd_regiao.render()
elif pagina == "📈 Sigma e DPMO":
    from pages import sigma_dpmo
    sigma_dpmo.render()
elif pagina == "📥 Injeção de Dados":
    from pages import injecao_dados
    injecao_dados.render()