"""
App MIRANTES - Versão com Banco de Dados Supabase

Este app registra descargas de produtos e armazena permanentemente no Supabase.
Os dados não serão perdidos ao reiniciar o app.
"""

import streamlit as st
from datetime import datetime, date
import pandas as pd
import plotly.express as px

from utils.database import salvar_descarga, carregar_historico, deletar_descarga, get_resumo_descargas

# Configuração da página
st.set_page_config(
    page_title="MIRANTES - Registro de Descargas",
    page_icon="📊",
    layout="wide"
)

# Título
st.title("📊 MIRANTES - Sistema de Registro de Descargas")

# Sidebar para navegação
st.sidebar.title("Navegação")
menu = st.sidebar.radio(
    "Escolha a página:",
    ["📝 Registrar Descarga", "📈 Dashboard", "📋 Histórico Completo"]
)

# ============================================
# PÁGINA: REGISTRAR DESCARGA
# ============================================
if menu == "📝 Registrar Descarga":
    st.header("📝 Nova Descarga")
    st.write("Preencha os dados abaixo para registrar uma nova descarga.")
    
    # Formulário de cadastro
    with st.form("form_descarga", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            data_descarga = st.date_input(
                "📅 Data da Descarga",
                value=date.today()
            )
            
            produto = st.text_input(
                "📦 Produto",
                placeholder="Ex: Milho, Soja, Trigo..."
            )
        
        with col2:
            volume = st.number_input(
                "🔢 Volume (unidade)",
                min_value=0.0,
                step=0.1,
                format="%.2f"
            )
            
            observacoes = st.text_area(
                "📝 Observações",
                placeholder="Informações adicionais (opcional)",
                height=100
            )
        
        botao_salvar = st.form_submit_button("💾 Salvar Descarga", type="primary")
    
    # Processar salvamento
    if botao_salvar:
        # Validações
        erros = []
        
        if not produto.strip():
            erros.append("Produto é obrigatório")
        
        if volume <= 0:
            erros.append("Volume deve ser maior que zero")
        
        if erros:
            for erro in erros:
                st.error(f"❌ {erro}")
        else:
            try:
                # Salvar no banco de dados
                dados_salvos = salvar_descarga(
                    data=datetime.combine(data_descarga, datetime.min.time()),
                    volume=volume,
                    produto=produto.strip(),
                    observacoes=observacoes.strip() if observacoes else None
                )
                
                st.success(f"✅ Descarga salva com sucesso! ID: {dados_salvos.get('id')}")
                st.balloons()
                
                # Mostrar resumo
                st.info(f"""
                **Dados salvos:**
                - Data: {data_descarga.strftime('%d/%m/%Y')}
                - Produto: {produto}
                - Volume: {volume:.2f}
                - Observações: {observacoes if observacoes else 'Nenhuma'}
                """)
                
            except Exception as e:
                st.error(f"❌ Erro ao salvar: {str(e)}")
                st.warning("Verifique se as credenciais do Supabase estão configuradas corretamente.")
    
    # Dicas
    with st.expander("💡 Dicas"):
        st.write("""
        - Os dados são salvos permanentemente no banco de dados
        - Você pode editar ou excluir registros na página 'Histórico Completo'
        - Use nomes padronizados para os produtos para facilitar a busca
        """)

# ============================================
# PÁGINA: DASHBOARD
# ============================================
elif menu == "📈 Dashboard":
    st.header("📈 Dashboard de Descargas")
    
    # Carregar dados do banco
    try:
        df = carregar_historico()
        
        if df.empty:
            st.warning("⚠️ Nenhuma descarga registrada ainda.")
            st.info("Vá para '📝 Registrar Descarga' para adicionar dados.")
        else:
            # Filtros
            st.subheader("🔍 Filtros")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Filtro por data
                datas = pd.to_datetime(df['data'])
                data_min = datas.min().date()
                data_max = datas.max().date()
                filtro_data = st.date_input(
                    "Período",
                    value=(data_min, data_max)
                )
            
            with col2:
                # Filtro por produto
                produtos = sorted(df['produto'].unique())
                filtro_produto = st.multiselect(
                    "Produto(s)",
                    options=produtos,
                    default=produtos
                )
            
            with col3:
                # Botão de atualizar
                st.write(" ")
                st.write(" ")
                if st.button("🔄 Atualizar"):
                    st.rerun()
            
            # Aplicar filtros
            df_filtrado = df.copy()
            
            if filtro_data:
                if isinstance(filtro_data, tuple):
                    df_filtrado = df_filtrado[
                        (pd.to_datetime(df_filtrado['data']) >= pd.to_datetime(filtro_data[0])) &
                        (pd.to_datetime(df_filtrado['data']) <= pd.to_datetime(filtro_data[1]))
                    ]
            
            if filtro_produto:
                df_filtrado = df_filtrado[df_filtrado['produto'].isin(filtro_produto)]
            
            # Métricas
            if not df_filtrado.empty:
                st.subheader("📊 Métricas")
                
                total_descargas = len(df_filtrado)
                volume_total = df_filtrado['volume'].sum()
                volume_medio = df_filtrado['volume'].mean()
                produtos_unicos = df_filtrado['produto'].nunique()
                
                col1, col2, col3, col4 = st.columns(4)
                
                col1.metric("📝 Total Descargas", total_descargas)
                col2.metric("📦 Volume Total", f"{volume_total:,.2f}")
                col3.metric("📊 Volume Médio", f"{volume_medio:,.2f}")
                col4.metric("🏷️ Produtos", produtos_unicos)
                
                # Gráficos
                st.divider()
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Volume por produto
                    st.subheader("📦 Volume por Produto")
                    vol_por_produto = df_filtrado.groupby('produto')['volume'].sum().reset_index()
                    fig_bar = px.bar(
                        vol_por_produto,
                        x='produto',
                        y='volume',
                        title='Volume Total por Produto',
                        labels={'produto': 'Produto', 'volume': 'Volume'},
                        color='volume',
                        color_continuous_scale='Blues'
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)
                
                with col2:
                    # Descargas ao longo do tempo
                    st.subheader("📅 Descargas por Data")
                    df_filtrado['data_dt'] = pd.to_datetime(df_filtrado['data'])
                    descargas_por_data = df_filtrado.groupby('data')['volume'].sum().reset_index()
                    fig_line = px.line(
                        descargas_por_data.sort_values('data'),
                        x='data',
                        y='volume',
                        title='Evolução das Descargas',
                        labels={'data': 'Data', 'volume': 'Volume'},
                        markers=True
                    )
                    st.plotly_chart(fig_line, use_container_width=True)
                
                # Top produtos
                st.divider()
                st.subheader("🏆 Top 5 Produtos por Volume")
                top_produtos = df_filtrado.groupby('produto')['volume'].sum().nlargest(5).reset_index()
                st.dataframe(
                    top_produtos,
                    column_config={"produto": "Produto", "volume": "Volume Total"},
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.warning("⚠️ Nenhum dado encontrado com os filtros selecionados.")
    
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados: {str(e)}")
        st.warning("Verifique se:")
        st.write("""
        1. O banco de dados está configurado (veja CONFIGURACAO_SUPABASE.md)
        2. A tabela 'descargas' foi criada no Supabase
        3. As credenciais estão corretas
        """)

# ============================================
# PÁGINA: HISTÓRICO COMPLETO
# ============================================
elif menu == "📋 Histórico Completo":
    st.header("📋 Histórico de Descargas")
    st.write("Visualize e gerencie todos os registros de descargas.")
    
    # Carregar dados
    try:
        df = carregar_historico()
        
        if df.empty:
            st.warning("⚠️ Nenhuma descarga registrada.")
        else:
            # Filtros
            st.subheader("🔍 Filtros")
            col1, col2 = st.columns(2)
            
            with col1:
                filtro_produto = st.selectbox(
                    "Filtrar por Produto",
                    options=["Todos"] + sorted(df['produto'].unique())
                )
            
            with col2:
                busca = st.text_input(
                    "🔎 Buscar (produto ou observação)",
                    placeholder="Digite para buscar..."
                )
            
            # Aplicar filtros
            df_filtrado = df.copy()
            
            if filtro_produto != "Todos":
                df_filtrado = df_filtrado[df_filtrado['produto'] == filtro_produto]
            
            if busca:
                df_filtrado = df_filtrado[
                    df_filtrado['produto'].str.contains(busca, case=False, na=False) |
                    df_filtrado['observacoes'].str.contains(busca, case=False, na=False)
                ]
            
            # Exibir tabela
            st.subheader(f"📊 Registros ({len(df_filtrado)} encontrados)")
            
            # Formatar data
            df_exibir = df_filtrado.copy()
            df_exibir['data'] = pd.to_datetime(df_exibir['data']).dt.strftime('%d/%m/%Y')
            
            # Selecionar colunas
            colunas_exibir = ['id', 'data', 'produto', 'volume', 'observacoes', 'created_at']
            df_exibir = df_exibir[colunas_exibir]
            
            st.dataframe(
                df_exibir,
                column_config={
                    "id": "ID",
                    "data": "Data",
                    "produto": "Produto",
                    "volume": st.dataframe.ColumnConfig(
                        "Volume",
                        type="number",
                        format="%.2f"
                    ),
                    "observacoes": "Observações",
                    "created_at": "Criado em"
                },
                use_container_width=True,
                hide_index=True
            )
            
            # Opção de excluir
            if not df_filtrado.empty:
                st.divider()
                st.subheader("🗑️ Excluir Registro")
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    id_excluir = st.number_input(
                        "ID do registro para excluir",
                        min_value=1,
                        step=1,
                        value=1
                    )
                
                with col2:
                    st.write(" ")
                    st.write(" ")
                    if st.button("🗑️ Excluir", type="secondary"):
                        try:
                            if deletar_descarga(int(id_excluir)):
                                st.success(f"✅ Registro {id_excluir} excluído com sucesso!")
                                st.rerun()
                            else:
                                st.error(f"❌ Registro {id_excluir} não encontrado.")
                        except Exception as e:
                            st.error(f"❌ Erro ao excluir: {str(e)}")
            
            # Exportar dados
            st.divider()
            st.subheader("💾 Exportar Dados")
            
            csv = df_filtrado.to_csv(index=False, sep=';', decimal=',')
            st.download_button(
                label="📥 Baixar CSV",
                data=csv,
                file_name=f"descargas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados: {str(e)}")
        st.warning("Verifique a configuração do Supabase (veja CONFIGURACAO_SUPABASE.md)")

# Footer
st.divider()
st.caption("""
MIRANTES © 2026 - Sistema de Registro de Descargas | 
Dados armazenados permanentemente no Supabase
""")
