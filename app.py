import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from PIL import Image

logo = Image.open("image_2d6b5c.png")
st.set_page_config(page_title="NAVIMAR PESCADOS", layout="centered", page_icon=logo)

# --- IDENTIDADE VISUAL E CORES AQUÁTICAS ---
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] {
        background-color: #EAF4F4; 
    }
    [data-testid="stSidebar"] {
        background-color: #031523; 
    }
    h1, h2, h3, h4 {
        color: #031523 !important; 
    }
    p, label, span {
        color: #031523 !important;
    }
    .stButton>button {
        background-color: #E4D9C3; 
        color: #031523;
        border-radius: 5px;
        font-weight: bold;
        border: 2px solid #031523;
    }
    .stButton>button:hover {
        background-color: #031523;
        color: #E4D9C3;
        border: 2px solid #E4D9C3;
    }
    /* Estilo para Tabela do Romaneio */
    [data-testid="stDataFrame"] {
        border: 2px solid #031523;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Conexão com o banco compartilhado
@st.cache_resource
def get_db():
    conn = sqlite3.connect("porto_atum.db", check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

conn = get_db()

st.page_link("app.py", label="Voltar para a Pesagem no Cais", icon="🐟")

st.title("📊 Painel Gerencial & Romaneio")

descargas = pd.read_sql("SELECT id, barco, proprietario, data_hora, status FROM descargas ORDER BY id DESC", conn)

if descargas.empty:
    st.info("Nenhuma descarga encontrada no banco de dados.")
    st.stop()

opcoes = {
    row["id"]: f"Lote #{row['id']} - {row['barco']} ({row['status']}) | {row['data_hora'][:10]}"
    for _, row in descargas.iterrows()
}

lote_selecionado = st.selectbox(
    "Selecione o Lote / Embarcação:",
    options=list(opcoes.keys()),
    format_func=lambda x: opcoes[x]
)

# Consulta incluindo a nova coluna LOMBO e renomeando categoria para 'peso'
try:
    query_analitica = """
    SELECT 
        d.id AS id_lote,
        d.barco,
        d.proprietario AS armador,
        p.numero_peca,
        p.peso_kg,
        p.categoria AS peso,
        CASE WHEN p.peso_kg >= 40.0 THEN 1 ELSE 0 END AS is_exportacao,
        CASE WHEN p.segundo_furo = 1 THEN 'Sim' ELSE 'Não' END AS segundo_furo,
        CASE WHEN p.lombo = 1 THEN 'Sim' ELSE 'Não' END AS lombo,
        p.destino,
        p.data_registro AS data_hora
    FROM pecas p
    JOIN descargas d ON d.id = p.id_descarga
    WHERE p.id_descarga = ?
    ORDER BY p.numero_peca ASC
    """
    df = pd.read_sql(query_analitica, conn, params=(int(lote_selecionado),))
except:
    # Fallback caso a tabela 'pecas' ainda não tenha a coluna 'lombo' por algum motivo
    query_analitica_fallback = """
    SELECT 
        d.id AS id_lote,
        d.barco,
        d.proprietario AS armador,
        p.numero_peca,
        p.peso_kg,
        p.categoria AS peso,
        CASE WHEN p.peso_kg >= 40.0 THEN 1 ELSE 0 END AS is_exportacao,
        CASE WHEN p.segundo_furo = 1 THEN 'Sim' ELSE 'Não' END AS segundo_furo,
        'Não' AS lombo,
        p.destino,
        p.data_registro AS data_hora
    FROM pecas p
    JOIN descargas d ON d.id = p.id_descarga
    WHERE p.id_descarga = ?
    ORDER BY p.numero_peca ASC
    """
    df = pd.read_sql(query_analitica_fallback, conn, params=(int(lote_selecionado),))

if df.empty:
    st.warning("Este lote não possui peças registradas ainda.")
    st.stop()

# --- ABAS PARA SEPARAR VISÃO GERAL DO ROMANEIO (NOVO DASHBOARD) ---
tab_gerencial, tab_romaneio = st.tabs(["📊 Visão Geral", "📄 Romaneio Oficial"])

with tab_gerencial:
    barco_nome = df["barco"].iloc[0]
    armador_nome = df["armador"].iloc[0]
    total_kg = df["peso_kg"].sum()
    total_pecas = len(df)
    peso_medio = df["peso_kg"].mean()
    peso_export = df[df["is_exportacao"] == 1]["peso_kg"].sum()
    perc_export = (peso_export / total_kg) * 100 if total_kg > 0 else 0
    qtd_furo = (df["segundo_furo"] == "Sim").sum()
    perc_furo = (qtd_furo / total_pecas) * 100 if total_pecas > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Peso Total", f"{total_kg:,.1f} kg")
    c2.metric("Total de Peças", f"{total_pecas}")
    c3.metric("Peso Médio / Peça", f"{peso_medio:.2f} kg")
    c4.metric("% Exportação (40+kg)", f"{perc_export:.1f}%", f"{perc_furo:.1f}% 2º furo", delta_color="inverse")

    st.divider()

    col_graf, col_tab = st.columns([1, 1])

    # Utilizando "peso" em vez de "calibre"
    resumo_peso = df.groupby("peso").agg(
        Pecas=("numero_peca", "count"),
        Peso_Total_Kg=("peso_kg", "sum"),
        Peso_Medio_Kg=("peso_kg", "mean"),
        Com_2_Furo=("segundo_furo", lambda x: (x == "Sim").sum()),
        Com_Lombo=("lombo", lambda x: (x == "Sim").sum())
    ).reset_index()
    resumo_peso["Part_%"] = (resumo_peso["Peso_Total_Kg"] / total_kg) * 100

    with col_graf:
        st.subheader("Volume por Peso (Kg)")
        peso_dist = df.groupby("peso")["peso_kg"].sum().reset_index()
        st.bar_chart(peso_dist.set_index("peso"), use_container_width=True)

    with col_tab:
        st.subheader("Quadro Sintético de Fechamento")
        st.dataframe(
            resumo_peso,
            column_config={
                "Peso_Total_Kg": st.column_config.NumberColumn(format="%.2f kg"),
                "Peso_Medio_Kg": st.column_config.NumberColumn(format="%.2f kg"),
                "Part_%": st.column_config.NumberColumn(format="%.1f%%")
            },
            hide_index=True,
            use_container_width=True
        )

with tab_romaneio:
    st.subheader("Romaneio de Descarga")
    
    # Cabeçalho com Logo e Informações
    col_img, col_info = st.columns([1, 3])
    with col_img:
        try:
            st.image("image_2d6b5c.png", width=180)
        except:
            st.markdown("### NAVIMAR PESCADOS")
    with col_info:
        st.write(f"**BARCO:** {df['barco'].iloc[0]}")
        st.write(f"**PROPRIETÁRIO:** {df['armador'].iloc[0]}")
        st.write("**COMPRADOR:** NAVIMAR PESCADOS")
        data_descarga = df['data_hora'].iloc[0][:10]
        st.write(f"**DATA:** {datetime.strptime(data_descarga, '%Y-%m-%d').strftime('%d/%m/%Y')}")

    st.markdown("---")
    st.write("### 💰 Tabela de Preços (Edite os valores em R$)")

    # Campos de Edição para os Preços Baseados na Tabela Excel
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        preco_15_24 = st.number_input("R$ (15-24KG)", value=25.00, step=1.00)
    with col2:
        preco_25_39 = st.number_input("R$ (25-39KG)", value=29.00, step=1.00)
    with col3:
        preco_40 = st.number_input("R$ (40KG ACIMA)", value=32.00, step=1.00)
    with col4:
        preco_furo = st.number_input("R$ (2º FURO)", value=21.00, step=1.00)
    with col5:
        preco_lombo = st.number_input("R$ (LOMBO)", value=15.00, step=1.00)

    # Filtragem correta dos pesos conforme as categorias marcadas
    df_furo = df[df["segundo_furo"] == "Sim"]
    df_lombo = df[(df["lombo"] == "Sim") & (df["segundo_furo"] == "Não")]
    df_normal = df[(df["segundo_furo"] == "Não") & (df["lombo"] == "Não")]

    kg_15_24 = df_normal[df_normal["peso"] == "15-24kg"]["peso_kg"].sum()
    kg_25_39 = df_normal[df_normal["peso"] == "25-39kg"]["peso_kg"].sum()
    kg_40 = df_normal[df_normal["peso"] == "40+kg (Exportação)"]["peso_kg"].sum()
    kg_furo = df_furo["peso_kg"].sum()
    kg_lombo = df_lombo["peso_kg"].sum()

    # Cálculos Finais
    total_15_24 = kg_15_24 * preco_15_24
    total_25_39 = kg_25_39 * preco_25_39
    total_40 = kg_40 * preco_40
    total_furo = kg_furo * preco_furo
    total_lombo = kg_lombo * preco_lombo

    kg_geral = kg_15_24 + kg_25_39 + kg_40 + kg_furo + kg_lombo
    total_geral = total_15_24 + total_25_39 + total_40 + total_furo + total_lombo

    # Montando a Tabela do Romaneio (Modelo Excel)
    romaneio_data = {
        "TIPO (ATUM)": ["15KG - 24KG", "25KG - 39KG", "40KG ACIMA", "2º FURO", "LOMBO", "TOTAL"],
        "KG": [kg_15_24, kg_25_39, kg_40, kg_furo, kg_lombo, kg_geral],
        "PREÇO (R$)": [f"R$ {preco_15_24:.2f}", f"R$ {preco_25_39:.2f}", f"R$ {preco_40:.2f}", f"R$ {preco_furo:.2f}", f"R$ {preco_lombo:.2f}", "-"],
        "TOTAL": [f"R$ {total_15_24:.2f}", f"R$ {total_25_39:.2f}", f"R$ {total_40:.2f}", f"R$ {total_furo:.2f}", f"R$ {total_lombo:.2f}", f"R$ {total_geral:.2f}"]
    }

    df_romaneio = pd.DataFrame(romaneio_data)

    st.markdown("### 📄 Resultado do Romaneio")
    st.dataframe(df_romaneio, use_container_width=True, hide_index=True)

    # Botão para exportar no final
    csv_romaneio = df_romaneio.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Baixar Romaneio do Barco (CSV)",
        data=csv_romaneio,
        file_name=f"romaneio_{df['barco'].iloc[0]}_{df['data_hora'].iloc[0][:10]}.csv",
        mime="text/csv",
        use_container_width=True
    )
