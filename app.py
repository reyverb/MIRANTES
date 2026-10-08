"""
App MIRANTES - Versão com Banco de Dados Supabase

Este app registra descargas de produtos e armazena permanentemente no Supabase.
Os dados não serão perdidos ao reiniciar o app.
"""

import streamlit as st
from datetime import datetime, date
import pandas as pd
import plotly.express as px

from utils.database import salvar_descarga, carregar_historico, deletar_descarga

st.set_page_config(page_title="MIRANTES - Registro de Descargas", page_icon="📊", layout="wide")
st.title("📊 MIRANTES - Sistema de Registro de Descargas")

st.sidebar.title("Navegação")
menu = st.sidebar.radio("Escolha a página:", ["📝 Registrar Descarga", "📈 Dashboard", "📋 Histórico Completo"])

if menu == "📝 Registrar Descarga":
    st.header("📝 Nova Descarga")
    with st.form("form_descarga", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            data_descarga = st.date_input("📅 Data da Descarga", value=date.today())
            produto = st.text_input("📦 Produto", placeholder="Ex: Milho, Soja, Trigo...")
        with col2:
            volume = st.number_input("🔢 Volume (unidade)", min_value=0.0, step=0.1, format="%.2f")
            observacoes = st.text_area("📝 Observações", placeholder="Informações adicionais (opcional)", height=100)
        botao_salvar = st.form_submit_button("💾 Salvar Descarga", type="primary")

    if botao_salvar:
        if not produto.strip():
            st.error("❌ Produto é obrigatório")
        elif volume <= 0:
            st.error("❌ Volume deve ser maior que zero")
        else:
            try:
                dados_salvos = salvar_descarga(
                    data=datetime.combine(data_descarga, datetime.min.time()),
                    volume=volume,
                    produto=produto.strip(),
                    observacoes=observacoes.strip() if observacoes else None,
                )
                st.success(f"✅ Descarga salva com sucesso! ID: {dados_salvos.get('id')}")
            except Exception as e:
                st.error(f"❌ Erro ao salvar: {e}")
                st.info("Configure as credenciais do Supabase antes de usar o formulário.")

elif menu == "📈 Dashboard":
    st.header("📈 Dashboard de Descargas")
    try:
        df = carregar_historico()
        if df.empty:
            st.info("Nenhuma descarga registrada ainda.")
        else:
            datas = pd.to_datetime(df["data"])
            col1, col2 = st.columns(2)
            with col1:
                periodo = st.date_input("Período", value=(datas.min().date(), datas.max().date()))
            with col2:
                produtos = sorted(df["produto"].dropna().unique())
                produtos_selecionados = st.multiselect("Produtos", produtos, default=produtos)

            filtrado = df.copy()
            if len(periodo) == 2:
                filtrado = filtrado[(pd.to_datetime(filtrado["data"]) >= pd.Timestamp(periodo[0])) & (pd.to_datetime(filtrado["data"]) <= pd.Timestamp(periodo[1]))]
            if produtos_selecionados:
                filtrado = filtrado[filtrado["produto"].isin(produtos_selecionados)]

            if filtrado.empty:
                st.warning("Nenhum registro corresponde aos filtros.")
            else:
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Descargas", len(filtrado))
                m2.metric("Volume total", f"{filtrado['volume'].sum():,.2f}")
                m3.metric("Volume médio", f"{filtrado['volume'].mean():,.2f}")
                m4.metric("Produtos", filtrado["produto"].nunique())

                col1, col2 = st.columns(2)
                with col1:
                    por_produto = filtrado.groupby("produto", as_index=False)["volume"].sum()
                    st.plotly_chart(px.bar(por_produto, x="produto", y="volume", title="Volume por produto"), use_container_width=True)
                with col2:
                    por_data = filtrado.groupby("data", as_index=False)["volume"].sum().sort_values("data")
                    st.plotly_chart(px.line(por_data, x="data", y="volume", markers=True, title="Evolução das descargas"), use_container_width=True)
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados: {e}")

else:
    st.header("📋 Histórico de Descargas")
    try:
        df = carregar_historico()
        if df.empty:
            st.info("Nenhuma descarga registrada.")
        else:
            df_exibir = df.copy()
            df_exibir["data"] = pd.to_datetime(df_exibir["data"]).dt.strftime("%d/%m/%Y")
            st.dataframe(df_exibir, use_container_width=True, hide_index=True)

            csv = df.to_csv(index=False, sep=";", decimal=",")
            st.download_button("📥 Baixar CSV", csv, f"descargas_{datetime.now():%Y%m%d_%H%M%S}.csv", "text/csv")

            with st.expander("🗑️ Excluir registro"):
                id_excluir = st.number_input("ID do registro", min_value=1, step=1)
                if st.button("Excluir registro", type="secondary"):
                    if deletar_descarga(int(id_excluir)):
                        st.success("✅ Registro excluído.")
                        st.rerun()
                    st.error("❌ Registro não encontrado ou não pôde ser excluído.")
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados: {e}")

st.divider()
st.caption("MIRANTES © 2026 | Dados armazenados no Supabase")
