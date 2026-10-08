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
# FUNÇÕES GERAIS
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


# ============================================================
# UTILITÁRIOS DE RELAÇÃO INDIVIDUAL E FINANCEIRO
# ============================================================

def formatar_numero_brasileiro(valor):
    """
    Exemplo: 5165.00 -> 5.165,00
    """
    return (
        f"{float(valor):,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def classificar_peca_relacao(row):
    """
    Classificação usada na Relação do Caminhão e Financeiro.
    """
    if str(row.get("segundo_furo", "Não")).strip() == "Sim":
        return "2º FURO"

    if str(row.get("lombo", "Não")).strip() == "Sim":
        return "LOMBO"

    categoria = str(row.get("peso", "")).strip()

    mapa_categorias = {
        "15-24kg": "15KG - 24KG",
        "15–24 kg": "15KG - 24KG",
        "15KG - 24KG": "15KG - 24KG",
        "25-39kg": "25KG - 39KG",
        "25–39 kg": "25KG - 39KG",
        "25KG - 39KG": "25KG - 39KG",
        "40+kg (Exportação)": "40KG ACIMA",
        "40+ kg · Exportação": "40KG ACIMA",
        "40KG ACIMA": "40KG ACIMA",
    }

    if categoria in mapa_categorias:
        return mapa_categorias[categoria]

    peso_kg = float(row["peso_kg"])

    if peso_kg >= 40:
        return "40KG ACIMA"

    if peso_kg >= 25:
        return "25KG - 39KG"

    return "15KG - 24KG"


def preparar_relacao_caminhao(df_lote):
    """
    Mantém uma linha por peixe. Não há consolidação de pesos.
    """
    df_relacao = ensure_lombo_column(df_lote).copy()

    df_relacao["CLASSIFICACAO_RELACAO"] = df_relacao.apply(
        classificar_peca_relacao,
        axis=1,
    )

    df_relacao["PESO_RELACAO"] = pd.to_numeric(
        df_relacao["peso_kg"],
        errors="coerce",
    ).fillna(0.0)

    df_relacao["NUMERO_PECA_RELACAO"] = pd.to_numeric(
        df_relacao["numero_peca"],
        errors="coerce",
    )

    ordem_categorias = [
        "15KG - 24KG",
        "25KG - 39KG",
        "40KG ACIMA",
        "2º FURO",
        "LOMBO",
    ]

    mapa_ordem = {
        categoria: indice
        for indice, categoria in enumerate(
            ordem_categorias
        )
    }

    df_relacao["ORDEM_CATEGORIA"] = df_relacao[
        "CLASSIFICACAO_RELACAO"
    ].map(mapa_ordem)

    return (
        df_relacao.sort_values(
            by=[
                "ORDEM_CATEGORIA",
                "PESO_RELACAO",
                "NUMERO_PECA_RELACAO",
            ],
            ascending=[
                True,
                False,
                True,
            ],
        )
        .reset_index(drop=True)
    )


def build_financial_dataframe(dataframe, prices):
    """
    Constrói o dataframe financeiro (Romaneio Comercial) cruzando
    o peso de cada categoria com os preços inseridos no ecrã.
    """
    df_fin = dataframe.copy()
    
    df_fin["CATEGORIA_FINANCEIRA"] = df_fin.apply(classificar_peca_relacao, axis=1)
    
    mapa_precos = {
        "15KG - 24KG": prices.get("15_24", 0.0),
        "25KG - 39KG": prices.get("25_39", 0.0),
        "40KG ACIMA": prices.get("40_up", 0.0),
        "2º FURO": prices.get("furo", 0.0),
        "LOMBO": prices.get("lombo", 0.0),
    }
    
    resumo = df_fin.groupby("CATEGORIA_FINANCEIRA")["peso_kg"].sum().reset_index()
    
    ordem_categorias = [
        "15KG - 24KG", 
        "25KG - 39KG", 
        "40KG ACIMA", 
        "2º FURO", 
        "LOMBO"
    ]
    
    linhas = []
    total_kg_geral = 0.0
    total_valor_geral = 0.0
    
    for cat in ordem_categorias:
        linha_cat = resumo[resumo["CATEGORIA_FINANCEIRA"] == cat]
        kg = float(linha_cat["peso_kg"].iloc[0]) if not linha_cat.empty else 0.0
        
        preco = mapa_precos[cat]
        valor_total_linha = kg * preco
        
        linhas.append({
            "TIPO (ATUM)": cat,
            "KG": kg,
            "PREÇO (R$)": preco,
            "TOTAL": valor_total_linha
        })
        
        total_kg_geral += kg
        total_valor_geral += valor_total_linha
        
    linhas.append({
        "TIPO (ATUM)": "TOTAL",
        "KG": total_kg_geral,
        "PREÇO (R$)": 0.0,
        "TOTAL": total_valor_geral
    })
    
    return pd.DataFrame(linhas)


# ============================================================
# BANCO E ACESSO A DADOS
# ============================================================

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
# PDF - RELATÓRIO DE DESCARGA COM LOGO NAVIMAR
# ============================================================

def gerar_dashboard_pdf(
    df_lote,
    df_resumo,
    df_financeiro,
    logo_path,
):
    from io import BytesIO

    from reportlab.lib.colors import HexColor, white
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas

    # --------------------------------------------------------
    # PALETA VISUAL NAVIMAR
    # --------------------------------------------------------

    NAVY = HexColor("#0B2545")
    METAL = HexColor("#4F7CAC")
    LINE = HexColor("#E6EAF0")
    SLATE = HexColor("#5B6573")
    LIGHT = HexColor("#A3ABB7")
    SHADOW = HexColor("#E9EDF3")
    CARD = HexColor("#FFFFFF")
    SOFT_BLUE = HexColor("#F1F6FA")

    # --------------------------------------------------------
    # FUNÇÕES AUXILIARES
    # --------------------------------------------------------

    def format_number(value):
        return (
            f"{float(value):,.2f}"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )

    def draw_rounded_card(
        pdf_canvas,
        x,
        y,
        width,
        height,
        radius=10,
        fill_color=CARD,
        border_color=LINE,
        shadow=True,
    ):
        if shadow:
            pdf_canvas.setFillColor(SHADOW)
            pdf_canvas.roundRect(
                x + 1.5,
                y - 2.5,
                width,
                height,
                radius,
                stroke=0,
                fill=1,
            )

        pdf_canvas.setFillColor(fill_color)
        pdf_canvas.setStrokeColor(border_color)
        pdf_canvas.setLineWidth(0.6)
        pdf_canvas.roundRect(
            x,
            y,
            width,
            height,
            radius,
            stroke=1,
            fill=1,
        )

    def draw_logo_card(
        pdf_canvas,
        image_path,
        x,
        y,
        card_width,
        card_height,
    ):
        draw_rounded_card(
            pdf_canvas,
            x=x,
            y=y,
            width=card_width,
            height=card_height,
            radius=10,
            fill_color=CARD,
            border_color=LINE,
            shadow=True,
        )

        if not image_path or not Path(image_path).exists():
            pdf_canvas.setFillColor(NAVY)
            pdf_canvas.setFont("Helvetica-Bold", 15)
            pdf_canvas.drawCentredString(
                x + card_width / 2,
                y + card_height / 2 - 5,
                "NAVIMAR",
            )
            return

        try:
            image = ImageReader(str(image_path))
            image_width, image_height = image.getSize()

            padding = 8
            available_width = card_width - 2 * padding
            available_height = card_height - 2 * padding

            scale = min(
                available_width / image_width,
                available_height / image_height,
            )

            draw_width = image_width * scale
            draw_height = image_height * scale

            draw_x = x + (card_width - draw_width) / 2
            draw_y = y + (card_height - draw_height) / 2

            pdf_canvas.drawImage(
                image,
                draw_x,
                draw_y,
                width=draw_width,
                height=draw_height,
                preserveAspectRatio=True,
                mask="auto",
            )

        except Exception:
            pdf_canvas.setFillColor(NAVY)
            pdf_canvas.setFont("Helvetica-Bold", 15)
            pdf_canvas.drawCentredString(
                x + card_width / 2,
                y + card_height / 2 - 5,
                "NAVIMAR",
            )

    # --------------------------------------------------------
    # PREPARAÇÃO DO DOCUMENTO
    # --------------------------------------------------------

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)

    page_width, page_height = A4
    margin = 40

    barco = str(df_lote["barco"].iloc[0])
    armador = str(df_lote["armador"].iloc[0])
    data_lote = format_date(df_lote["data_hora"].iloc[0])

    total_kg = float(df_lote["peso_kg"].sum())
    total_pecas = int(len(df_lote))

    peso_medio = (
        total_kg / total_pecas
        if total_pecas > 0
        else 0
    )

    # --------------------------------------------------------
    # CABEÇALHO
    # --------------------------------------------------------

    header_top = page_height - margin
    logo_card_width = 103
    logo_card_height = 62
    logo_card_y = header_top - logo_card_height

    draw_logo_card(
        pdf_canvas=pdf,
        image_path=logo_path,
        x=margin,
        y=logo_card_y,
        card_width=logo_card_width,
        card_height=logo_card_height,
    )

    title_x = margin + logo_card_width + 18

    pdf.setFillColor(NAVY)
    pdf.setFont("Helvetica-Bold", 17)
    pdf.drawString(
        title_x,
        header_top - 21,
        "Relatório de Descarga",
    )

    pdf.setFillColor(METAL)
    pdf.setFont("Helvetica-Bold", 8)
    pdf.drawString(
        title_x,
        header_top - 35,
        "NAVIMAR PESCADOS",
    )

    pdf.setFillColor(SLATE)
    pdf.setFont("Helvetica", 8.5)

    metadata = [
        f"Barco: {barco}",
        f"Proprietário: {armador}",
        f"Data: {data_lote}",
    ]

    for index, item in enumerate(metadata):
        pdf.drawRightString(
            page_width - margin,
            header_top - 17 - index * 13,
            item,
        )

    separator_y = logo_card_y - 14

    pdf.setStrokeColor(METAL)
    pdf.setLineWidth(1.2)
    pdf.line(
        margin,
        separator_y,
        page_width - margin,
        separator_y,
    )

    # --------------------------------------------------------
    # RESUMO OPERACIONAL
    # --------------------------------------------------------

    section_y = separator_y - 30

    pdf.setFillColor(METAL)
    pdf.setFont("Helvetica-Bold", 8)
    pdf.drawString(
        margin,
        section_y,
        "RESUMO OPERACIONAL",
    )

    card_gap = 14
    card_width = (
        page_width
        - (2 * margin)
        - (2 * card_gap)
    ) / 3
    card_height = 76
    cards_y = section_y - 92

    kpis = [
        ("PESO TOTAL", f"{total_kg:.1f} kg"),
        ("PEÇAS", str(total_pecas)),
        ("MÉDIA POR PEÇA", f"{peso_medio:.2f} kg"),
    ]

    for index, (label, value) in enumerate(kpis):
        card_x = margin + index * (card_width + card_gap)

        draw_rounded_card(
            pdf_canvas=pdf,
            x=card_x,
            y=cards_y,
            width=card_width,
            height=card_height,
            radius=10,
            fill_color=CARD,
            border_color=LINE,
            shadow=True,
        )

        pdf.setFillColor(METAL)
        pdf.roundRect(
            card_x + 14,
            cards_y + card_height - 15,
            20,
            2.5,
            1,
            stroke=0,
            fill=1,
        )

        pdf.setFillColor(SLATE)
        pdf.setFont("Helvetica-Bold", 7.5)
        pdf.drawString(
            card_x + 14,
            cards_y + card_height - 30,
            label,
        )

        pdf.setFillColor(NAVY)
        pdf.setFont("Helvetica-Bold", 22)
        pdf.drawString(
            card_x + 14,
            cards_y + 17,
            value,
        )

    # --------------------------------------------------------
    # RESUMO COMERCIAL
    # --------------------------------------------------------

    commercial_title_y = cards_y - 31

    pdf.setFillColor(METAL)
    pdf.setFont("Helvetica-Bold", 8)
    pdf.drawString(
        margin,
        commercial_title_y,
        "RESUMO COMERCIAL",
    )

    table_header_y = commercial_title_y - 19

    col_tipo = margin + 4
    col_kg = margin + 250
    col_preco = margin + 365
    col_total = page_width - margin - 4

    pdf.setFillColor(SLATE)
    pdf.setFont("Helvetica-Bold", 7.5)

    pdf.drawString(col_tipo, table_header_y, "TIPO (ATUM)")
    pdf.drawRightString(col_kg, table_header_y, "KG")
    pdf.drawRightString(col_preco, table_header_y, "PREÇO (R$)")
    pdf.drawRightString(col_total, table_header_y, "TOTAL")

    table_line_y = table_header_y - 10

    pdf.setStrokeColor(NAVY)
    pdf.setLineWidth(0.9)
    pdf.line(
        margin,
        table_line_y,
        page_width - margin,
        table_line_y,
    )

    current_y = table_line_y
    row_height = 29

    for _, row in df_financeiro.iloc[:-1].iterrows():
        current_y -= row_height

        tipo = str(row["TIPO (ATUM)"])
        kg = float(row["KG"])
        preco = float(row["PREÇO (R$)"])
        total = float(row["TOTAL"])

        pdf.setFillColor(NAVY)
        pdf.setFont("Helvetica-Bold", 9.3)
        pdf.drawString(
            col_tipo,
            current_y + 10,
            tipo,
        )

        pdf.setFillColor(SLATE)
        pdf.setFont("Helvetica", 9.3)

        pdf.drawRightString(
            col_kg,
            current_y + 10,
            format_number(kg),
        )

        pdf.drawRightString(
            col_preco,
            current_y + 10,
            format_number(preco),
        )

        pdf.drawRightString(
            col_total,
            current_y + 10,
            f"R$ {format_number(total)}",
        )

        pdf.setStrokeColor(LINE)
        pdf.setLineWidth(0.5)
        pdf.line(
            margin,
            current_y,
            page_width - margin,
            current_y,
        )

    # --------------------------------------------------------
    # LINHA TOTAL
    # --------------------------------------------------------

    total_row = df_financeiro.iloc[-1]

    total_kg_financeiro = float(total_row["KG"])
    total_valor = float(total_row["TOTAL"])

    total_y = current_y - 42
    total_height = 34

    pdf.setFillColor(NAVY)
    pdf.roundRect(
        margin,
        total_y,
        page_width - 2 * margin,
        total_height,
        7,
        stroke=0,
        fill=1,
    )

    pdf.setFillColor(white)
    pdf.setFont("Helvetica-Bold", 10.5)

    pdf.drawString(
        col_tipo + 6,
        total_y + 12,
        "TOTAL",
    )

    pdf.drawRightString(
        col_kg,
        total_y + 12,
        format_number(total_kg_financeiro),
    )

    pdf.drawRightString(
        col_total - 6,
        total_y + 12,
        f"R$ {format_number(total_valor)}",
    )

    # --------------------------------------------------------
    # RODAPÉ
    # --------------------------------------------------------

    pdf.setStrokeColor(LINE)
    pdf.setLineWidth(0.6)
    pdf.line(
        margin,
        43,
        page_width - margin,
        43,
    )

    pdf.setFillColor(LIGHT)
    pdf.setFont("Helvetica", 7.5)
    pdf.drawCentredString(
        page_width / 2,
        28,
        "Documento gerado pelo sistema NAVIMAR PESCADOS.",
    )

    pdf.save()

    return buffer.getvalue()


