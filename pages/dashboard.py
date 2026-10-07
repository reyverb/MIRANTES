import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from PIL import Image
import os
import io
import plotly.express as px
# --- 1. CARREGAMENTO DA IMAGEM ---
try:
    # Ajuste do caminho da imagem para garantir que encontre estando dentro da pasta pages/
    img_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logo.png")
    logo = Image.open(img_path)
except FileNotFoundError:
    try:
         logo = Image.open("logo.png")
    except:
         logo = "🐟"

# --- 2. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Painel Gerencial & Romaneio",
    page_icon=logo,
    layout="wide"
)

# --- 3. IDENTIDADE VISUAL ---
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
    [data-testid="stDataFrame"] {
        border: 2px solid #031523;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# --- 4. CONEXÃO SEGURA E RECUPERAÇÃO DO BANCO ---
@st.cache_resource
def get_db():
    conn = sqlite3.connect("porto_atum.db", check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    cursor = conn.cursor()
    # Garante a existência da tabela antes de prosseguir
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS descargas (
        id INTEGER PRIMARY KEY AUTOINCREMENT, barco TEXT NOT NULL,
        proprietario TEXT NOT NULL, data_hora TEXT NOT NULL,
        status TEXT DEFAULT 'Em Andamento'
    )""")
    conn.commit()
    return conn

conn = get_db()

# --- 5. INTERFACE DO DASHBOARD ---
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

# Consulta com proteção para a coluna lombo
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


# --- ABAS VISUAIS ---
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
    
    col_img, col_info = st.columns([1, 3])
    with col_img:
        try:
             # Tenta carregar a imagem na interface
             st.image(img_path, width=180)
        except:
             try:
                  st.image("logo.png", width=180)
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

    df_furo = df[df["segundo_furo"] == "Sim"]
    df_lombo = df[(df["lombo"] == "Sim") & (df["segundo_furo"] == "Não")]
    df_normal = df[(df["segundo_furo"] == "Não") & (df["lombo"] == "Não")]

    kg_15_24 = df_normal[df_normal["peso"] == "15-24kg"]["peso_kg"].sum()
    kg_25_39 = df_normal[df_normal["peso"] == "25-39kg"]["peso_kg"].sum()
    kg_40 = df_normal[df_normal["peso"] == "40+kg (Exportação)"]["peso_kg"].sum()
    kg_furo = df_furo["peso_kg"].sum()
    kg_lombo = df_lombo["peso_kg"].sum()

    total_15_24 = kg_15_24 * preco_15_24
    total_25_39 = kg_25_39 * preco_25_39
    total_40 = kg_40 * preco_40
    total_furo = kg_furo * preco_furo
    total_lombo = kg_lombo * preco_lombo

    kg_geral = kg_15_24 + kg_25_39 + kg_40 + kg_furo + kg_lombo
    total_geral = total_15_24 + total_25_39 + total_40 + total_furo + total_lombo

    romaneio_data = {
        "TIPO (ATUM)": ["15KG - 24KG", "25KG - 39KG", "40KG ACIMA", "2º FURO", "LOMBO", "TOTAL"],
        "KG": [kg_15_24, kg_25_39, kg_40, kg_furo, kg_lombo, kg_geral],
        "PREÇO (R$)": [f"R$ {preco_15_24:.2f}", f"R$ {preco_25_39:.2f}", f"R$ {preco_40:.2f}", f"R$ {preco_furo:.2f}", f"R$ {preco_lombo:.2f}", "-"],
        "TOTAL": [f"R$ {total_15_24:.2f}", f"R$ {total_25_39:.2f}", f"R$ {total_40:.2f}", f"R$ {total_furo:.2f}", f"R$ {total_lombo:.2f}", f"R$ {total_geral:.2f}"]
    }

    df_romaneio = pd.DataFrame(romaneio_data)

    st.markdown("### 📄 Resultado do Romaneio")
    st.dataframe(df_romaneio, use_container_width=True, hide_index=True)

    csv_romaneio = df_romaneio.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Baixar Romaneio do Barco (CSV)",
        data=csv_romaneio,
        file_name=f"romaneio_{df['barco'].iloc[0]}_{df['data_hora'].iloc[0][:10]}.csv",
        mime="text/csv",
        use_container_width=True
    )
# ==============================================================================
# OPÇÃO 1: GERADOR DE DASHBOARD HTML INTERATIVO (PLOTLY + CSS + FILTRO JS)
# (Usando o backup fornecido)
# ==============================================================================
def gerar_dashboard_html(df_lote, df_resumo):
    # Gráfico 1: Volume por Calibre
    fig_calibre = px.bar(
        df_resumo, x="calibre", y="Peso_Total_Kg", text="Pecas", color="calibre",
        title="Volume Total por Calibre (kg) e Qtd. de Peças",
        template="plotly_white", color_discrete_sequence=["#0284c7", "#0ea5e9", "#38bdf8", "#0369a1"]
    )
    fig_calibre.update_traces(texttemplate="%{y:.1f} kg (%{text} pçs)", textposition="outside")
    fig_calibre.update_layout(showlegend=False, margin=dict(t=50, b=30, l=30, r=30))

    # Gráfico 2: Distribuição por Destino
    df_destino = df_lote.groupby("destino")["peso_kg"].sum().reset_index()
    fig_destino = px.pie(
        df_destino, names="destino", values="peso_kg", hole=0.45,
        title="Divisão de Volume por Destino (kg)",
        template="plotly_white", color_discrete_sequence=["#0f172a", "#0284c7"]
    )
    fig_destino.update_traces(textinfo="percent+label+value")
    
    # Renderização HTML
    html_fig1 = fig_calibre.to_html(full_html=False, include_plotlyjs="cdn")
    html_fig2 = fig_destino.to_html(full_html=False, include_plotlyjs=False)

    html_completo = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head><meta charset="UTF-8"><title>Relatório - Lote</title></head>
    <body style="font-family: sans-serif; padding: 20px;">
        <h2>Painel Gerencial - Lote</h2>
        <div style="display: flex; gap: 20px;">
            <div style="width: 50%;">{html_fig1}</div>
            <div style="width: 50%;">{html_fig2}</div>
        </div>
    </body>
    </html>
    """
    return html_completo.encode("utf-8")


# ==============================================================================
# OPÇÃO 2: NOVO EXCEL EXECUTIVO - SEGUINDO MODELO ANEXADO
# ==============================================================================
def gerar_excel_executivo(df_lote):
    output = io.BytesIO()
    
    # Extração de dados da embarcação e consolidação dos calibres
    barco = str(df_lote["barco"].iloc[0]).upper()
    armador = str(df_lote["armador"].iloc[0]).upper()
    data_lote = df_lote["data_hora"].iloc[0][:10]
    
    # Categorização conforme layout exigido
    kg_15_24 = df_lote[df_lote["calibre"] == "15kg a 24.9kg"]["peso_kg"].sum()
    kg_25_39 = df_lote[df_lote["calibre"] == "25kg a 39.9kg"]["peso_kg"].sum()
    kg_40_up = df_lote[df_lote["calibre"] == "+40kg Exportação"]["peso_kg"].sum()
    kg_2_furo = df_lote[df_lote["segundo_furo"] == "Sim"]["peso_kg"].sum()
    
    # Nota: A categoria 'LOMBO' não está explícita no BI, alocada como 0, 
    # mas ajustável caso você insira uma regra.
    kg_lombo = df_lote[df_lote["calibre"] == "Lombo"]["peso_kg"].sum() if "Lombo" in df_lote["calibre"].values else 0
    total_kg_geral = df_lote["peso_kg"].sum()
    
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        workbook = writer.book
        ws = workbook.add_worksheet("Planilha1")
        ws.hide_gridlines(2)
        
        # Formatos do modelo
        fmt_bold = workbook.add_format({"bold": True, "valign": "vcenter"})
        fmt_cabecalho_tbl = workbook.add_format({"bold": True, "border": 1, "bg_color": "#D9D9D9", "align": "center"})
        fmt_tbl_texto = workbook.add_format({"border": 1, "align": "center", "bold": True})
        fmt_tbl_num = workbook.add_format({"border": 1, "align": "center", "num_format": '#,##0'})
        fmt_tbl_moeda = workbook.add_format({"border": 1, "align": "center", "num_format": 'R$ #,##0.00'})
        
        # Largura das colunas
        ws.set_column("B:B", 18)
        ws.set_column("C:E", 14)
        
        # Cabeçalho da embarcação (Linhas 2 a 6)
        ws.write("B3", "BARCO:", fmt_bold)
        ws.write("C3", f" {barco}", fmt_bold)
        ws.write("B4", "PROPRIETÁRIO:", fmt_bold)
        ws.write("C4", f" {armador}", fmt_bold)
        ws.write("B5", "COMANDANTE:", fmt_bold)
        ws.write("C5", " ", fmt_bold)  # Para preencher à mão/posteriormente
        ws.write("B6", "COMPRADOR:", fmt_bold)
        ws.write("C6", " NAVIMAR PESCADOS", fmt_bold)
        ws.write("B7", "DATA:", fmt_bold)
        ws.write("C7", f" {data_lote}", fmt_bold)
        
        # Cabeçalho da Tabela (Linha 8)
        headers = ["TIPO (ATUM)", "KG", "PREÇO (R$)", "TOTAL"]
        for col_num, header in enumerate(headers, start=1):
            ws.write(8, col_num, header, fmt_cabecalho_tbl)
            
        # Preenchimento da Tabela
        linhas_dados = [
            ("15KG - 24KG", kg_15_24, ""), 
            ("25KG - 39KG", kg_25_39, ""), 
            ("40KG ACIMA", kg_40_up, ""),
            ("2º FURO", kg_2_furo, ""),
            ("LOMBO", kg_lombo, "")
        ]
        
        linha_atual = 9
        for tipo, kg, preco in linhas_dados:
            ws.write(linha_atual, 1, tipo, fmt_tbl_texto)
            ws.write(linha_atual, 2, kg if kg > 0 else "", fmt_tbl_num)
            ws.write(linha_atual, 3, preco, fmt_tbl_num)
            # Fórmula Excel para calcular o total por linha se houvesse preço preenchido.
            ws.write_formula(linha_atual, 4, f"=IF(ISBLANK(D{linha_atual + 1}), 0, C{linha_atual + 1}*D{linha_atual + 1})", fmt_tbl_num)
            linha_atual += 1
            
        # Linha de TOTAL
        ws.write(linha_atual, 1, "TOTAL", fmt_tbl_texto)
        ws.write_formula(linha_atual, 2, f"=SUM(C10:C{linha_atual})", fmt_tbl_num)
        ws.write(linha_atual, 3, "", fmt_tbl_num)
        ws.write_formula(linha_atual, 4, f"=SUM(E10:E{linha_atual})", fmt_tbl_num)
        
    return output.getvalue()


# --- BOTÕES DE EXPORTAÇÃO LADO A LADO ---
st.subheader("📥 Exportação do Romaneio")
col_btn1, col_btn2 = st.columns(2)

with col_btn1:
    html_bytes = gerar_dashboard_html(df, resumo_calibre)
    st.download_button(
        label="🌐 Dashboard Interativo (.HTML)",
        data=html_bytes,
        file_name=f"dashboard_lote.html",
        mime="text/html",
        use_container_width=True
    )

with col_btn2:
    excel_bytes = gerar_excel_executivo(df)
    st.download_button(
        label="📊 Excel Executivo Modelo (.XLSX)",
        data=excel_bytes,
        file_name=f"romaneio_navimar.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
