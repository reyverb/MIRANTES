from pathlib import Path
import io
import sqlite3
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st
from PIL import Image


# ============================================================
# CAMINHOS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "porto_atum.db"
LOGO_PATH = BASE_DIR / "logo.png"


# ============================================================
# LOGO
# ============================================================

try:
    logo = Image.open(LOGO_PATH)
except Exception:
    logo = None


# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================

st.set_page_config(
    page_title="Painel Gerencial | NAVIMAR",
    page_icon=logo if logo is not None else "⚓",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>
        @import url(
            'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap'
        );

        :root {
            --navy: #08263d;
            --blue: #1479a8;
            --blue-dark: #0b587d;
            --blue-light: #e7f4fa;
            --aqua: #18a6a6;
            --gold: #d5a94f;
            --text: #183243;
            --muted: #607786;
            --border: #c9d9df;
            --white: #ffffff;
            --cream: #fffaf0;
            --success: #087443;
        }

        html, body, [class*="css"] {
            font-family: "Inter", sans-serif;
        }

        .stApp,
        [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(
                    circle at top right,
                    rgba(20, 121, 168, 0.08),
                    transparent 30%
                ),
                linear-gradient(
                    180deg,
                    #f7fbfc 0%,
                    #eaf4f4 100%
                ) !important;
            color: var(--text) !important;
        }

        [data-testid="stHeader"] {
            background: rgba(255, 255, 255, 0.85) !important;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(
                180deg,
                #041827,
                #08263d
            ) !important;
        }

        [data-testid="stSidebar"] * {
            color: #ffffff !important;
        }

        .block-container {
            max-width: 1450px;
            padding-top: 1.5rem;
            padding-bottom: 3rem;
        }

        h1, h2, h3, h4, h5, h6 {
            color: var(--navy) !important;
            font-weight: 800 !important;
            letter-spacing: -0.03em;
        }

        p, label {
            color: var(--text) !important;
        }

        .main-title {
            color: var(--navy) !important;
            font-size: clamp(2rem, 4vw, 3rem);
            font-weight: 800;
            letter-spacing: -0.05em;
            margin-bottom: 0.2rem;
        }

        .page-subtitle {
            color: var(--muted) !important;
            font-size: 1rem;
            margin-bottom: 1.25rem;
        }

        .section-title {
            color: var(--navy) !important;
            font-size: 1.3rem;
            font-weight: 800;
            margin: 0.7rem 0 0.8rem 0;
        }

        .lote-header {
            background: linear-gradient(
                135deg,
                #0b587d,
                #1479a8
            ) !important;
            border-radius: 18px;
            padding: 1.2rem 1.4rem;
            margin: 0.8rem 0 1.2rem 0;
            box-shadow: 0 10px 28px rgba(8, 38, 61, 0.16);
        }

        .lote-header h2,
        .lote-header p {
            color: #ffffff !important;
            margin: 0;
        }

        .lote-header h2 {
            font-size: 1.45rem;
            margin-bottom: 0.3rem;
        }

        .lote-header p {
            opacity: 0.9;
            font-size: 0.9rem;
        }

        .metric-card {
            background: #ffffff !important;
            border: 1px solid var(--border);
            border-left: 5px solid var(--blue);
            border-radius: 16px;
            padding: 1rem 1.05rem;
            min-height: 112px;
            box-shadow: 0 8px 24px rgba(8, 38, 61, 0.08);
        }

        .metric-label {
            color: var(--muted) !important;
            font-size: 0.75rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.055em;
        }

        .metric-value {
            color: var(--navy) !important;
            font-size: 1.55rem;
            font-weight: 800;
            margin-top: 0.45rem;
        }

        .metric-helper {
            color: var(--muted) !important;
            font-size: 0.78rem;
            margin-top: 0.25rem;
        }

        .summary-card {
            background: #ffffff !important;
            border: 1px solid var(--border);
            border-radius: 18px;
            padding: 1.2rem;
            box-shadow: 0 8px 24px rgba(8, 38, 61, 0.07);
        }

        .summary-card h3 {
            margin-top: 0;
            color: var(--navy) !important;
        }

        .filter-card {
            background: #ffffff !important;
            border: 1px solid var(--border) !important;
            border-radius: 16px !important;
            padding: 1rem !important;
            margin-bottom: 0.8rem !important;
            box-shadow: 0 6px 18px rgba(8, 38, 61, 0.06) !important;
        }

        .filter-card label {
            color: var(--text) !important;
            font-weight: 700 !important;
        }

        /* =====================================================
           BOTÕES
        ===================================================== */

        .stButton > button,
        .stDownloadButton > button,
        .stFormSubmitButton > button {
            outline: none !important;
            filter: none !important;
            text-shadow: none !important;
            box-shadow: none !important;
            transition:
                background-color 0.16s ease,
                border-color 0.16s ease,
                transform 0.16s ease;
        }

        .stButton > button {
            background: var(--navy) !important;
            color: #ffffff !important;
            border: 1px solid var(--navy) !important;
        }

        .stButton > button:hover {
            background: var(--blue) !important;
            color: #ffffff !important;
            border-color: var(--blue) !important;
            transform: translateY(-1px);
        }

        .stButton > button:focus,
        .stButton > button:focus-visible,
        .stButton > button:active {
            outline: none !important;
            box-shadow: none !important;
        }

        .stDownloadButton > button {
            background: var(--cream) !important;
            color: var(--navy) !important;
            border: 1px solid var(--gold) !important;
        }

        .stDownloadButton > button:hover {
            background: #fff3d6 !important;
            color: var(--navy) !important;
            border-color: #bd8b23 !important;
        }

        /* =====================================================
           ABAS
        ===================================================== */

        .stTabs [data-baseweb="tab-list"] {
            display: flex !important;
            gap: 0.45rem !important;
            background: #edf5f7 !important;
            border: 1px solid var(--border) !important;
            padding: 0.35rem !important;
            border-radius: 12px !important;
            box-shadow: none !important;
        }

        .stTabs [data-baseweb="tab"] {
            height: 2.55rem !important;
            padding: 0 1rem !important;
            border-radius: 9px !important;
            background: transparent !important;
            color: #365466 !important;
            font-weight: 700 !important;
            box-shadow: none !important;
            outline: none !important;
        }

        .stTabs [data-baseweb="tab"]:hover {
            background: #dcecf2 !important;
            color: var(--navy) !important;
        }

        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background: var(--blue) !important;
            color: #ffffff !important;
            box-shadow: none !important;
        }

        .stTabs [data-baseweb="tab-highlight"],
        .stTabs [data-baseweb="tab-border"] {
            display: none !important;
        }

        /* =====================================================
           FILTROS
        ===================================================== */

        [data-baseweb="select"] > div {
            background: #ffffff !important;
            color: var(--text) !important;
            border: 1px solid #9db5c0 !important;
            border-radius: 10px !important;
            box-shadow: none !important;
        }

        [data-baseweb="select"] input {
            color: var(--text) !important;
            background: #ffffff !important;
        }

        [data-baseweb="select"] [data-baseweb="tag"] {
            background: var(--blue-light) !important;
            border: 1px solid #a8cfdd !important;
            color: var(--navy) !important;
        }

        [data-baseweb="select"] [data-baseweb="tag"] span {
            color: var(--navy) !important;
        }

        [data-baseweb="select"] svg {
            fill: var(--navy) !important;
        }

        [role="listbox"],
        [data-baseweb="menu"] {
            background: #ffffff !important;
            border: 1px solid var(--border) !important;
            color: var(--text) !important;
            box-shadow: 0 8px 22px rgba(8, 38, 61, 0.14) !important;
        }

        [role="option"] {
            background: #ffffff !important;
            color: var(--text) !important;
        }

        [role="option"]:hover,
        [aria-selected="true"] {
            background: var(--blue-light) !important;
            color: var(--navy) !important;
        }

        [data-baseweb="select"] > div:focus-within {
            border-color: var(--blue) !important;
            box-shadow: 0 0 0 2px rgba(20, 121, 168, 0.14) !important;
        }

        /* =====================================================
           TABELAS
        ===================================================== */

        [data-testid="stDataFrame"] {
            background: #ffffff !important;
            border: 1px solid var(--border) !important;
            border-radius: 12px !important;
            overflow: hidden !important;
        }

        [data-testid="stDataFrame"] iframe {
            background: #ffffff !important;
        }

        button:focus,
        button:focus-visible,
        input:focus,
        input:focus-visible,
        [data-baseweb="tab"]:focus,
        [data-baseweb="tab"]:focus-visible {
            outline: none !important;
        }

        [data-baseweb="tab-list"]::before,
        [data-baseweb="tab-list"]::after {
            display: none !important;
        }

        hr {
            border: none;
            border-top: 1px solid rgba(96, 119, 134, 0.24);
            margin: 1.45rem 0;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# FUNÇÕES
# ============================================================

def metric_card(label, value, helper="", accent="#1479a8"):
    st.markdown(
        f"""
        <div class="metric-card" style="border-left-color: {accent};">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-helper">{helper}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def format_date(value):
    try:
        return datetime.strptime(
            str(value)[:10],
            "%Y-%m-%d",
        ).strftime("%d/%m/%Y")
    except Exception:
        return str(value)


def ensure_lombo_column(dataframe):
    dataframe = dataframe.copy()

    if "lombo" not in dataframe.columns:
        dataframe["lombo"] = "Não"

    return dataframe


def build_financial_dataframe(dataframe, prices):
    dataframe = ensure_lombo_column(dataframe)

    df_furo = dataframe[
        dataframe["segundo_furo"] == "Sim"
    ]

    df_lombo = dataframe[
        (dataframe["lombo"] == "Sim")
        & (dataframe["segundo_furo"] == "Não")
    ]

    df_normal = dataframe[
        (dataframe["segundo_furo"] == "Não")
        & (dataframe["lombo"] == "Não")
    ]

    kg_15_24 = df_normal[
        df_normal["peso"].isin(
            ["15-24kg", "15–24 kg"]
        )
    ]["peso_kg"].sum()

    kg_25_39 = df_normal[
        df_normal["peso"].isin(
            ["25-39kg", "25–39 kg"]
        )
    ]["peso_kg"].sum()

    kg_40 = df_normal[
        df_normal["peso"].isin(
            [
                "40+kg (Exportação)",
                "40+ kg · Exportação",
            ]
        )
    ]["peso_kg"].sum()

    kg_furo = df_furo["peso_kg"].sum()
    kg_lombo = df_lombo["peso_kg"].sum()

    rows = [
        ("15KG - 24KG", kg_15_24, prices["15_24"]),
        ("25KG - 39KG", kg_25_39, prices["25_39"]),
        ("40KG ACIMA", kg_40, prices["40_up"]),
        ("2º FURO", kg_furo, prices["furo"]),
        ("LOMBO", kg_lombo, prices["lombo"]),
    ]

    result = []

    for category, kilograms, price in rows:
        result.append(
            {
                "TIPO (ATUM)": category,
                "KG": float(kilograms),
                "PREÇO (R$)": float(price),
                "TOTAL": float(kilograms * price),
            }
        )

    total_kg = sum(row["KG"] for row in result)
    total_value = sum(row["TOTAL"] for row in result)

    result.append(
        {
            "TIPO (ATUM)": "TOTAL",
            "KG": total_kg,
            "PREÇO (R$)": 0.0,
            "TOTAL": total_value,
        }
    )

    return pd.DataFrame(result)


def get_database():
    connection = sqlite3.connect(
        DB_PATH,
        check_same_thread=False,
    )

    connection.execute("PRAGMA journal_mode=WAL;")

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS descargas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barco TEXT NOT NULL,
            proprietario TEXT NOT NULL,
            data_hora TEXT NOT NULL,
            status TEXT DEFAULT 'Em Andamento'
        )
        """
    )

    connection.commit()
    return connection


# ============================================================
# BANCO
# ============================================================

conn = get_database()


# ============================================================
# CABEÇALHO
# ============================================================

st.page_link(
    "app.py",
    label="Voltar para a pesagem no cais",
    icon="🐟",
)

st.markdown(
    '<div class="main-title">📊 Painel gerencial</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="page-subtitle">'
    'Acompanhe produção, classificação, romaneio e resultados financeiros por lote.'
    '</div>',
    unsafe_allow_html=True,
)


# ============================================================
# DESCARGAS
# ============================================================

descargas = pd.read_sql(
    """
    SELECT id, barco, proprietario, data_hora, status
    FROM descargas
    ORDER BY id DESC
    """,
    conn,
)

if descargas.empty:
    st.info("Nenhuma descarga encontrada no banco de dados.")
    st.stop()

opcoes = {
    int(row["id"]): (
        f"Lote #{int(row['id'])} · {row['barco']} · "
        f"{row['status']} · {str(row['data_hora'])[:10]}"
    )
    for _, row in descargas.iterrows()
}

lote_selecionado = st.selectbox(
    "Selecione o lote ou embarcação",
    options=list(opcoes.keys()),
    format_func=lambda value: opcoes[value],
)


# ============================================================
# CONSULTA
# ============================================================

query_analitica = """
    SELECT
        d.id AS id_lote,
        d.barco,
        d.proprietario AS armador,
        d.status,
        d.data_hora AS data_descarga,
        p.numero_peca,
        p.peso_kg,
        p.categoria AS peso,

        CASE
            WHEN p.peso_kg >= 40.0 THEN 1
            ELSE 0
        END AS is_exportacao,

        CASE
            WHEN p.segundo_furo = 1 THEN 'Sim'
            ELSE 'Não'
        END AS segundo_furo,

        CASE
            WHEN p.lombo = 1 THEN 'Sim'
            ELSE 'Não'
        END AS lombo,

        p.destino,
        p.data_registro AS data_hora
    FROM pecas p
    JOIN descargas d
        ON d.id = p.id_descarga
    WHERE p.id_descarga = ?
    ORDER BY p.numero_peca ASC
"""

try:
    df = pd.read_sql(
        query_analitica,
        conn,
        params=(int(lote_selecionado),),
    )
except Exception:
    query_fallback = """
        SELECT
            d.id AS id_lote,
            d.barco,
            d.proprietario AS armador,
            d.status,
            d.data_hora AS data_descarga,
            p.numero_peca,
            p.peso_kg,
            p.categoria AS peso,

            CASE
                WHEN p.peso_kg >= 40.0 THEN 1
                ELSE 0
            END AS is_exportacao,

            CASE
                WHEN p.segundo_furo = 1 THEN 'Sim'
                ELSE 'Não'
            END AS segundo_furo,

            'Não' AS lombo,
            p.destino,
            p.data_registro AS data_hora
        FROM pecas p
        JOIN descargas d
            ON d.id = p.id_descarga
        WHERE p.id_descarga = ?
        ORDER BY p.numero_peca ASC
    """

    df = pd.read_sql(
        query_fallback,
        conn,
        params=(int(lote_selecionado),),
    )

if df.empty:
    st.warning("Este lote ainda não possui peças registradas.")
    st.stop()

df = ensure_lombo_column(df)


# ============================================================
# CABEÇALHO DO LOTE
# ============================================================

barco_nome = str(df["barco"].iloc[0])
armador_nome = str(df["armador"].iloc[0])
status_lote = str(df["status"].iloc[0])

st.markdown(
    f"""
    <div class="lote-header">
        <h2>🚢 {barco_nome}</h2>
        <p>
            Armador: {armador_nome}
            &nbsp; · &nbsp;
            Lote #{int(lote_selecionado)}
            &nbsp; · &nbsp;
            {status_lote}
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# ABAS
# ============================================================

tab_gerencial, tab_romaneio = st.tabs(
    [
        "📊 Visão geral",
        "📄 Romaneio comercial",
    ]
)


# ============================================================
# VISÃO GERAL
# ============================================================

with tab_gerencial:
    total_kg = float(df["peso_kg"].sum())
    total_pecas = len(df)
    peso_medio = float(df["peso_kg"].mean())

    peso_export = float(
        df.loc[
            df["is_exportacao"] == 1,
            "peso_kg",
        ].sum()
    )

    perc_export = (
        peso_export / total_kg * 100
        if total_kg > 0
        else 0
    )

    qtd_furo = int(
        (df["segundo_furo"] == "Sim").sum()
    )

    perc_furo = (
        qtd_furo / total_pecas * 100
        if total_pecas > 0
        else 0
    )

    qtd_lombo = int(
        (df["lombo"] == "Sim").sum()
    )

    metrics = st.columns(5)

    with metrics[0]:
        metric_card(
            "Peso total",
            f"{total_kg:,.1f} kg",
            "Volume registrado",
            "#1479a8",
        )

    with metrics[1]:
        metric_card(
            "Total de peças",
            f"{total_pecas:,}",
            "Peças lançadas",
            "#18a6a6",
        )

    with metrics[2]:
        metric_card(
            "Média por peça",
            f"{peso_medio:,.2f} kg",
            "Peso médio",
            "#d5a94f",
        )

    with metrics[3]:
        metric_card(
            "Exportação",
            f"{perc_export:.1f}%",
            f"{peso_export:,.1f} kg acima de 40 kg",
            "#087443",
        )

    with metrics[4]:
        metric_card(
            "Lombo / 2º furo",
            f"{qtd_lombo:,} / {qtd_furo:,}",
            f"{perc_furo:.1f}% com 2º furo",
            "#b76e11",
        )

    st.markdown("<br>", unsafe_allow_html=True)

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.markdown(
            '<div class="section-title">'
            '📈 Evolução peça a peça'
            '</div>',
            unsafe_allow_html=True,
        )

        fig_scatter = px.scatter(
            df,
            x="numero_peca",
            y="peso_kg",
            color="peso",
            symbol="segundo_furo",
            hover_data=[
                "destino",
                "lombo",
                "data_hora",
            ],
            labels={
                "numero_peca": "Número da peça",
                "peso_kg": "Peso (kg)",
                "peso": "Classificação",
                "segundo_furo": "2º furo",
            },
            color_discrete_sequence=[
                "#1479a8",
                "#18a6a6",
                "#d5a94f",
                "#08263d",
            ],
        )

        fig_scatter.update_traces(
            marker=dict(
                size=11,
                line=dict(
                    width=1,
                    color="#ffffff",
                ),
            )
        )

        fig_scatter.update_layout(
            template="plotly_white",
            paper_bgcolor="#ffffff",
            plot_bgcolor="#ffffff",
            font=dict(
                family="Inter, Arial, sans-serif",
                color="#183243",
            ),
            legend=dict(
                bgcolor="rgba(255,255,255,0.9)",
                bordercolor="#c9d9df",
                borderwidth=1,
                font=dict(color="#183243"),
            ),
            xaxis=dict(
                title_font=dict(color="#08263d"),
                tickfont=dict(color="#183243"),
                gridcolor="#dbe7eb",
                linecolor="#9db5c0",
            ),
            yaxis=dict(
                title_font=dict(color="#08263d"),
                tickfont=dict(color="#183243"),
                gridcolor="#dbe7eb",
                linecolor="#9db5c0",
            ),
            height=390,
            margin=dict(t=25, b=35, l=25, r=20),
        )

        st.plotly_chart(
            fig_scatter,
            use_container_width=True,
        )

    with chart_col2:
        st.markdown(
            '<div class="section-title">'
            '🎯 Distribuição por destino'
            '</div>',
            unsafe_allow_html=True,
        )

        df_destino = (
            df.groupby(
                "destino",
                as_index=False,
            )["peso_kg"]
            .sum()
            .sort_values(
                "peso_kg",
                ascending=False,
            )
        )

        fig_pie = px.pie(
            df_destino,
            names="destino",
            values="peso_kg",
            hole=0.55,
            labels={
                "destino": "Destino",
                "peso_kg": "Peso (kg)",
            },
            color_discrete_sequence=[
                "#1479a8",
                "#18a6a6",
                "#d5a94f",
                "#08263d",
            ],
        )

        fig_pie.update_traces(
            textposition="inside",
            textinfo="percent+label",
            marker=dict(
                line=dict(
                    color="#ffffff",
                    width=2,
                )
            ),
        )

        fig_pie.update_layout(
            template="plotly_white",
            paper_bgcolor="#ffffff",
            plot_bgcolor="#ffffff",
            font=dict(
                family="Inter, Arial, sans-serif",
                color="#183243",
            ),
            legend=dict(
                bgcolor="rgba(255,255,255,0.9)",
                bordercolor="#c9d9df",
                borderwidth=1,
                font=dict(color="#183243"),
            ),
            height=390,
            margin=dict(t=25, b=25, l=20, r=20),
        )

        st.plotly_chart(
            fig_pie,
            use_container_width=True,
        )

    st.markdown("---")

    st.markdown(
        '<div class="section-title">'
        '📦 Fechamento por categoria'
        '</div>',
        unsafe_allow_html=True,
    )

    resumo_peso = (
        df.groupby("peso")
        .agg(
            Pecas=("numero_peca", "count"),
            Peso_Total_Kg=("peso_kg", "sum"),
            Peso_Medio_Kg=("peso_kg", "mean"),
            Com_2_Furo=(
                "segundo_furo",
                lambda values: (
                    values == "Sim"
                ).sum(),
            ),
            Com_Lombo=(
                "lombo",
                lambda values: (
                    values == "Sim"
                ).sum(),
            ),
        )
        .reset_index()
    )

    resumo_peso["Part_%"] = (
        resumo_peso["Peso_Total_Kg"]
        / total_kg
        * 100
        if total_kg > 0
        else 0
    )

    st.dataframe(
        resumo_peso,
        column_config={
            "peso": st.column_config.TextColumn(
                "Faixa de peso"
            ),
            "Pecas": st.column_config.NumberColumn(
                "Peças"
            ),
            "Peso_Total_Kg": st.column_config.NumberColumn(
                "Peso total",
                format="%.2f kg",
            ),
            "Peso_Medio_Kg": st.column_config.NumberColumn(
                "Média",
                format="%.2f kg",
            ),
            "Com_2_Furo": st.column_config.NumberColumn(
                "2º furo"
            ),
            "Com_Lombo": st.column_config.NumberColumn(
                "Lombo"
            ),
            "Part_%": st.column_config.NumberColumn(
                "Participação",
                format="%.1f%%",
            ),
        },
        hide_index=True,
        use_container_width=True,
    )

    st.markdown("---")

    st.markdown(
        '<div class="section-title">'
        '🧾 Peças do lote'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="filter-card">',
        unsafe_allow_html=True,
    )

    filtro_col1, filtro_col2 = st.columns(2)

    with filtro_col1:
        filtro_peso = st.multiselect(
            "Filtrar por faixa de peso",
            options=sorted(
                df["peso"].dropna().unique().tolist()
            ),
            placeholder="Selecione uma ou mais faixas",
            key="filtro_peso_dashboard",
        )

    with filtro_col2:
        filtro_destino = st.multiselect(
            "Filtrar por destino",
            options=sorted(
                df["destino"].dropna().unique().tolist()
            ),
            placeholder="Selecione um ou mais destinos",
            key="filtro_destino_dashboard",
        )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )

    df_visual = df.copy()

    if filtro_peso:
        df_visual = df_visual[
            df_visual["peso"].isin(filtro_peso)
        ]

    if filtro_destino:
        df_visual = df_visual[
            df_visual["destino"].isin(filtro_destino)
        ]

    st.dataframe(
        df_visual[
            [
                "numero_peca",
                "peso_kg",
                "peso",
                "segundo_furo",
                "lombo",
                "destino",
                "data_hora",
            ]
        ],
        column_config={
            "numero_peca": st.column_config.NumberColumn(
                "Nº"
            ),
            "peso_kg": st.column_config.NumberColumn(
                "Peso",
                format="%.2f kg",
            ),
            "peso": st.column_config.TextColumn(
                "Classificação"
            ),
            "segundo_furo": st.column_config.TextColumn(
                "2º furo"
            ),
            "lombo": st.column_config.TextColumn(
                "Lombo"
            ),
            "destino": st.column_config.TextColumn(
                "Destino"
            ),
            "data_hora": st.column_config.TextColumn(
                "Registro"
            ),
        },
        hide_index=True,
        use_container_width=True,
    )


# ============================================================
# ROMANEIO COMERCIAL
# ============================================================

with tab_romaneio:
    st.markdown(
        '<div class="section-title">'
        '📄 Romaneio de descarga'
        '</div>',
        unsafe_allow_html=True,
    )

    info_col1, info_col2 = st.columns([1, 3])

    with info_col1:
        if logo is not None:
            st.image(logo, width=190)
        else:
            st.markdown(
                '<div class="section-title">'
                'NAVIMAR PESCADOS'
                '</div>',
                unsafe_allow_html=True,
            )

    with info_col2:
        st.markdown(
            f"""
            <div class="summary-card">
                <h3>Dados comerciais</h3>
                <p><strong>BARCO:</strong> {barco_nome}</p>
                <p><strong>PROPRIETÁRIO:</strong> {armador_nome}</p>
                <p><strong>COMPRADOR:</strong> NAVIMAR PESCADOS</p>
                <p><strong>DATA:</strong> {
                    format_date(df["data_hora"].iloc[0])
                }</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    st.markdown(
        '<div class="section-title">'
        '💰 Tabela de preços'
        '</div>',
        unsafe_allow_html=True,
    )

    price_cols = st.columns(5)

    with price_cols[0]:
        preco_15_24 = st.number_input(
            "15–24 kg · R$",
            min_value=0.0,
            value=25.00,
            step=1.00,
            format="%.2f",
            key="preco_15_24",
        )

    with price_cols[1]:
        preco_25_39 = st.number_input(
            "25–39 kg · R$",
            min_value=0.0,
            value=29.00,
            step=1.00,
            format="%.2f",
            key="preco_25_39",
        )

    with price_cols[2]:
        preco_40 = st.number_input(
            "40 kg ou mais · R$",
            min_value=0.0,
            value=32.00,
            step=1.00,
            format="%.2f",
            key="preco_40",
        )

    with price_cols[3]:
        preco_furo = st.number_input(
            "2º furo · R$",
            min_value=0.0,
            value=21.00,
            step=1.00,
            format="%.2f",
            key="preco_furo",
        )

    with price_cols[4]:
        preco_lombo = st.number_input(
            "Lombo · R$",
            min_value=0.0,
            value=15.00,
            step=1.00,
            format="%.2f",
            key="preco_lombo",
        )

    tabela_precos = {
        "15_24": preco_15_24,
        "25_39": preco_25_39,
        "40_up": preco_40,
        "furo": preco_furo,
        "lombo": preco_lombo,
    }

    df_romaneio = build_financial_dataframe(
        df,
        tabela_precos,
    )

    total_kg_comercial = df_romaneio.iloc[-1]["KG"]
    total_valor = df_romaneio.iloc[-1]["TOTAL"]

    total_cols = st.columns(2)

    with total_cols[0]:
        metric_card(
            "Peso comercial",
            f"{total_kg_comercial:,.2f} kg",
            "Base do romaneio",
            "#1479a8",
        )

    with total_cols[1]:
        metric_card(
            "Valor estimado",
            f"R$ {total_valor:,.2f}",
            "Conforme preços informados",
            "#18a6a6",
        )

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown(
        '<div class="section-title">'
        'Resultado do romaneio'
        '</div>',
        unsafe_allow_html=True,
    )

    st.dataframe(
        df_romaneio,
        column_config={
            "TIPO (ATUM)": st.column_config.TextColumn(
                "Tipo de atum"
            ),
            "KG": st.column_config.NumberColumn(
                "Peso",
                format="%.2f kg",
            ),
            "PREÇO (R$)": st.column_config.NumberColumn(
                "Preço por kg",
                format="R$ %.2f",
            ),
            "TOTAL": st.column_config.NumberColumn(
                "Total",
                format="R$ %.2f",
            ),
        },
        hide_index=True,
        use_container_width=True,
    )


# ============================================================
# PDF - RELATÓRIO DE DESCARGA (NOVO LAYOUT NAVIMAR)
# ============================================================

def gerar_dashboard_pdf(
    df_lote,
    df_resumo,
    df_financeiro,
    logo_path,
):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.colors import HexColor, white
    from io import BytesIO

    NAVY = HexColor("#0B2545")
    METAL = HexColor("#4F7CAC")
    LINE = HexColor("#E6EAF0")
    SLATE = HexColor("#5B6573")
    LIGHT = HexColor("#A3ABB7")
    SHADOW = HexColor("#E9EDF3")
    CARD = HexColor("#FFFFFF")

    W, H = A4
    m = 40
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    barco = str(df_lote["barco"].iloc[0])
    armador = str(df_lote["armador"].iloc[0])
    data_lote = format_date(df_lote["data_hora"].iloc[0])

    total_kg = float(df_lote["peso_kg"].sum())
    total_pecas = int(len(df_lote))
    peso_medio = total_kg / total_pecas if total_pecas > 0 else 0

    # ---------- CABEÇALHO ----------
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 26)
    c.drawString(m, H - m - 18, "NAVIMAR")
    c.setFillColor(METAL)
    c.rect(m, H - m - 27, 34, 2.5, stroke=0, fill=1)

    c.setFillColor(SLATE)
    c.setFont("Helvetica", 8.5)
    for i, t in enumerate([f"Barco: {barco}", f"Proprietário: {armador}", f"Data: {data_lote}"]):
        c.drawRightString(W - m, H - m - 8 - i * 12, t)

    c.setStrokeColor(LINE)
    c.setLineWidth(0.8)
    c.line(m, H - m - 42, W - m, H - m - 42)

    # ---------- TÍTULO ----------
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(m, H - 130, "Relatório de Descarga")

    # ---------- RESUMO OPERACIONAL (KPI CARDS) ----------
    c.setFillColor(METAL)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(m, H - 160, "RESUMO OPERACIONAL")

    gap = 14
    cw = (W - 2 * m - 2 * gap) / 3
    ch = 74
    top = H - 176

    for i, (lab, val) in enumerate([("PESO TOTAL", f"{total_kg:.1f} kg"),
                                     ("PEÇAS", str(total_pecas)),
                                     ("MÉDIA POR PEÇA", f"{peso_medio:.2f} kg")]):
        x = m + i * (cw + gap)
        y = top - ch

        # sombra suave
        c.setFillColor(SHADOW)
        c.roundRect(x + 1.5, y - 3, cw, ch, 10, stroke=0, fill=1)
        c.setFillColor(HexColor("#F1F4F8"))
        c.roundRect(x + 0.8, y - 1.5, cw, ch, 10, stroke=0, fill=1)

        # cartão
        c.setFillColor(CARD)
        c.setStrokeColor(LINE)
        c.setLineWidth(0.6)
        c.roundRect(x, y, cw, ch, 10, stroke=1, fill=1)

        # detalhe metálico
        c.setFillColor(METAL)
        c.roundRect(x + 14, y + ch - 14, 18, 2.5, 1, stroke=0, fill=1)

        # rótulo e valor
        c.setFillColor(SLATE)
        c.setFont("Helvetica", 7.5)
        c.drawString(x + 14, y + ch - 28, lab)
        c.setFillColor(NAVY)
        c.setFont("Helvetica-Bold", 24)
        c.drawString(x + 14, y + 16, val)

    # ---------- RESUMO COMERCIAL (TABELA) ----------
    y = top - ch - 40
    c.setFillColor(METAL)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(m, y, "RESUMO COMERCIAL")
    y -= 16

    cols = [m + 4, m + 250, m + 365, W - m - 4]
    c.setFillColor(SLATE)
    c.setFont("Helvetica-Bold", 7.5)
    c.drawString(cols[0], y, "TIPO (ATUM)")
    c.drawRightString(cols[1], y, "KG")
    c.drawRightString(cols[2], y, "PREÇO (R$)")
    c.drawRightString(cols[3], y, "TOTAL")

    y -= 10
    c.setStrokeColor(NAVY)
    c.setLineWidth(0.9)
    c.line(m, y, W - m, y)

    rh = 30
    for _, row in df_financeiro.iloc[:-1].iterrows():
        tipo = row["TIPO (ATUM)"]
        kg = float(row["KG"])
        preco = float(row["PREÇO (R$)"])
        tot = float(row["TOTAL"])
        y -= rh
        c.setFillColor(NAVY)
        c.setFont("Helvetica-Bold", 9.5)
        c.drawString(cols[0], y + 10, tipo)

        c.setFont("Helvetica", 9.5)
        c.setFillColor(SLATE)
        c.drawRightString(cols[1], y + 10, f"{kg:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        c.drawRightString(cols[2], y + 10, f"{preco:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        c.drawRightString(cols[3], y + 10, f"R$ {tot:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

        c.setStrokeColor(LINE)
        c.setLineWidth(0.5)
        c.line(m, y, W - m, y)

    # linha TOTAL destacada
    total_row = df_financeiro.iloc[-1]
    y -= 8
    th = 34
    y -= th
    c.setFillColor(NAVY)
    c.roundRect(m, y, W - 2 * m, th, 6, stroke=0, fill=1)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 10.5)
    c.drawString(cols[0] + 6, y + 12, "TOTAL")
    c.drawRightString(cols[1], y + 12, f"{float(total_row['KG']):.2f}".replace(".", ","))
    c.drawRightString(cols[3] - 6, y + 12, ("R$ " + f"{float(total_row['TOTAL']):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")))

    # ---------- RODAPÉ ----------
    c.setFillColor(LIGHT)
    c.setFont("Helvetica", 7.5)
    c.drawCentredString(W / 2, 28, "Documento gerado pelo sistema NAVIMAR PESCADOS.")

    c.save()
    return buffer.getvalue()


# ============================================================
# EXCEL EXECUTIVO MODELO
# ============================================================

def gerar_excel_executivo(
    df_lote,
    prices,
    image_path,
):
    output = io.BytesIO()

    barco = str(
        df_lote["barco"].iloc[0]
    ).upper()

    armador = str(
        df_lote["armador"].iloc[0]
    ).upper()

    data_lote = format_date(
        df_lote["data_hora"].iloc[0]
    )

    df_financeiro = build_financial_dataframe(
        df_lote,
        prices,
    )

    with pd.ExcelWriter(
        output,
        engine="xlsxwriter",
    ) as writer:
        workbook = writer.book
        worksheet = workbook.add_worksheet(
            "Planilha1"
        )

        worksheet.hide_gridlines(2)

        worksheet.set_landscape()
        worksheet.fit_to_pages(1, 1)
        worksheet.set_margins(
            left=0.25,
            right=0.25,
            top=0.35,
            bottom=0.35,
        )

        worksheet.set_column("A:A", 3)
        worksheet.set_column("B:B", 20)
        worksheet.set_column("C:C", 22)
        worksheet.set_column("D:D", 18)
        worksheet.set_column("E:E", 18)

        for row in range(0, 15):
            worksheet.set_row(row, 21)

        fmt_label = workbook.add_format(
            {
                "bold": True,
                "font_size": 11,
                "font_color": "#08263d",
                "valign": "vcenter",
                "align": "left",
            }
        )

        fmt_value = workbook.add_format(
            {
                "bold": True,
                "font_size": 11,
                "font_color": "#183243",
                "valign": "vcenter",
                "align": "left",
            }
        )

        fmt_header = workbook.add_format(
            {
                "bold": True,
                "border": 1,
                "bg_color": "#08263d",
                "font_color": "#FFFFFF",
                "align": "center",
                "valign": "vcenter",
            }
        )

        fmt_text = workbook.add_format(
            {
                "border": 1,
                "align": "center",
                "font_color": "#183243",
                "valign": "vcenter",
            }
        )

        fmt_number = workbook.add_format(
            {
                "border": 1,
                "align": "center",
                "font_color": "#183243",
                "num_format": '#,##0.00 "kg"',
            }
        )

        fmt_money = workbook.add_format(
            {
                "border": 1,
                "align": "center",
                "font_color": "#183243",
                "num_format": 'R$ #,##0.00',
            }
        )

        fmt_total_text = workbook.add_format(
            {
                "border": 1,
                "bold": True,
                "bg_color": "#E7F4FA",
                "font_color": "#08263d",
                "align": "center",
            }
        )

        fmt_total_number = workbook.add_format(
            {
                "border": 1,
                "bold": True,
                "bg_color": "#E7F4FA",
                "font_color": "#08263d",
                "align": "center",
                "num_format": '#,##0.00 "kg"',
            }
        )

        fmt_total_money = workbook.add_format(
            {
                "border": 1,
                "bold": True,
                "bg_color": "#E7F4FA",
                "font_color": "#08263d",
                "align": "center",
                "num_format": 'R$ #,##0.00',
            }
        )

        # ====================================================
        # CABEÇALHO DO MODELO
        # ====================================================

        linha_cabecalho = 2

        informacoes = [
            ("BARCO:", barco),
            ("PROPRIETÁRIO:", armador),
            ("COMANDANTE:", ""),
            ("COMPRADOR:", "NAVIMAR PESCADOS"),
            ("DATA:", data_lote),
        ]

        for offset, (label, value) in enumerate(
            informacoes
        ):
            worksheet.write(
                linha_cabecalho + offset,
                1,
                label,
                fmt_label,
            )

            worksheet.write(
                linha_cabecalho + offset,
                2,
                value,
                fmt_value,
            )

        # Logo fora da tabela, mantendo proporção
        try:
            if Path(image_path).exists():
                worksheet.insert_image(
                    "E2",
                    str(image_path),
                    {
                        "x_scale": 0.22,
                        "y_scale": 0.22,
                        "x_offset": 6,
                        "y_offset": 4,
                        "positioning": 2,
                    },
                )
        except Exception:
            pass

        # ====================================================
        # TABELA COM A MESMA ORGANIZAÇÃO DA PLANILHA MODELO
        # ====================================================

        linha_tabela = 8

        headers = [
            "TIPO (ATUM)",
            "KG",
            "PREÇO (R$)",
            "TOTAL",
        ]

        for coluna, header in enumerate(
            headers,
            start=1,
        ):
            worksheet.write(
                linha_tabela,
                coluna,
                header,
                fmt_header,
            )

        linha_dados = linha_tabela + 1

        for _, row in df_financeiro.iloc[:-1].iterrows():
            worksheet.write(
                linha_dados,
                1,
                row["TIPO (ATUM)"],
                fmt_text,
            )

            worksheet.write(
                linha_dados,
                2,
                float(row["KG"]),
                fmt_number,
            )

            worksheet.write(
                linha_dados,
                3,
                float(row["PREÇO (R$)"]),
                fmt_money,
            )

            worksheet.write_formula(
                linha_dados,
                4,
                f"=C{linha_dados + 1}*D{linha_dados + 1}",
                fmt_money,
            )

            linha_dados += 1

        linha_total = linha_dados
        total = df_financeiro.iloc[-1]

        worksheet.write(
            linha_total,
            1,
            "TOTAL",
            fmt_total_text,
        )

        worksheet.write(
            linha_total,
            2,
            float(total["KG"]),
            fmt_total_number,
        )

        worksheet.write(
            linha_total,
            3,
            "-",
            fmt_total_text,
        )

        worksheet.write_formula(
            linha_total,
            4,
            f"=SUM(E{linha_tabela + 2}:E{linha_total})",
            fmt_total_money,
        )

        worksheet.print_area(
            0,
            0,
            linha_total,
            4,
        )

    return output.getvalue()


# ============================================================
# EXPORTAÇÕES
# ============================================================

st.markdown("---")

st.markdown(
    '<div class="section-title">'
    '📥 Exportação do relatório oficial'
    '</div>',
    unsafe_allow_html=True,
)

export_col1, export_col2, export_col3 = st.columns(3)

with export_col1:
    pdf_bytes = gerar_dashboard_pdf(
        df_lote=df,
        df_resumo=resumo_peso,
        df_financeiro=df_romaneio,
        logo_path=LOGO_PATH,
    )

    st.download_button(
        label="📄 Relatório executivo · PDF",
        data=pdf_bytes,
        file_name=(
            f"dashboard_lote_{barco_nome}.pdf"
        ),
        mime="application/pdf",
        use_container_width=True,
    )

with export_col2:
    excel_bytes = gerar_excel_executivo(
        df_lote=df,
        prices=tabela_precos,
        image_path=LOGO_PATH,
    )

    st.download_button(
        label="📊 Excel executivo · XLSX",
        data=excel_bytes,
        file_name=(
            f"Romaneio_Navimar_{barco_nome}.xlsx"
        ),
        mime=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        use_container_width=True,
    )

with export_col3:
    csv_data = df_romaneio.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        label="📥 Resumo comercial · CSV",
        data=csv_data,
        file_name=(
            f"resumo_comercial_{barco_nome}.csv"
        ),
        mime="text/csv",
        use_container_width=True,
    )
