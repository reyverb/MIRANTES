import streamlit as st
import pandas as pd
import sqlite3

st.set_page_config(
    page_title="Painel Gerencial & Romaneio",
    page_icon="📊",
    layout="wide"
)

# Conexão com o banco compartilhado
@st.cache_resource
def get_db():
    conn = sqlite3.connect("porto_atum.db", check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

conn = get_db()

# Navegação de retorno ao cais
st.page_link("app.py", label="Voltar para a Pesagem no Cais", icon="🐟")

st.title("📊 Painel Gerencial & Romaneio de Atum")

# Busca de lotes
descargas = pd.read_sql("SELECT id, barco, proprietario, data_hora, status FROM descargas ORDER BY id DESC", conn)

if descargas.empty:
    st.info("Nenhuma descarga encontrada no banco de dados.")
    st.stop()

# Filtro por lote
opcoes = {
    row["id"]: f"Lote #{row['id']} - {row['barco']} ({row['status']}) | {row['data_hora'][:10]}"
    for _, row in descargas.iterrows()
}

lote_selecionado = st.selectbox(
    "Selecione o Lote / Embarcação:",
    options=list(opcoes.keys()),
    format_func=lambda x: opcoes[x]
)

# Consulta com regras de BI
query_analitica = """
SELECT 
    d.id AS id_lote,
    d.barco,
    d.proprietario AS armador,
    p.numero_peca,
    p.peso_kg,
    p.categoria AS calibre,
    CASE WHEN p.peso_kg >= 40.0 THEN 1 ELSE 0 END AS is_exportacao,
    CASE WHEN p.segundo_furo = 1 THEN 'Sim' ELSE 'Não' END AS segundo_furo,
    p.destino,
    p.data_registro AS data_hora
FROM pecas p
JOIN descargas d ON d.id = p.id_descarga
WHERE p.id_descarga = ?
ORDER BY p.numero_peca ASC
"""
df = pd.read_sql(query_analitica, conn, params=(int(lote_selecionado),))

if df.empty:
    st.warning("Este lote não possui peças registradas ainda.")
    st.stop()

# --- CARDS DE PERFORMANCE ---
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

# --- ANÁLISE GRÁFICA & MATRIZ DE CALIBRES ---
col_graf, col_tab = st.columns([1, 1])

with col_graf:
    st.subheader("Volume por Calibre (Kg)")
    calibre_dist = df.groupby("calibre")["peso_kg"].sum().reset_index()
    st.bar_chart(calibre_dist.set_index("calibre"), use_container_width=True)

with col_tab:
    st.subheader("Quadro Sintético de Fechamento")
    resumo_calibre = df.groupby("calibre").agg(
        Pecas=("numero_peca", "count"),
        Peso_Total_Kg=("peso_kg", "sum"),
        Peso_Medio_Kg=("peso_kg", "mean"),
        Com_2_Furo=("segundo_furo", lambda x: (x == "Sim").sum())
    ).reset_index()
    resumo_calibre["Part_%"] = (resumo_calibre["Peso_Total_Kg"] / total_kg) * 100
    st.dataframe(
        resumo_calibre,
        column_config={
            "Peso_Total_Kg": st.column_config.NumberColumn(format="%.2f kg"),
            "Peso_Medio_Kg": st.column_config.NumberColumn(format="%.2f kg"),
            "Part_%": st.column_config.NumberColumn(format="%.1f%%")
        },
        hide_index=True,
        use_container_width=True
    )

st.divider()

# --- EXPORTAÇÃO COMPLETA PARA BI / POWER BI / EXCEL ---
st.subheader("📥 Exportação do Romaneio Analítico")
csv_bi = df.to_csv(index=False, sep=";").encode("utf-8-sig")

st.download_button(
    label=f"💾 Baixar CSV Estruturado (Lote #{lote_selecionado})",
    data=csv_bi,
    file_name=f"romaneio_bi_lote_{lote_selecionado}.csv",
    mime="text/csv",
    type="primary",
    use_container_width=True
)