# ============================================================
# EXCEL EXECUTIVO MODELO
# ============================================================

def gerar_excel_executivo(df_lote, prices, image_path):
    # Se possuir a lógica real de geração de Excel executivo, insira aqui.
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        pd.DataFrame({"Aviso": ["Lógica Ausente"]}).to_excel(writer, index=False)
    return output.getvalue()


# ============================================================
# PDF — RELAÇÃO INDIVIDUAL DO CAMINHÃO (GERAL - SEM LOMBO)
# ============================================================

def gerar_relacao_caminhao_pdf(
    df_lote,
    logo_path,
    caminhao="",
    motorista="",
    comprador="",
):
    from io import BytesIO
    from reportlab.lib.colors import HexColor, white
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas

    # Paleta de Cores
    NAVY = HexColor("#0B2545")
    METAL = HexColor("#4F7CAC")
    LINE = HexColor("#E6EAF0")
    SLATE = HexColor("#5B6573")
    CARD = HexColor("#FFFFFF")
    SHADOW = HexColor("#E9EDF3")
    LIGHT = HexColor("#A3ABB7") 

    cores = {
        "15KG - 24KG": {"bg": HexColor("#85C1E9"), "fg": HexColor("#08263D")},
        "25KG - 39KG": {"bg": HexColor("#3498DB"), "fg": white},
        "40KG ACIMA": {"bg": HexColor("#0B2545"), "fg": white},
        "2º FURO": {"bg": HexColor("#7D3C98"), "fg": white},
        "LOMBO": {"bg": HexColor("#D5A94F"), "fg": HexColor("#4A3512")},
    }

    # Processamento de Dados
    barco = str(df_lote["barco"].iloc[0]).upper()
    armador = str(df_lote["armador"].iloc[0]).upper()
    data_lote = format_date(df_lote["data_hora"].iloc[0])

    caminhao = str(caminhao).upper() if str(caminhao).strip() else "NÃO INFORMADO"
    motorista = str(motorista).upper() if str(motorista).strip() else "NÃO INFORMADO"
    comprador = str(comprador).upper() if str(comprador).strip() else "NAVIMAR PESCADOS"

    df_relacao = preparar_relacao_caminhao(df_lote)

    # Ordem das categorias sem LOMBO para este relatório
    ordem_categorias = ["15KG - 24KG", "25KG - 39KG", "40KG ACIMA", "2º FURO"]

    MAX_LINHAS = 10
    colunas_chunks = []

    for categoria in ordem_categorias:
        df_categoria = df_relacao[df_relacao["CLASSIFICACAO_RELACAO"] == categoria]
        pesos = df_categoria["PESO_RELACAO"].tolist()

        if not pesos:
            continue

        for i in range(0, len(pesos), MAX_LINHAS):
            chunk = pesos[i : i + MAX_LINHAS]
            colunas_chunks.append({"categoria": categoria, "pesos": chunk})

    if not colunas_chunks:
        colunas_chunks = [{"categoria": "15KG - 24KG", "pesos": []}]

    total_geral = sum(sum(chunk["pesos"]) for chunk in colunas_chunks)

    # Configuração do PDF (Formato Paisagem)
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=landscape(A4))
    page_width, page_height = landscape(A4)
    margin = 40

    def draw_header(pdf_canvas, page_num):
        logo_width, logo_height = 100, 60
        pdf_canvas.setFillColor(SHADOW)
        pdf_canvas.roundRect(margin + 1.5, page_height - margin - logo_height - 2.5, logo_width, logo_height, 8, stroke=0, fill=1)
        pdf_canvas.setFillColor(CARD)
        pdf_canvas.setStrokeColor(LINE)
        pdf_canvas.roundRect(margin, page_height - margin - logo_height, logo_width, logo_height, 8, stroke=1, fill=1)

        try:
            if Path(logo_path).exists():
                img = ImageReader(str(logo_path))
                pdf_canvas.drawImage(img, margin + 10, page_height - margin - logo_height + 10, width=80, height=40, preserveAspectRatio=True, mask="auto")
        except:
            pdf_canvas.setFillColor(NAVY)
            pdf_canvas.setFont("Helvetica-Bold", 12)
            pdf_canvas.drawCentredString(margin + logo_width/2, page_height - margin - logo_height/2 - 4, "NAVIMAR")

        title_x = margin + logo_width + 20

        pdf_canvas.setFillColor(NAVY)
        pdf_canvas.setFont("Helvetica-Bold", 16)
        pdf_canvas.drawString(title_x, page_height - 58, "Relação Individual da Carga")

        pdf_canvas.setFillColor(SLATE)
        pdf_canvas.setFont("Helvetica-Bold", 9)
        pdf_canvas.drawString(title_x, page_height - 76, f"Caminhão: {caminhao}   |   Motorista: {motorista}   |   Comprador: {comprador}")

        pdf_canvas.drawRightString(page_width - margin, page_height - 54, f"Barco: {barco}")
        pdf_canvas.drawRightString(page_width - margin, page_height - 66, f"Armador: {armador}")
        pdf_canvas.drawRightString(page_width - margin, page_height - 78, f"Data: {data_lote}")

        pdf_canvas.setStrokeColor(METAL)
        pdf_canvas.setLineWidth(1.2)
        pdf_canvas.line(margin, page_height - 110, page_width - margin, page_height - 110)

        pdf_canvas.setFillColor(LIGHT)
        pdf_canvas.setFont("Helvetica", 7.5)
        pdf_canvas.drawCentredString(page_width / 2, 25, f"Documento gerado pelo sistema NAVIMAR PESCADOS  ·  Página {page_num}")

    # Variáveis de Controlo de Eixo
    current_x = margin
    y_top = page_height - 135
    col_width = 82
    col_gap = 12
    row_height = 18
    page_num = 1

    draw_header(pdf, page_num)

    for chunk in colunas_chunks:
        if current_x + col_width > page_width - margin:
            pdf.showPage()
            page_num += 1
            draw_header(pdf, page_num)
            current_x = margin

        cat = chunk["categoria"]
        pesos = chunk["pesos"]
        bg_color = cores[cat]["bg"]
        fg_color = cores[cat]["fg"]

        pdf.setFillColor(bg_color)
        pdf.roundRect(current_x, y_top - 20, col_width, 20, 3, stroke=0, fill=1)
        pdf.setFillColor(fg_color)
        pdf.setFont("Helvetica-Bold", 8)
        pdf.drawCentredString(current_x + col_width/2, y_top - 14, cat)

        current_y = y_top - 20
        pdf.setLineWidth(0.5)
        for i in range(MAX_LINHAS):
            current_y -= row_height
            
            pdf.setFillColor(CARD if i < len(pesos) else HexColor("#F8F9FA"))
            pdf.setStrokeColor(LINE)
            pdf.rect(current_x, current_y, col_width, row_height, stroke=1, fill=1)

            if i < len(pesos):
                pdf.setFillColor(SLATE)
                pdf.setFont("Helvetica", 7)
                pdf.drawString(current_x + 5, current_y + 6, f"{i+1}º")

                pdf.setFillColor(NAVY)
                pdf.setFont("Helvetica-Bold", 9.5)
                pdf.drawRightString(current_x + col_width - 6, current_y + 6, f"{pesos[i]:.2f}".replace(".", ","))

        current_y -= 22
        pdf.setFillColor(bg_color)
        pdf.roundRect(current_x, current_y, col_width, 22, 3, stroke=0, fill=1)
        pdf.setFillColor(fg_color)
        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawCentredString(current_x + col_width/2, current_y + 7, f"{sum(pesos):.2f}".replace(".", ","))

        current_x += col_width + col_gap

    # CAIXA DE TOTAL GERAL
    if current_x + 160 > page_width - margin:
        pdf.showPage()
        page_num += 1
        draw_header(pdf, page_num)
        current_x = margin

    y_total_box = y_top - 20 - (MAX_LINHAS * row_height) - 22
    pdf.setFillColor(SHADOW)
    pdf.roundRect(current_x + 1.5, y_total_box - 2.5, 150, 42, 6, stroke=0, fill=1)
    pdf.setFillColor(NAVY)
    pdf.roundRect(current_x, y_total_box, 150, 42, 6, stroke=0, fill=1)
    
    pdf.setFillColor(white)
    pdf.setFont("Helvetica-Bold", 8)
    pdf.drawString(current_x + 12, y_total_box + 26, "PESO TOTAL DA CARGA")
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawRightString(current_x + 138, y_total_box + 10, f"{total_geral:,.2f} kg".replace(",", "X").replace(".", ",").replace("X", "."))

    pdf.save()
    return buffer.getvalue()

