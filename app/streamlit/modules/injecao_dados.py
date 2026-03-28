import streamlit as st
import pandas as pd
from datetime import date
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from db import get_client

COLUNAS_CSV = {
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

def inserir_bronze(registros: list, source: str):
    supabase = get_client()
    supabase.table("bronze_deliveries").insert(registros).execute()
    st.success(f"✅ {len(registros)} registro(s) inserido(s) com sucesso na camada Bronze!")

def render():
    st.title("📥 Injeção de Dados")
    st.markdown("Adicione novos registros via upload de arquivo ou formulário manual.")
    st.markdown("---")

    aba_upload, aba_form = st.tabs(["📂 Upload CSV/Excel", "✏️ Formulário Manual"])

    # ── ABA UPLOAD ────────────────────────────────────────────────
    with aba_upload:
        st.subheader("Upload de arquivo")
        st.caption("O arquivo deve seguir o mesmo formato do DataCo Supply Chain.")

        # Downloads de template
        col_csv, col_xlsx, _ = st.columns([1, 1, 4])

        with col_csv:
            with open("data/template_injecao.csv", "rb") as f:
                st.download_button(
                    label="📥 Template CSV",
                    data=f,
                    file_name="template_injecao.csv",
                    mime="text/csv"
                )

        with col_xlsx:
            with open("data/template_injecao.xlsx", "rb") as f:
                st.download_button(
                    label="📥 Template Excel",
                    data=f,
                    file_name="template_injecao.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        arquivo = st.file_uploader(
            "Selecione o arquivo",
            type=["csv", "xlsx"]
        )

        if arquivo:
            try:
                if arquivo.name.endswith(".csv"):
                    df = pd.read_csv(arquivo, encoding="latin1")
                else:
                    df = pd.read_excel(arquivo)

                # Verificar colunas obrigatórias
                colunas_faltando = [c for c in COLUNAS_CSV.keys() if c not in df.columns]

                if colunas_faltando:
                    st.error(f"Colunas ausentes no arquivo: {colunas_faltando}")
                    return

                df = df[list(COLUNAS_CSV.keys())].rename(columns=COLUNAS_CSV)
                df["order_date"] = pd.to_datetime(df["order_date"]).dt.strftime("%Y-%m-%d")
                df["ship_date"]  = pd.to_datetime(df["ship_date"]).dt.strftime("%Y-%m-%d")
                df["damage_flag"] = False
                df["return_flag"] = False
                df["source"]      = "csv_upload"
                df = df.dropna(subset=["order_id", "order_date", "delivery_status"])

                st.info(f"**{len(df)} registros** encontrados no arquivo.")
                st.dataframe(df.head(5), use_container_width=True, hide_index=True)

                if st.button("⬆️ Enviar para o Bronze", type="primary"):
                    with st.spinner("Inserindo registros..."):
                        lotes = [
                            df.iloc[i:i+500].to_dict(orient="records")
                            for i in range(0, len(df), 500)
                        ]
                        for lote in lotes:
                            inserir_bronze(lote, "csv_upload")

            except Exception as e:
                st.error(f"Erro ao processar arquivo: {e}")

    # ── ABA FORMULÁRIO ────────────────────────────────────────────
    with aba_form:
        st.subheader("Registro manual")
        st.caption("Insira um novo pedido diretamente pelo formulário.")

        col1, col2 = st.columns(2)

        with col1:
            order_id       = st.number_input("Order ID",          min_value=1, step=1)
            order_date     = st.date_input("Data do Pedido",      value=date.today())
            ship_date      = st.date_input("Data de Envio",       value=date.today())
            days_scheduled = st.number_input("Dias Planejados",   min_value=1, step=1)
            days_real      = st.number_input("Dias Reais",        min_value=1, step=1)

        with col2:
            delivery_status = st.selectbox(
                "Status da Entrega",
                ["Late delivery", "Advance shipping", "Shipping on time", "Shipping canceled"]
            )
            late_risk    = st.selectbox("Risco de Atraso", [0, 1])
            order_region = st.text_input("Região", placeholder="Ex: OCEANIA")
            order_country= st.text_input("País",   placeholder="Ex: Australia")
            category     = st.text_input("Categoria", placeholder="Ex: Electronics")
            damage_flag  = st.checkbox("Avaria registrada")
            return_flag  = st.checkbox("Devolução registrada")

        st.markdown("---")

        if st.button("💾 Salvar Registro", type="primary"):
            if not order_region or not order_country or not category:
                st.warning("Preencha todos os campos obrigatórios.")
            else:
                registro = [{
                    "order_id"          : int(order_id),
                    "order_date"        : order_date.strftime("%Y-%m-%d"),
                    "ship_date"         : ship_date.strftime("%Y-%m-%d"),
                    "days_scheduled"    : int(days_scheduled),
                    "days_real"         : int(days_real),
                    "delivery_status"   : delivery_status,
                    "late_delivery_risk": int(late_risk),
                    "order_region"      : order_region.strip().upper(),
                    "order_country"     : order_country.strip(),
                    "category_name"     : category.strip(),
                    "damage_flag"       : damage_flag,
                    "return_flag"       : return_flag,
                    "source"            : "form"
                }]

                with st.spinner("Salvando..."):
                    inserir_bronze(registro, "form")