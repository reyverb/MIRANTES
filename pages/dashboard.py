"""
Dashboard MIRANTES - Versão com Banco de Dados Supabase

Este arquivo pode ser usado como página alternativa de dashboard.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from utils.database import carregar_historico, get_resumo_descargas

st.set_page_config(page_title="Dashboard - MIRANTES", page_icon="📈", layout="wide")
st.title("📈 Dashboard de Descargas")

try:
    df = carregar_historico()
    if df.empty:
        st.warning("Nenhuma descarga registrada.")
    else:
        datas = pd.to_datetime(df['data'])
        col1, col2 = st.columns(2)
        with col1:
            periodo = st.date_input("Período", value=(datas.min().date(), datas.max().date()))
        with col2:
            produtos = sorted(df['produto'].dropna().unique())
            produtos_filtro = st.multiselect("Produtos", options=produtos, default=produtos)

        df_filtrado = df.copy()
        if len(periodo) == 2:
            df_filtrado = df_filtrado[(pd.to_datetime(df_filtrado['data']) >= pd.Timestamp(periodo[0])) & (pd.to_datetime(df_filtrado['data']) <= pd.Timestamp(periodo[1]))]
        if produtos_filtro:
            df_filtrado = df_filtrado[df_filtrado['produto'].isin(produtos_filtro)]

        if not df_filtrado.empty:
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Descargas", len(df_filtrado))
            m2.metric("Volume total", f"{df_filtrado['volume'].sum():,.2f}")
            m3.metric("Volume médio", f"{df_filtrado['volume'].mean():,.2f}")
            m4.metric("Produtos", df_filtrado['produto'].nunique())

            col1, col2 = st.columns(2)
            with col1:
                vol = df_filtrado.groupby('produto', as_index=False)['volume'].sum()
                st.plotly_chart(px.bar(vol, x='produto', y='volume', title='Volume por produto'), use_container_width=True)
            with col2:
                evol = df_filtrado.groupby('data', as_index=False)['volume'].sum().sort_values('data')
                st.plotly_chart(px.line(evol, x='data', y='volume', markers=True, title='Evolução'), use_container_width=True)

            csv = df_filtrado.to_csv(index=False, sep=';', decimal=',')
            st.download_button("📥 Baixar CSV", csv, f"dashboard_{datetime.now():%Y%m%d_%H%M%S}.csv", "text/csv")
except Exception as e:
    st.error(f"Erro: {e}")

st.caption("Dashboard MIRANTES © 2026")