# ============================================================
# PDF — RELAÇÃO EXCLUSIVA DO LOMBO
# ============================================================

def gerar_relacao_lombo_pdf(
    df_lote,
    logo_path,
    caminhao="",
    motorista="",
    comprador="",
    fornecedor="",
    preco_kg=0.0,
):
    from io import BytesIO
    from reportlab.lib.colors import HexColor, white
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas

    NAVY = HexColor("#0B2545")
    METAL = HexColor("#4F7CAC")
    LINE = HexColor("#E6EAF0")
    SLATE = HexColor("#5B6573")
    CARD = HexColor("#FFFFFF")
    SHADOW = HexColor("#E9EDF3")
    LIGHT = HexColor("#A3ABB7")
    GOLD = HexColor("#D5A94F")
    GOLD_DARK = HexColor("#4A3512")
    GREEN_MONEY = HexColor("#087443")

    data_lote = format_date(df_lote["data_hora"].iloc[0])

    caminhao = str(caminhao).upper() if str(caminhao).strip() else "NÃO INFORMADO"
    motorista = str(motorista).upper() if str(motorista).strip() else "NÃO INFORMADO"
    comprador = str(comprador).upper() if str(comprador).strip() else "NAVIMAR PESCADOS"
    fornecedor = str(fornecedor).upper() if str(fornecedor).strip() else "NÃO INFORMADO"

    df_relacao = preparar_relacao_caminhao(df_lote)
    df_lombo = df_relacao[df_relacao["CLASSIFICACAO_RELACAO"] == "LOMBO"]
    
    total_lombo = float(df_lombo["PESO_RELACAO"].sum())
    total_pecas = len(df_lombo)
    valor_total = total_lombo * float(preco_kg)

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=landscape(A4))
    page_width, page_height = landscape(A4)
    margin = 40

    # 1. Cabeçalho Padrão Navimar
    logo_width, logo_height = 100, 60
    pdf.setFillColor(SHADOW)
    pdf.roundRect(margin + 1.5, page_height - margin - logo_height - 2.5, logo_width, logo_height, 8, stroke=0, fill=1)
    pdf.setFillColor(CARD)
    pdf.setStrokeColor(LINE)
    pdf.roundRect(margin, page_height - margin - logo_height, logo_width, logo_height, 8, stroke=1, fill=1)

    try:
        if Path(logo_path).exists():
            img = ImageReader(str(logo_path))
            pdf.drawImage(img, margin + 10, page_height - margin - logo_height + 10, width=80, height=40, preserveAspectRatio=True, mask="auto")
    except:
        pdf.setFillColor(NAVY)
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawCentredString(margin + logo_width/2, page_height - margin - logo_height/2 - 4, "NAVIMAR")

    title_x = margin + logo_width + 20

    pdf.setFillColor(NAVY)
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(title_x, page_height - 58, "Relação Exclusiva da Carga - LOMBO")

    pdf.setFillColor(SLATE)
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawString(title_x, page_height - 76, f"Caminhão: {caminhao}   |   Motorista: {motorista}   |   Comprador: {comprador}")

    # Exibe apenas Fornecedor e Data à direita (removidos barco e armador)
    pdf.drawRightString(page_width - margin, page_height - 54, f"Fornecedor: {fornecedor}")
    pdf.drawRightString(page_width - margin, page_height - 68, f"Data: {data_lote}")

    pdf.setStrokeColor(METAL)
    pdf.setLineWidth(1.2)
    pdf.line(margin, page_height - 110, page_width - margin, page_height - 110)

    pdf.setFillColor(LIGHT)
    pdf.setFont("Helvetica", 7.5)
    pdf.drawCentredString(page_width / 2, 25, "Documento gerado pelo sistema NAVIMAR PESCADOS")

    # 2. Cartão de Resumo Centralizado (aumentado para caber o valor financeiro)
    box_width = 360
    box_height = 170
    box_x = (page_width - box_width) / 2
    box_y = (page_height - 110) / 2 - box_height / 2 + 20

    pdf.setFillColor(SHADOW)
    pdf.roundRect(box_x + 3, box_y - 3, box_width, box_height, 10, stroke=0, fill=1)
    pdf.setFillColor(CARD)
    pdf.setStrokeColor(LINE)
    pdf.roundRect(box_x, box_y, box_width, box_height, 10, stroke=1, fill=1)

    header_h = 35
    pdf.setFillColor(GOLD)
    pdf.roundRect(box_x, box_y + box_height - header_h, box_width, header_h, 10, stroke=0, fill=1)
    pdf.rect(box_x, box_y + box_height - header_h, box_width, 10, stroke=0, fill=1) 

    pdf.setFillColor(GOLD_DARK)
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawCentredString(box_x + box_width/2, box_y + box_height - 22, "ATUM TIPO: LOMBO")

    # Quantidade de Peças
    pdf.setFillColor(SLATE)
    pdf.setFont("Helvetica", 11)
    pdf.drawCentredString(box_x + box_width/2, box_y + 100, f"Quantidade embalada: {total_pecas} peças")

    # Peso Total
    peso_str = f"{total_lombo:,.2f} kg".replace(",", "X").replace(".", ",").replace("X", ".")
    pdf.setFillColor(NAVY)
    pdf.setFont("Helvetica-Bold", 32)
    pdf.drawCentredString(box_x + box_width/2, box_y + 64, peso_str)

    # Preço Base
    preco_str = f"R$ {preco_kg:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    pdf.setFillColor(SLATE)
    pdf.setFont("Helvetica", 11)
    pdf.drawCentredString(box_x + box_width/2, box_y + 40, f"Preço base acordado: {preco_str} / kg")

    # Valor Total
    valor_str = f"R$ {valor_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    pdf.setFillColor(GREEN_MONEY)
    pdf.setFont("Helvetica-Bold", 22)
    pdf.drawCentredString(box_x + box_width/2, box_y + 14, f"Total: {valor_str}")

    pdf.save()
    return buffer.getvalue()


