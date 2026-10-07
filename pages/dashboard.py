import streamlit as st
import pandas as pd
import sqlite3
import io
import plotly.express as px
from datetime import datetime
from PIL import Image
import os
import base64

# --- 1. CARREGAMENTO DA IMAGEM E BASE64 ---
img_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logo.png")
if not os.path.exists(img_path):
    img_path = "logo.png"

try:
    logo = Image.open(img_path)
except:
    logo = "🐟"

# Função para converter a logo em texto e colocar no HTML
def get_image_base64(path):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except:
        return ""

logo_b64 = get_image_base64(img_path)

# --- 2. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Painel Gerencial & Romaneio",
    page_icon=logo,
    layout="wide"
)

# --- 3. IDENTIDADE VISUAL ---
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background-color: #EAF4F4; }
    [data-testid="stSidebar"] { background-color: #031523; }
    h1, h2, h3, h4 { color: #031523 !important; }
    p, label, span { color: #031523 !important; }
    [data-testid="stSidebarNav"] span { color: #EAF4F4 !important; font-weight: bold; }
    .stButton>button {
        background-color: #E4D9C3; color: #031523; border-radius: 5px;
        font-weight: bold; border: 2px solid #031523;
    }
    .stButton>button:hover {
        background-color: #031523; color: #E4D9C3; border: 2px solid #E4D9C3;
    }
    [data-testid="stDataFrame"] { border: 2px solid #031523; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

# --- 4. CONEXÃO SEGURA E RECUPERAÇÃO DO BANCO ---
@st.cache_resource
def get_db():
    conn = sqlite3.connect("porto_atum.db", check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    cursor = conn.cursor()
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
        d.id AS id_lote, d.barco, d.proprietario AS armador,
        p.numero_peca, p.peso_kg, p.categoria AS peso,
        CASE WHEN p.peso_kg >= 40.0 THEN 1 ELSE 0 END AS is_exportacao,
        CASE WHEN p.segundo_furo = 1 THEN 'Sim' ELSE 'Não' END AS segundo_furo,
        'Não' AS lombo, p.destino, p.data_registro AS data_hora
    FROM pecas p
    JOIN descargas d ON d.id = p.id_descarga
    WHERE p.id_descarga = ? ORDER BY p.numero_peca ASC
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
    qtd_lombo = (df["lombo"] == "Sim").sum()

    # Cards principais expandidos
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Peso Total", f"{total_kg:,.1f} kg")
    c2.metric("Total de Peças", f"{total_pecas}")
    c3.metric("Peso Médio / Peça", f"{peso_medio:.2f} kg")
    c4.metric("% Exportação (40+kg)", f"{perc_export:.1f}%", f"{perc_furo:.1f}% 2º furo", delta_color="inverse")
    c5.metric("Peças p/ Lombo", f"{qtd_lombo}")

    st.divider()

    # Gráficos de Visão Geral aprimorados
    col_graf1, col_graf2 = st.columns(2)
    
    with col_graf1:
        st.subheader("Dispersão Peça a Peça")
        fig_scatter = px.scatter(
            df, x="numero_peca", y="peso_kg", color="peso", symbol="segundo_furo",
            hover_data=["destino"], title="Histórico de Pesagem na Descarga",
            labels={"numero_peca": "Sequência (Nº Peça)", "peso_kg": "Peso (kg)"},
            template="plotly_white"
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    with col_graf2:
        st.subheader("Distribuição por Destino")
        df_destino = df.groupby("destino")["peso_kg"].sum().reset_index()
        fig_pie = px.pie(
            df_destino, names="destino", values="peso_kg", hole=0.45,
            title="Volume (kg) por Destino", template="plotly_white",
            color_discrete_sequence=["#031523", "#E4D9C3"]
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    st.divider()
    
    # Quadro Sintético
    st.subheader("Quadro Sintético de Fechamento por Categoria")
    resumo_peso = df.groupby("peso").agg(
        Pecas=("numero_peca", "count"),
        Peso_Total_Kg=("peso_kg", "sum"),
        Peso_Medio_Kg=("peso_kg", "mean"),
        Com_2_Furo=("segundo_furo", lambda x: (x == "Sim").sum()),
        Com_Lombo=("lombo", lambda x: (x == "Sim").sum())
    ).reset_index()
    resumo_peso["Part_%"] = (resumo_peso["Peso_Total_Kg"] / total_kg) * 100

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
             st.image(img_path, width=180)
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

    # Dicionário de preços para passar para as funções de exportação
    tabela_precos = {
        "15_24": preco_15_24, "25_39": preco_25_39,
        "40_up": preco_40, "furo": preco_furo, "lombo": preco_lombo
    }

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


# ==============================================================================
# FUNÇÕES DE EXPORTAÇÃO (HTML e EXCEL) COM PREÇOS E LOGO
# ==============================================================================
def gerar_dashboard_html(df_lote, df_resumo, df_financeiro, logo_b64_str):
    # Gráficos
    fig_calibre = px.bar(
        df_resumo, x="peso", y="Peso_Total_Kg", text="Pecas", color="peso",
        title="Volume Total por Faixa de Peso (kg)", template="plotly_white",
        color_discrete_sequence=["#031523", "#E4D9C3", "#0284c7", "#38bdf8"]
    )
    fig_calibre.update_traces(texttemplate="%{y:.1f} kg", textposition="outside")
    fig_calibre.update_layout(showlegend=False, margin=dict(t=50, b=30, l=30, r=30))
    
    html_fig1 = fig_calibre.to_html(full_html=False, include_plotlyjs="cdn")

    # Construção da tabela financeira em HTML
    linhas_financeiro = ""
    for _, row in df_financeiro.iterrows():
        is_total = "font-weight: bold; background: #e2e8f0;" if row["TIPO (ATUM)"] == "TOTAL" else ""
        linhas_financeiro += f"""
        <tr style="{is_total}">
            <td style="padding: 10px; border-bottom: 1px solid #cbd5e1;">{row['TIPO (ATUM)']}</td>
            <td style="padding: 10px; border-bottom: 1px solid #cbd5e1; text-align: right;">{row['KG']:.2f} kg</td>
            <td style="padding: 10px; border-bottom: 1px solid #cbd5e1; text-align: center;">{row['PREÇO (R$)']}</td>
            <td style="padding: 10px; border-bottom: 1px solid #cbd5e1; text-align: right;"><strong>{row['TOTAL']}</strong></td>
        </tr>
        """

    img_tag = f'<img src="data:image/png;base64,{logo_b64_str}" style="max-height: 80px;">' if logo_b64_str else '<h2>NAVIMAR PESCADOS</h2>'

    html_completo = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head><meta charset="UTF-8"><title>Relatório - {df_lote['barco'].iloc[0]}</title></head>
    <body style="font-family: sans-serif; background: #f8fafc; padding: 20px; color: #0f172a;">
        <div style="max-width: 1000px; margin: auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #031523; padding-bottom: 20px; margin-bottom: 20px;">
                <div>{img_tag}</div>
                <div style="text-align: right;">
                    <h2 style="margin: 0; color: #031523;">ROMANEIO DE DESCARGA</h2>
                    <p style="margin: 5px 0;"><strong>Barco:</strong> {df_lote['barco'].iloc[0]} | <strong>Data:</strong> {df_lote['data_hora'].iloc[0][:10]}</p>
                </div>
            </div>

            <div style="display: flex; gap: 20px;">
                <div style="width: 50%;">
                    <h3 style="color: #031523;">Resumo Financeiro</h3>
                    <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                        <thead>
                            <tr style="background: #031523; color: white;">
                                <th style="padding: 10px; text-align: left;">Tipo</th>
                                <th style="padding: 10px; text-align: right;">KG</th>
                                <th style="padding: 10px; text-align: center;">Preço (R$)</th>
                                <th style="padding: 10px; text-align: right;">Total</th>
                            </tr>
                        </thead>
                        <tbody>
                            {linhas_financeiro}
                        </tbody>
                    </table>
                </div>
                <div style="width: 50%;">
                    {html_fig1}
                </div>
            </div>
            
        </div>
    </body>
    </html>
    """
    return html_completo.encode("utf-8")


def gerar_excel_executivo(df_lote, precos, img_path):
    output = io.BytesIO()
    
    barco = str(df_lote["barco"].iloc[0]).upper()
    armador = str(df_lote["armador"].iloc[0]).upper()
    data_lote_str = df_lote["data_hora"].iloc[0][:10]
    data_formatada = datetime.strptime(data_lote_str, '%Y-%m-%d').strftime('%d/%m/%Y')
    
    df_furo = df_lote[df_lote["segundo_furo"] == "Sim"]
    df_lombo = df_lote[(df_lote["lombo"] == "Sim") & (df_lote["segundo_furo"] == "Não")]
    df_normal = df_lote[(df_lote["segundo_furo"] == "Não") & (df_lote["lombo"] == "Não")]

    kg_15_24 = df_normal[df_normal["peso"] == "15-24kg"]["peso_kg"].sum()
    kg_25_39 = df_normal[df_normal["peso"] == "25-39kg"]["peso_kg"].sum()
    kg_40_up = df_normal[df_normal["peso"] == "40+kg (Exportação)"]["peso_kg"].sum()
    kg_2_furo = df_furo["peso_kg"].sum()
    kg_lombo_final = df_lombo["peso_kg"].sum()
    
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        workbook = writer.book
        ws = workbook.add_worksheet("Planilha1")
        ws.hide_gridlines(2)
        
        # Inserir Logo no Excel
        try:
            if os.path.exists(img_path):
                # Scale ajustado para não ficar gigante na célula
                ws.insert_image('A1', img_path, {'x_scale': 0.15, 'y_scale': 0.15})
        except:
            pass
        
        fmt_bold = workbook.add_format({"bold": True, "valign": "vcenter"})
        fmt_cabecalho_tbl = workbook.add_format({"bold": True, "border": 1, "bg_color": "#D9D9D9", "align": "center"})
        fmt_tbl_texto = workbook.add_format({"border": 1, "align": "center", "bold": True})
        fmt_tbl_num = workbook.add_format({"border": 1, "align": "center", "num_format": '#,##0.00'})
        fmt_tbl_moeda = workbook.add_format({"border": 1, "align": "center", "num_format": 'R$ #,##0.00'})
        
        ws.set_column("A:A", 5) # Margem esq
        ws.set_column("B:B", 18)
        ws.set_column("C:E", 16)
        
        # Deslocamos os dados para a linha 5 para a Logo ficar livre acima
        ws.write("B6", "BARCO:", fmt_bold)
        ws.write("C6", f" {barco}", fmt_bold)
        ws.write("B7", "PROPRIETÁRIO:", fmt_bold)
        ws.write("C7", f" {armador}", fmt_bold)
        ws.write("B8", "COMANDANTE:", fmt_bold)
        ws.write("C8", " ", fmt_bold)
        ws.write("B9", "COMPRADOR:", fmt_bold)
        ws.write("C9", " NAVIMAR PESCADOS", fmt_bold)
        ws.write("B10", "DATA:", fmt_bold)
        ws.write("C10", f" {data_formatada}", fmt_bold)
        
        headers = ["TIPO (ATUM)", "KG", "PREÇO (R$)", "TOTAL"]
        for col_num, header in enumerate(headers, start=1):
            ws.write(12, col_num, header, fmt_cabecalho_tbl)
            
        # Linhas de dados consumindo o dicionário de preços inseridos no App
        linhas_dados = [
            ("15KG - 24KG", kg_15_24, precos["15_24"]), 
            ("25KG - 39KG", kg_25_39, precos["25_39"]), 
            ("40KG ACIMA", kg_40_up, precos["40_up"]),
            ("2º FURO", kg_2_furo, precos["furo"]),
            ("LOMBO", kg_lombo_final, precos["lombo"])
        ]
        
        linha_atual = 13
        for tipo, kg, preco in linhas_dados:
            ws.write(linha_atual, 1, tipo, fmt_tbl_texto)
            ws.write(linha_atual, 2, kg if kg > 0 else 0, fmt_tbl_num)
            ws.write(linha_atual, 3, preco, fmt_tbl_moeda) # PREÇO AQUI!
            ws.write_formula(linha_atual, 4, f"=C{linha_atual + 1}*D{linha_atual + 1}", fmt_tbl_moeda)
            linha_atual += 1
            
        ws.write(linha_atual, 1, "TOTAL", fmt_tbl_texto)
        ws.write_formula(linha_atual, 2, f"=SUM(C14:C{linha_atual})", fmt_tbl_num)
        ws.write(linha_atual, 3, "-", fmt_tbl_texto)
        ws.write_formula(linha_atual, 4, f"=SUM(E14:E{linha_atual})", fmt_tbl_moeda)
        
    return output.getvalue()

st.divider()

# --- BOTÕES DE EXPORTAÇÃO LADO A LADO ---
st.subheader("📥 Exportação do Relatório Oficial")
col_btn1, col_btn2, col_btn3 = st.columns(3)

with col_btn1:
    html_bytes = gerar_dashboard_html(df, resumo_peso, df_romaneio, logo_b64) 
    st.download_button(
        label="🌐 Dashboard Interativo (.HTML)",
        data=html_bytes,
        file_name=f"dashboard_lote_{df['barco'].iloc[0]}.html",
        mime="text/html",
        use_container_width=True
    )

with col_btn2:
    excel_bytes = gerar_excel_executivo(df, tabela_precos, img_path)
    st.download_button(
        label="📊 Excel Executivo Modelo (.XLSX)",
        data=excel_bytes,
        file_name=f"Romaneio_Navimar_{df['barco'].iloc[0]}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

with col_btn3:
    csv_romaneio_geral = df_romaneio.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 CSV Resumo Comercial (.CSV)",
        data=csv_romaneio_geral,
        file_name=f"resumo_comercial_{df['barco'].iloc[0]}.csv",
        mime="text/csv",
        use_container_width=True
    )
