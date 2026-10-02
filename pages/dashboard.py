import streamlit as st
import pandas as pd
import sqlite3
import io
import plotly.express as px

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

# --- ANÁLISE GRÁFICA & MATRIZ DE CALIBRES ---
col_graf, col_tab = st.columns([1, 1])

resumo_calibre = df.groupby("calibre").agg(
    Pecas=("numero_peca", "count"),
    Peso_Total_Kg=("peso_kg", "sum"),
    Peso_Medio_Kg=("peso_kg", "mean"),
    Com_2_Furo=("segundo_furo", lambda x: (x == "Sim").sum())
).reset_index()
resumo_calibre["Part_%"] = (resumo_calibre["Peso_Total_Kg"] / total_kg) * 100

with col_graf:
    st.subheader("Volume por Calibre (Kg)")
    calibre_dist = df.groupby("calibre")["peso_kg"].sum().reset_index()
    st.bar_chart(calibre_dist.set_index("calibre"), use_container_width=True)

with col_tab:
    st.subheader("Quadro Sintético de Fechamento")
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


# ==============================================================================
# OPÇÃO 1: GERADOR DE DASHBOARD HTML INTERATIVO (PLOTLY + CSS + FILTRO JS)
# ==============================================================================
def gerar_dashboard_html(df_lote, df_resumo):
    # Gráfico 1: Volume por Calibre
    fig_calibre = px.bar(
        df_resumo,
        x="calibre",
        y="Peso_Total_Kg",
        text="Pecas",
        color="calibre",
        title="Volume Total por Calibre (kg) e Qtd. de Peças",
        labels={"calibre": "Faixa de Calibre", "Peso_Total_Kg": "Peso Total (kg)", "Pecas": "Peças"},
        template="plotly_white",
        color_discrete_sequence=["#0284c7", "#0ea5e9", "#38bdf8", "#0369a1"]
    )
    fig_calibre.update_traces(texttemplate="%{y:.1f} kg (%{text} pçs)", textposition="outside")
    fig_calibre.update_layout(showlegend=False, margin=dict(t=50, b=30, l=30, r=30))

    # Gráfico 2: Distribuição por Destino
    df_destino = df_lote.groupby("destino")["peso_kg"].sum().reset_index()
    fig_destino = px.pie(
        df_destino,
        names="destino",
        values="peso_kg",
        hole=0.45,
        title="Divisão de Volume por Destino (kg)",
        template="plotly_white",
        color_discrete_sequence=["#0f172a", "#0284c7"]
    )
    fig_destino.update_traces(textinfo="percent+label+value")
    fig_destino.update_layout(margin=dict(t=50, b=30, l=30, r=30))

    # Gráfico 3: Dispersão Peça a Peça
    fig_pecas = px.scatter(
        df_lote,
        x="numero_peca",
        y="peso_kg",
        color="calibre",
        symbol="segundo_furo",
        hover_data=["destino", "data_hora"],
        title="Histórico de Pesagem Peça a Peça (Sequência de Descarga)",
        labels={"numero_peca": "Nº da Peça", "peso_kg": "Peso (kg)", "calibre": "Calibre", "segundo_furo": "2º Furo"},
        template="plotly_white"
    )
    fig_pecas.update_traces(marker=dict(size=10, line=dict(width=1, color="DarkSlateGrey")))
    fig_pecas.update_layout(margin=dict(t=50, b=30, l=30, r=30))

    html_fig1 = fig_calibre.to_html(full_html=False, include_plotlyjs="cdn")
    html_fig2 = fig_destino.to_html(full_html=False, include_plotlyjs=False)
    html_fig3 = fig_pecas.to_html(full_html=False, include_plotlyjs=False)

    # Linhas do Quadro Sintético
    linhas_resumo = ""
    for _, r in df_resumo.iterrows():
        linhas_resumo += f"""
        <tr>
            <td><strong>{r['calibre']}</strong></td>
            <td>{int(r['Pecas'])}</td>
            <td>{r['Peso_Total_Kg']:,.2f} kg</td>
            <td>{r['Peso_Medio_Kg']:,.2f} kg</td>
            <td>{int(r['Com_2_Furo'])}</td>
            <td>{r['Part_%']:.1f}%</td>
        </tr>
        """

    # Linhas do Romaneio Detalhado
    linhas_pecas = ""
    for _, r in df_lote.iterrows():
        badge_furo = '<span class="badge-alerta">Sim</span>' if r["segundo_furo"] == "Sim" else '<span class="badge-ok">Não</span>'
        linhas_pecas += f"""
        <tr>
            <td>#{int(r['numero_peca'])}</td>
            <td><strong>{r['peso_kg']:.2f} kg</strong></td>
            <td>{r['calibre']}</td>
            <td>{badge_furo}</td>
            <td>{r['destino']}</td>
            <td>{r['data_hora']}</td>
        </tr>
        """

    html_completo = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <title>Relatório Gerencial - Lote #{lote_selecionado}</title>
        <style>
            body {{ font-family: 'Segoe UI', system-ui, sans-serif; background: #f1f5f9; color: #0f172a; margin: 0; padding: 24px; }}
            .container {{ max-width: 1280px; margin: auto; }}
            .header {{ background: linear-gradient(135deg, #0f172a, #0369a1); color: white; padding: 24px 32px; border-radius: 12px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }}
            .header h1 {{ margin: 0 0 6px 0; font-size: 24px; }}
            .header p {{ margin: 0; opacity: 0.85; font-size: 14px; }}
            .kpis {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 24px; }}
            .card {{ background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); border-left: 5px solid #0284c7; }}
            .card span {{ font-size: 13px; color: #64748b; text-transform: uppercase; font-weight: 600; }}
            .card h2 {{ margin: 8px 0 4px 0; font-size: 28px; color: #0f172a; }}
            .card small {{ color: #0369a1; font-weight: 600; }}
            .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 24px; }}
            .panel {{ background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); margin-bottom: 24px; }}
            .panel h3 {{ margin-top: 0; border-bottom: 1px solid #e2e8f0; padding-bottom: 10px; }}
            table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
            th {{ background: #f8fafc; text-align: left; padding: 12px; border-bottom: 2px solid #cbd5e1; color: #334155; }}
            td {{ padding: 10px 12px; border-bottom: 1px solid #e2e8f0; }}
            tr:hover {{ background: #f8fafc; }}
            .search-input {{ width: 100%; padding: 10px 14px; margin-bottom: 14px; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 14px; box-sizing: border-box; }}
            .badge-alerta {{ background: #fee2e2; color: #991b1b; padding: 3px 8px; border-radius: 6px; font-weight: 600; font-size: 12px; }}
            .badge-ok {{ background: #dcfce7; color: #166534; padding: 3px 8px; border-radius: 6px; font-weight: 600; font-size: 12px; }}
            @media (max-width: 900px) {{ .grid-2 {{ grid-template-columns: 1fr; }} }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div>
                    <h1>🐟 Painel Gerencial & Romaneio de Atum</h1>
                    <p>Embarcação: <strong>{barco_nome}</strong> | Armador: <strong>{armador_nome}</strong> | Lote #{lote_selecionado}</p>
                </div>
                <button onclick="window.print()" style="background:white; color:#0f172a; border:none; padding:10px 16px; border-radius:8px; font-weight:600; cursor:pointer;">🖨️ Imprimir / Salvar PDF</button>
            </div>

            <div class="kpis">
                <div class="card"><span>Peso Total</span><h2>{total_kg:,.1f} kg</h2><small>Volume consolidado</small></div>
                <div class="card"><span>Total de Peças</span><h2>{total_pecas}</h2><small>Unidades pesadas</small></div>
                <div class="card"><span>Peso Médio / Peça</span><h2>{peso_medio:.2f} kg</h2><small>Média geral do lote</small></div>
                <div class="card"><span>% Exportação (40+kg)</span><h2>{perc_export:.1f}%</h2><small>{perc_furo:.1f}% com 2º furo ({qtd_furo} pçs)</small></div>
            </div>

            <div class="grid-2">
                <div class="panel">{html_fig1}</div>
                <div class="panel">{html_fig2}</div>
            </div>

            <div class="panel">{html_fig3}</div>

            <div class="panel">
                <h3>📋 Quadro Sintético de Fechamento por Calibre</h3>
                <table>
                    <thead>
                        <tr><th>Calibre</th><th>Peças</th><th>Peso Total</th><th>Peso Médio</th><th>Com 2º Furo</th><th>Participação (%)</th></tr>
                    </thead>
                    <tbody>{linhas_resumo}</tbody>
                </table>
            </div>

            <div class="panel">
                <h3>🔎 Romaneio Analítico Peça a Peça (Interativo)</h3>
                <input type="text" id="filtroTabela" class="search-input" onkeyup="filtrarRomaneio()" placeholder="Digite para filtrar por calibre, destino (Caminhão / Câmara Fria), 2º furo ou nº da peça...">
                <table id="tabelaRomaneio">
                    <thead>
                        <tr><th>Nº Peça</th><th>Peso (kg)</th><th>Calibre</th><th>2º Furo</th><th>Destino</th><th>Data/Hora</th></tr>
                    </thead>
                    <tbody>{linhas_pecas}</tbody>
                </table>
            </div>
        </div>

        <script>
            function filtrarRomaneio() {{
                var input = document.getElementById("filtroTabela");
                var filter = input.value.toUpperCase();
                var tr = document.getElementById("tabelaRomaneio").getElementsByTagName("tr");
                for (var i = 1; i < tr.length; i++) {{
                    var textoLinha = tr[i].textContent || tr[i].innerText;
                    tr[i].style.display = textoLinha.toUpperCase().indexOf(filter) > -1 ? "" : "none";
                }}
            }}
        </script>
    </body>
    </html>
    """
    return html_completo.encode("utf-8")


# ==============================================================================
# OPÇÃO 2: GERADOR DE EXCEL EXECUTIVO (.XLSX COM DASHBOARD E GRÁFICOS NATIVOS)
# ==============================================================================
def gerar_excel_executivo(df_lote, df_resumo):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        workbook = writer.book

        # --- ABA 1: PAINEL GERENCIAL ---
        ws_dash = workbook.add_worksheet("Painel Gerencial")
        ws_dash.hide_gridlines(2)

        # Paleta de Estilos
        fmt_titulo = workbook.add_format({"bold": True, "font_size": 16, "font_color": "#FFFFFF", "bg_color": "#0F172A", "valign": "vcenter"})
        fmt_subtitulo = workbook.add_format({"italic": True, "font_size": 10, "font_color": "#E2E8F0", "bg_color": "#0F172A", "valign": "vcenter"})
        fmt_kpi_label = workbook.add_format({"bold": True, "font_size": 9, "font_color": "#64748B", "bg_color": "#F8FAFC", "top": 1, "left": 1, "right": 1, "border_color": "#CBD5E1", "align": "center"})
        fmt_kpi_val = workbook.add_format({"bold": True, "font_size": 15, "font_color": "#0284C7", "bg_color": "#F8FAFC", "bottom": 1, "left": 1, "right": 1, "border_color": "#CBD5E1", "align": "center"})
        fmt_sec_header = workbook.add_format({"bold": True, "font_size": 12, "font_color": "#0F172A", "bottom": 2, "border_color": "#0284C7"})
        fmt_th = workbook.add_format({"bold": True, "bg_color": "#0284C7", "font_color": "#FFFFFF", "border": 1, "align": "center"})
        fmt_td_str = workbook.add_format({"border": 1, "align": "left"})
        fmt_td_int = workbook.add_format({"border": 1, "align": "center", "num_format": "#,##0"})
        fmt_td_kg = workbook.add_format({"border": 1, "align": "right", "num_format": '#,##0.00 "kg"'})
        fmt_td_pct = workbook.add_format({"border": 1, "align": "right", "num_format": "0.0%"})

        # Largura das colunas
        ws_dash.set_column("A:A", 24)
        ws_dash.set_column("B:F", 16)

        # Banner de Cabeçalho
        ws_dash.merge_range("A1:F1", f"  PAINEL GERENCIAL DE DESEMBARQUE - LOTE #{lote_selecionado}", fmt_titulo)
        ws_dash.merge_range("A2:F2", f"  Embarcação: {barco_nome}  |  Armador: {armador_nome}", fmt_subtitulo)
        ws_dash.set_row(0, 28)
        ws_dash.set_row(1, 20)

        # Blocos de KPIs (Linhas 4 e 5)
        kpis = [
            ("A", "PESO TOTAL", f"{total_kg:,.1f} kg"),
            ("B", "TOTAL DE PEÇAS", f"{total_pecas}"),
            ("C", "PESO MÉDIO", f"{peso_medio:.2f} kg"),
            ("D", "% EXPORTAÇÃO (40+)", f"{perc_export:.1f}%"),
            ("E", "PEÇAS 2º FURO", f"{qtd_furo} ({perc_furo:.1f}%)")
        ]
        for col_letra, titulo, valor in kpis:
            ws_dash.write(f"{col_letra}4", titulo, fmt_kpi_label)
            ws_dash.write(f"{col_letra}5", valor, fmt_kpi_val)
        ws_dash.set_row(4, 24)

        # Quadro Sintético de Fechamento (Inicia na Linha 7)
        ws_dash.merge_range("A7:F7", "Quadro Sintético por Faixa de Calibre", fmt_sec_header)
        headers_resumo = ["Calibre", "Peças", "Peso Total (kg)", "Peso Médio (kg)", "Com 2º Furo", "Participação"]
        for col_idx, h in enumerate(headers_resumo):
            ws_dash.write(7, col_idx, h, fmt_th)

        start_row = 8
        for idx, r in df_resumo.iterrows():
            row_num = start_row + idx
            ws_dash.write(row_num, 0, r["calibre"], fmt_td_str)
            ws_dash.write(row_num, 1, int(r["Pecas"]), fmt_td_int)
            ws_dash.write(row_num, 2, float(r["Peso_Total_Kg"]), fmt_td_kg)
            ws_dash.write(row_num, 3, float(r["Peso_Medio_Kg"]), fmt_td_kg)
            ws_dash.write(row_num, 4, int(r["Com_2_Furo"]), fmt_td_int)
            ws_dash.write(row_num, 5, float(r["Part_%"]) / 100.0, fmt_td_pct)

        end_row = start_row + len(df_resumo) - 1

        # Gráfico Nativo 1: Colunas (Volume por Calibre)
        chart_col = workbook.add_chart({"type": "column"})
        chart_col.add_series({
            "name": "Peso Total (kg)",
            "categories": ["Painel Gerencial", start_row, 0, end_row, 0],
            "values": ["Painel Gerencial", start_row, 2, end_row, 2],
            "fill": {"color": "#0284C7"},
            "data_labels": {"value": True}
        })
        chart_col.set_title({"name": "Volume por Calibre (kg)"})
        chart_col.set_legend({"none": True})
        chart_col.set_size({"width": 480, "height": 280})
        ws_dash.insert_chart("A15", chart_col)

        # Gráfico Nativo 2: Rosca (Participação por Calibre)
        chart_pie = workbook.add_chart({"type": "doughnut"})
        chart_pie.add_series({
            "name": "Participação por Calibre",
            "categories": ["Painel Gerencial", start_row, 0, end_row, 0],
            "values": ["Painel Gerencial", start_row, 2, end_row, 2],
            "data_labels": {"percentage": True}
        })
        chart_pie.set_title({"name": "Distribuição % por Calibre"})
        chart_pie.set_size({"width": 420, "height": 280})
        ws_dash.insert_chart("D15", chart_pie)

        # --- ABA 2: ROMANEIO ANALÍTICO (TABELA OFICIAL DO EXCEL) ---
        df_export = df_lote[[
            "id_lote", "barco", "armador", "numero_peca",
            "peso_kg", "calibre", "segundo_furo", "destino", "data_hora"
        ]].copy()
        df_export.columns = [
            "Lote", "Embarcação", "Armador", "Nº Peça",
            "Peso (kg)", "Calibre", "2º Furo", "Destino", "Data/Hora"
        ]

        df_export.to_excel(writer, sheet_name="Romaneio Analítico", index=False)
        ws_rom = writer.sheets["Romaneio Analítico"]

        max_row, max_col = df_export.shape
        ws_rom.add_table(0, 0, max_row, max_col - 1, {
            "columns": [{"header": col} for col in df_export.columns],
            "style": "Table Style Medium 2",
            "name": f"Romaneio_Lote_{lote_selecionado}"
        })
        ws_rom.set_column("A:D", 14)
        ws_rom.set_column("E:E", 14)
        ws_rom.set_column("F:H", 22)
        ws_rom.set_column("I:I", 20)

    return output.getvalue()


# --- BOTÕES DE EXPORTAÇÃO LADO A LADO PARA AVALIAÇÃO ---
st.subheader("📥 Exportação do Romaneio & Dashboard")
st.caption("Teste e compare os três formatos abaixo para definir o padrão oficial da operação:")

col_btn1, col_btn2, col_btn3 = st.columns(3)

with col_btn1:
    html_bytes = gerar_dashboard_html(df, resumo_calibre)
    st.download_button(
        label="🌐 Dashboard Interativo (.HTML)",
        data=html_bytes,
        file_name=f"dashboard_lote_{lote_selecionado}.html",
        mime="text/html",
        type="primary",
        use_container_width=True
    )

with col_btn2:
    excel_bytes = gerar_excel_executivo(df, resumo_calibre)
    st.download_button(
        label="📊 Excel Executivo (.XLSX)",
        data=excel_bytes,
        file_name=f"painel_romaneio_lote_{lote_selecionado}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
        use_container_width=True
    )

with col_btn3:
    csv_bi = df.to_csv(index=False, sep=";").encode("utf-8-sig")
    st.download_button(
        label="💾 CSV Bruto (.CSV)",
        data=csv_bi,
        file_name=f"romaneio_bi_lote_{lote_selecionado}.csv",
        mime="text/csv",
        use_container_width=True
    )