# ============================================================
# EXPORTAÇÕES EXECUTIVAS
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

# ============================================================
# RELAÇÃO OPERACIONAL DA CARGA
# ============================================================

st.markdown("<br>", unsafe_allow_html=True)

st.markdown(
    '<div class="section-title">'
    '🚚 Relação operacional da carga'
    '</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="summary-card">
        <p>
            Gere os relatórios em PDF para a conferência da carga e pré-venda. 
            A listagem geral detalha os peixes; a exportação de Lombo exibe apenas o volume total e o valor.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Agora usamos 4 colunas para incluir o Fornecedor
caminhao_col, motorista_col, comprador_col, fornecedor_col = st.columns(4)

with caminhao_col:
    caminhao_relacao = st.text_input("Caminhão", value="", placeholder="Ex.: SCANIA")
with motorista_col:
    motorista_relacao = st.text_input("Motorista", value="", placeholder="Ex.: EDUARDO")
with comprador_col:
    comprador_relacao = st.text_input("Comprador", value="NAVIMAR PESCADOS")
with fornecedor_col:
    # O Fornecedor assume por defeito o nome do Armador
    fornecedor_relacao = st.text_input("Fornecedor", value=armador_nome)

# PDF Geral (Continua sem o Lombo, detalhando os outros peixes)
relacao_caminhao_pdf_bytes = gerar_relacao_caminhao_pdf(
    df_lote=df,
    logo_path=LOGO_PATH,
    caminhao=caminhao_relacao,
    motorista=motorista_relacao,
    comprador=comprador_relacao,
)

df_verificacao = preparar_relacao_caminhao(df)
tem_lombo = (df_verificacao["CLASSIFICACAO_RELACAO"] == "LOMBO").any()

if tem_lombo:
    # PDF do Lombo puxa o preço inserido na Tabela de Preços e o novo Fornecedor
    relacao_lombo_pdf_bytes = gerar_relacao_lombo_pdf(
        df_lote=df,
        logo_path=LOGO_PATH,
        caminhao=caminhao_relacao,
        motorista=motorista_relacao,
        comprador=comprador_relacao,
        fornecedor=fornecedor_relacao,
        preco_kg=tabela_precos["lombo"], 
    )
    
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        st.download_button(
            label="📄 Relação do Caminhão (Geral)",
            data=relacao_caminhao_pdf_bytes,
            file_name=f"Relacao_Geral_{barco_nome}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    with btn_col2:
        st.download_button(
            label="Relação do Lombo (Total + Preço)",
            data=relacao_lombo_pdf_bytes,
            file_name=f"Relacao_Lombo_{barco_nome}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
else:
    st.download_button(
        label="📄 Baixar Relação do Caminhão",
        data=relacao_caminhao_pdf_bytes,
        file_name=f"Relacao_Caminhao_{barco_nome}.pdf",
        mime="application/pdf",
        use_container_width=True,
    )
