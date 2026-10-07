from pathlib import Path
import sqlite3
from datetime import datetime

import pandas as pd
import streamlit as st
from PIL import Image


# ============================================================
# CONFIGURAÇÃO DE CAMINHOS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
LOGO_PATH = BASE_DIR / "logo.png"
DATABASE_PATH = BASE_DIR / "porto_atum.db"


# ============================================================
# CARREGAMENTO SEGURO DA LOGO
# ============================================================

try:
    logo = Image.open(LOGO_PATH)
except Exception:
    logo = None


# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================

st.set_page_config(
    page_title="NAVIMAR PESCADOS",
    layout="wide",
    page_icon=logo if logo is not None else "⚓",
    initial_sidebar_state="collapsed",
)


# ============================================================
# IDENTIDADE VISUAL
# ============================================================

st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        :root {
            --navy: #08263d;
            --navy-dark: #041827;
            --blue: #1479a8;
            --blue-dark: #0b587d;
            --aqua: #18a6a6;
            --blue-light: #e7f4fa;
            --cream: #f7f4ed;
            --gold: #d5a94f;
            --text: #183243;
            --muted: #607786;
            --border: #c9d9df;
            --white: #ffffff;
            --success: #087443;
            --danger: #b42318;
        }

        html, body, [class*="css"] {
            font-family: "Inter", sans-serif;
        }

        .stApp {
            background:
                radial-gradient(
                    circle at top right,
                    rgba(20, 121, 168, 0.10),
                    transparent 30%
                ),
                linear-gradient(
                    180deg,
                    #f6fbfc 0%,
                    #eaf4f4 100%
                );
            color: var(--text);
        }

        [data-testid="stAppViewContainer"] {
            background: transparent;
        }

        [data-testid="stHeader"] {
            background: rgba(255, 255, 255, 0.82);
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(
                180deg,
                var(--navy-dark),
                var(--navy)
            );
        }

        [data-testid="stSidebar"] * {
            color: #ffffff !important;
        }

        h1, h2, h3, h4, h5, h6 {
            color: var(--navy) !important;
            font-weight: 800 !important;
            letter-spacing: -0.03em;
        }

        p, label, span, div {
            color: var(--text);
        }

        .block-container {
            max-width: 1380px;
            padding-top: 1.7rem;
            padding-bottom: 3rem;
        }

        .main-title {
            color: var(--navy);
            font-size: clamp(2rem, 4vw, 3.1rem);
            font-weight: 800;
            letter-spacing: -0.055em;
            margin-bottom: 0.15rem;
        }

        .page-subtitle {
            color: var(--muted) !important;
            font-size: 1rem;
            margin-bottom: 1.5rem;
        }

        .section-title {
            color: var(--navy);
            font-size: 1.35rem;
            font-weight: 800;
            margin-top: 0.5rem;
            margin-bottom: 0.75rem;
        }

        .logo-container {
            display: flex;
            align-items: center;
            gap: 0.9rem;
            margin-bottom: 0.25rem;
        }

        .logo-fallback {
            width: 72px;
            height: 72px;
            border-radius: 16px;
            display: flex;
            justify-content: center;
            align-items: center;
            background: var(--navy);
            color: #ffffff !important;
            font-size: 2rem;
        }

        /* =====================================================
           EXPANDER
        ===================================================== */

        [data-testid="stExpander"] {
            background: rgba(255, 255, 255, 0.86);
            border: 1px solid var(--border);
            border-radius: 14px;
            overflow: hidden;
        }

        [data-testid="stExpander"] details summary {
            background: var(--navy) !important;
            color: #ffffff !important;
            min-height: 2.9rem;
            border-radius: 13px 13px 0 0 !important;
        }

        [data-testid="stExpander"] details summary:hover {
            background: var(--blue) !important;
        }

        [data-testid="stExpander"] details summary p,
        [data-testid="stExpander"] details summary span,
        [data-testid="stExpander"] details summary svg {
            color: #ffffff !important;
            fill: #ffffff !important;
            font-weight: 800 !important;
        }

        [data-testid="stExpander"] details[open] summary {
            border-bottom: 1px solid var(--border);
        }

        /* =====================================================
           ABAS
        ===================================================== */

        .stTabs [data-baseweb="tab-list"] {
            display: flex;
            gap: 0.45rem;
            background: #eef5f7;
            border: 1px solid var(--border);
            padding: 0.35rem;
            border-radius: 12px;
            box-shadow: none !important;
        }

        .stTabs [data-baseweb="tab"] {
            height: 2.55rem;
            padding: 0 1rem;
            border-radius: 9px;
            background: transparent !important;
            color: #365466 !important;
            font-weight: 700 !important;
            box-shadow: none !important;
        }

        .stTabs [data-baseweb="tab"]:hover {
            background: #dcecf2 !important;
            color: var(--navy) !important;
        }

        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background: var(--blue) !important;
            color: #ffffff !important;
            box-shadow: 0 3px 8px rgba(20, 121, 168, 0.25) !important;
        }

        .stTabs [data-baseweb="tab-highlight"],
        .stTabs [data-baseweb="tab-border"] {
            display: none !important;
        }

        /* =====================================================
           CAMPOS
        ===================================================== */

        .stTextInput > div > div,
        .stNumberInput > div > div,
        .stSelectbox > div > div,
        .stTextArea > div > div {
            background-color: #ffffff !important;
            border: 1px solid #9db5c0 !important;
            border-radius: 10px !important;
        }

        .stTextInput input,
        .stNumberInput input,
        .stTextArea textarea {
            color: var(--text) !important;
            background-color: #ffffff !important;
            font-weight: 600 !important;
        }

        .stTextInput input::placeholder,
        .stNumberInput input::placeholder {
            color: #718793 !important;
            opacity: 1 !important;
        }

        .stTextInput input:focus,
        .stNumberInput input:focus {
            border-color: var(--blue) !important;
            box-shadow: 0 0 0 2px rgba(20, 121, 168, 0.16) !important;
        }

        /* =====================================================
           BOTÕES
        ===================================================== */

        .stButton > button,
        .stFormSubmitButton > button,
        .stDownloadButton > button {
            min-height: 2.8rem;
            border-radius: 10px;
            font-weight: 800;
            transition: all 0.18s ease;
        }

        .stButton > button {
            background: var(--navy);
            color: #ffffff !important;
            border: 1px solid var(--navy);
        }

        .stButton > button:hover {
            background: var(--blue);
            color: #ffffff !important;
            border-color: var(--blue);
            transform: translateY(-1px);
            box-shadow: 0 6px 16px rgba(20, 121, 168, 0.25);
        }

        .stButton > button[kind="primary"],
        .stFormSubmitButton > button {
            background: linear-gradient(
                135deg,
                var(--blue),
                var(--blue-dark)
            ) !important;
            color: #ffffff !important;
            border: 1px solid var(--blue-dark) !important;
            font-weight: 800 !important;
        }

        .stButton > button[kind="primary"]:hover,
        .stFormSubmitButton > button:hover {
            background: linear-gradient(
                135deg,
                var(--aqua),
                var(--blue)
            ) !important;
            color: #ffffff !important;
            border-color: var(--blue) !important;
        }

        .stDownloadButton > button {
            background: var(--cream);
            border: 1px solid var(--gold);
            color: var(--navy) !important;
        }

        .stDownloadButton > button:hover {
            background: #fff8e8;
            border-color: var(--gold);
        }

        /* =====================================================
           CARTÕES DE MÉTRICAS
        ===================================================== */

        .metric-card {
            background: rgba(255, 255, 255, 0.95);
            border: 1px solid var(--border);
            border-left: 5px solid var(--blue);
            border-radius: 16px;
            padding: 1rem 1.1rem;
            min-height: 105px;
            box-shadow: 0 8px 24px rgba(8, 38, 61, 0.08);
        }

        .metric-label {
            color: var(--muted) !important;
            font-size: 0.8rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }

        .metric-value {
            color: var(--navy) !important;
            font-size: 1.65rem;
            font-weight: 800;
            margin-top: 0.35rem;
        }

        /* =====================================================
           CARTÃO DE FORMULÁRIO
        ===================================================== */

        .input-card {
            background: rgba(255, 255, 255, 0.96);
            border: 1px solid var(--border);
            border-radius: 18px;
            padding: 1.25rem;
            box-shadow: 0 10px 28px rgba(8, 38, 61, 0.08);
        }

        .help-text {
            color: var(--muted) !important;
            font-size: 0.86rem;
            margin-top: -0.25rem;
        }

        .status-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.42rem 0.75rem;
            border-radius: 999px;
            background: #e4f6ed;
            color: var(--success) !important;
            border: 1px solid #acdcbf;
            font-size: 0.82rem;
            font-weight: 800;
        }

        [data-testid="stDataFrame"] {
            border: 1px solid var(--border);
            border-radius: 12px;
            overflow: hidden;
        }

        .stAlert {
            border-radius: 12px;
        }

        hr {
            border: none;
            border-top: 1px solid rgba(96, 119, 134, 0.25);
            margin: 1.5rem 0;
        }

        /* =====================================================
           REMOÇÃO DO BORRÃO DE FOCO
        ===================================================== */

        button:focus,
        button:focus-visible,
        [data-baseweb="tab"]:focus,
        [data-baseweb="tab"]:focus-visible {
            outline: none !important;
            box-shadow: none !important;
        }

        [data-baseweb="tab-list"]::after,
        [data-baseweb="tab-list"]::before {
            display: none !important;
        }

        @media (max-width: 768px) {
            .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
            }

            .main-title {
                font-size: 2rem;
            }

            .metric-value {
                font-size: 1.35rem;
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# CONEXÃO E CRIAÇÃO DO BANCO
# ============================================================

@st.cache_resource
def get_database():
    connection = sqlite3.connect(
        DATABASE_PATH,
        check_same_thread=False,
    )

    cursor = connection.cursor()

    cursor.execute(
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

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS pecas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_descarga INTEGER,
            numero_peca INTEGER,
            peso_kg REAL,
            categoria TEXT,
            segundo_furo INTEGER,
            lombo INTEGER,
            destino TEXT,
            data_registro TEXT,
            FOREIGN KEY(id_descarga) REFERENCES descargas(id)
        )
        """
    )

    try:
        cursor.execute(
            "ALTER TABLE pecas ADD COLUMN lombo INTEGER DEFAULT 0"
        )
    except sqlite3.OperationalError:
        pass

    connection.commit()
    return connection


conn = get_database()
cursor = conn.cursor()


# ============================================================
# FUNÇÕES
# ============================================================

def classificar_faixa(peso):
    if peso < 15.0:
        return "< 15 kg · Refugo/Local"
    elif peso < 25.0:
        return "15-24kg"
    elif peso < 40.0:
        return "25-39kg"
    else:
        return "40+kg (Exportação)"


def render_metric_card(label, value, accent="#1479a8"):
    st.markdown(
        f"""
        <div class="metric-card" style="border-left-color: {accent};">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# CABEÇALHO PRINCIPAL
# ============================================================

if logo is not None:
    logo_col, title_col = st.columns([0.7, 5])

    with logo_col:
        st.image(logo, width=72)

    with title_col:
        st.markdown(
            '<div class="main-title">NAVIMAR PESCADOS</div>',
            unsafe_allow_html=True,
        )
else:
    st.markdown(
        """
        <div class="logo-container">
            <div class="logo-fallback">⚓</div>
            <div class="main-title">NAVIMAR PESCADOS</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown(
    '<div class="page-subtitle">Controle de descargas, pesagem e classificação de pescados.</div>',
    unsafe_allow_html=True,
)


# ============================================================
# CONSULTAS
# ============================================================

barcos_ativos = pd.read_sql(
    """
    SELECT id, barco, proprietario
    FROM descargas
    WHERE status = 'Em Andamento'
    ORDER BY id DESC
    """,
    conn,
)

descargas_concluidas = pd.read_sql(
    """
    SELECT id, barco, proprietario, data_hora
    FROM descargas
    WHERE status = 'Concluída'
    ORDER BY id DESC
    """,
    conn,
)


# ============================================================
# GESTÃO DE DESCARGAS
# ============================================================

with st.expander(
    "⚙️ Gestão de descargas e seleção de embarcação",
    expanded=barcos_ativos.empty,
):
    tab1, tab2, tab3 = st.tabs(
        [
            "➕ Nova descarga",
            "🚢 Descargas ativas",
            "📚 Histórico concluído",
        ]
    )

    with tab1:
        st.markdown(
            '<div class="section-title">Iniciar novo lote</div>',
            unsafe_allow_html=True,
        )

        col_a, col_b = st.columns(2)

        with col_a:
            novo_barco = st.text_input(
                "Nome da embarcação",
                placeholder="Ex.: Navio Atlântico",
                key="novo_barco",
            )

        with col_b:
            proprietario = st.text_input(
                "Armador / proprietário",
                placeholder="Ex.: Empresa Naval Ltda.",
                key="proprietario",
            )

        if st.button(
            "🚀 Iniciar descarga",
            use_container_width=True,
            type="primary",
        ):
            if novo_barco.strip() and proprietario.strip():
                cursor.execute(
                    """
                    INSERT INTO descargas
                    (barco, proprietario, data_hora)
                    VALUES (?, ?, ?)
                    """,
                    (
                        novo_barco.strip(),
                        proprietario.strip(),
                        datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                    ),
                )

                conn.commit()
                st.success("Nova descarga iniciada com sucesso.")
                st.rerun()
            else:
                st.warning(
                    "Preencha o nome da embarcação e "
                    "o armador/proprietário."
                )

    with tab2:
        if not barcos_ativos.empty:
            opcoes_barcos = barcos_ativos["id"].tolist()

            escolha_atual = st.session_state.get(
                "id_descarga",
                opcoes_barcos[0],
            )

            if escolha_atual not in opcoes_barcos:
                escolha_atual = opcoes_barcos[0]

            escolha = st.selectbox(
                "Embarcação em operação",
                options=opcoes_barcos,
                index=opcoes_barcos.index(escolha_atual),
                format_func=lambda x: (
                    f"{barcos_ativos.loc[barcos_ativos['id'] == x, 'barco'].iloc[0]}"
                    f" · "
                    f"{barcos_ativos.loc[barcos_ativos['id'] == x, 'proprietario'].iloc[0]}"
                ),
            )

            st.session_state["id_descarga"] = escolha

            st.markdown(
                '<span class="status-pill">● Descarga em andamento</span>',
                unsafe_allow_html=True,
            )
        else:
            st.info(
                "Não existem descargas em andamento no momento."
            )

    with tab3:
        if not descargas_concluidas.empty:
            st.dataframe(
                descargas_concluidas,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "id": st.column_config.NumberColumn("ID"),
                    "barco": "Embarcação",
                    "proprietario": "Proprietário",
                    "data_hora": "Início",
                },
            )
        else:
            st.info(
                "Nenhuma descarga concluída registrada."
            )


# ============================================================
# OPERAÇÃO DA DESCARGA
# ============================================================

if not barcos_ativos.empty:
    ids_ativos = barcos_ativos["id"].tolist()

    id_descarga = st.session_state.get(
        "id_descarga",
        ids_ativos[0],
    )

    if id_descarga not in ids_ativos:
        id_descarga = ids_ativos[0]
        st.session_state["id_descarga"] = id_descarga

    dados_barco = barcos_ativos[
        barcos_ativos["id"] == id_descarga
    ].iloc[0]

    df_pecas = pd.read_sql(
        """
        SELECT *
        FROM pecas
        WHERE id_descarga = ?
        ORDER BY id DESC
        """,
        conn,
        params=(int(id_descarga),),
    )

    proxima_peca = len(df_pecas) + 1
    total_kg_atual = (
        df_pecas["peso_kg"].sum()
        if not df_pecas.empty
        else 0
    )

    st.markdown("---")

    header_col, status_col = st.columns([3, 1])

    with header_col:
        st.markdown(
            f'<div class="section-title">🚢 {dados_barco["barco"]}</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            f'<div class="help-text">Armador / proprietário: '
            f'{dados_barco["proprietario"]}</div>',
            unsafe_allow_html=True,
        )

    with status_col:
        st.markdown(
            '<div style="text-align:right;">'
            '<span class="status-pill">● Operação ativa</span>'
            '</div>',
            unsafe_allow_html=True,
        )

    metric_col1, metric_col2, metric_col3 = st.columns(3)

    with metric_col1:
        render_metric_card(
            "Peças registradas",
            f"{len(df_pecas):,}",
            "#1479a8",
        )

    with metric_col2:
        render_metric_card(
            "Peso total acumulado",
            f"{total_kg_atual:,.1f} kg",
            "#18a6a6",
        )

    with metric_col3:
        media_atual = (
            total_kg_atual / len(df_pecas)
            if not df_pecas.empty
            else 0
        )

        render_metric_card(
            "Média por peça",
            f"{media_atual:,.1f} kg",
            "#d5a94f",
        )

    st.markdown("<br>", unsafe_allow_html=True)

    if "peso_counter" not in st.session_state:
        st.session_state["peso_counter"] = 0

    if "ultimo_destino" not in st.session_state:
        st.session_state["ultimo_destino"] = "Caminhão"

    campo_peso_key = (
        f"peso_input_{st.session_state['peso_counter']}"
    )

    st.markdown(
        '<div class="input-card">',
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<div class="section-title">⚖️ Registrar peça nº '
        f'{proxima_peca}</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="help-text">'
        'Digite o peso e pressione Enter para salvar rapidamente. '
        'O campo será liberado novamente para a próxima peça.'
        '</div>',
        unsafe_allow_html=True,
    )

    with st.form(
        f"form_pesagem_{st.session_state['peso_counter']}",
        clear_on_submit=False,
    ):
        peso_input = st.number_input(
            "Peso da peça (kg)",
            min_value=0.0,
            max_value=350.0,
            value=None,
            step=0.5,
            format="%.2f",
            key=campo_peso_key,
            placeholder="Ex.: 32,50",
        )

        col1, col2 = st.columns(2)

        with col1:
            segundo_furo = st.checkbox("🚩 2º furo")

        with col2:
            lombo = st.checkbox("🔪 Lombo")

        destinos = ["Caminhão"]

        destino = st.radio(
            "Destino imediato",
            options=destinos,
            index=(
                destinos.index(
                    st.session_state["ultimo_destino"]
                )
                if st.session_state["ultimo_destino"] in destinos
                else 0
            ),
            horizontal=True,
        )

        salvar = st.form_submit_button(
            "➕ Salvar peça e liberar próximo campo",
            use_container_width=True,
        )

        if salvar:
            if peso_input is None:
                st.error("Informe o peso da peça.")
            elif peso_input < 5.0:
                st.error(
                    "O peso mínimo permitido é de 5,00 kg."
                )
            else:
                categoria = classificar_faixa(
                    float(peso_input)
                )

                cursor.execute(
                    """
                    INSERT INTO pecas (
                        id_descarga,
                        numero_peca,
                        peso_kg,
                        categoria,
                        segundo_furo,
                        lombo,
                        destino,
                        data_registro
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        int(id_descarga),
                        proxima_peca,
                        float(peso_input),
                        categoria,
                        1 if segundo_furo else 0,
                        1 if lombo else 0,
                        destino,
                        datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                    ),
                )

                conn.commit()

                st.session_state["ultimo_destino"] = destino
                st.session_state["peso_counter"] += 1

                st.toast(
                    f"Peça nº {proxima_peca} registrada: "
                    f"{peso_input:.2f} kg",
                    icon="✅",
                )

                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    # ========================================================
    # HISTÓRICO RECENTE
    # ========================================================

    if not df_pecas.empty:
        st.markdown(
            '<div class="section-title">🧾 Últimos lançamentos</div>',
            unsafe_allow_html=True,
        )

        historico = df_pecas[
            [
                "numero_peca",
                "peso_kg",
                "categoria",
                "segundo_furo",
                "lombo",
                "destino",
            ]
        ].head(8)

        st.dataframe(
            historico,
            column_config={
                "numero_peca": st.column_config.NumberColumn(
                    "Nº",
                    width="small",
                ),
                "peso_kg": st.column_config.NumberColumn(
                    "Peso",
                    format="%.2f kg",
                ),
                "categoria": st.column_config.TextColumn(
                    "Classificação",
                ),
                "segundo_furo": st.column_config.CheckboxColumn(
                    "2º furo",
                ),
                "lombo": st.column_config.CheckboxColumn(
                    "Lombo",
                ),
                "destino": st.column_config.TextColumn(
                    "Destino",
                ),
            },
            hide_index=True,
            use_container_width=True,
        )

        if st.button(
            "🗑️ Excluir última peça inserida",
            type="secondary",
            use_container_width=True,
        ):
            id_para_excluir = int(
                df_pecas.iloc[0]["id"]
            )

            cursor.execute(
                "DELETE FROM pecas WHERE id = ?",
                (id_para_excluir,),
            )

            conn.commit()

            st.warning(
                f"Peça nº {df_pecas.iloc[0]['numero_peca']} "
                "removida."
            )

            st.rerun()

        st.markdown("---")

        # ====================================================
        # CONCLUSÃO DA DESCARGA
        # ====================================================

        st.markdown(
            '<div class="section-title">🏁 Conclusão da descarga</div>',
            unsafe_allow_html=True,
        )

        with st.expander(
            "Encerrar lote e gerar balanço final"
        ):
            total_kg = df_pecas["peso_kg"].sum()
            total_pecas = len(df_pecas)
            media_kg = (
                total_kg / total_pecas
                if total_pecas
                else 0
            )

            qtd_furo = int(
                df_pecas["segundo_furo"].sum()
            )

            qtd_lombo = (
                int(df_pecas["lombo"].sum())
                if "lombo" in df_pecas.columns
                else 0
            )

            st.warning(
                f"Confirme o encerramento da descarga do lote "
                f"**{dados_barco['barco']}**."
            )

            final_col1, final_col2, final_col3 = st.columns(3)

            with final_col1:
                render_metric_card(
                    "Total de peças",
                    f"{total_pecas:,}",
                    "#1479a8",
                )

            with final_col2:
                render_metric_card(
                    "Total de peso",
                    f"{total_kg:,.1f} kg",
                    "#18a6a6",
                )

            with final_col3:
                render_metric_card(
                    "Média por peça",
                    f"{media_kg:,.1f} kg",
                    "#d5a94f",
                )

            if qtd_furo > 0 or qtd_lombo > 0:
                st.caption(
                    f"🚩 Peças com 2º furo: **{qtd_furo}** · "
                    f"🔪 Peças como lombo: **{qtd_lombo}**"
                )

            csv_data = df_pecas.to_csv(
                index=False
            ).encode("utf-8")

            st.download_button(
                label="📥 Baixar relatório CSV",
                data=csv_data,
                file_name=(
                    f"descarga_{dados_barco['barco']}_"
                    f"{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
                ),
                mime="text/csv",
                use_container_width=True,
            )

            if st.button(
                "✅ Concluir e fechar descarga",
                type="primary",
                use_container_width=True,
            ):
                cursor.execute(
                    """
                    UPDATE descargas
                    SET status = 'Concluída'
                    WHERE id = ?
                    """,
                    (int(id_descarga),),
                )

                conn.commit()

                st.success(
                    f"Descarga de **{dados_barco['barco']}** "
                    "finalizada e arquivada com sucesso."
                )

                st.balloons()
                st.rerun()

else:
    st.info(
        "Nenhuma descarga em andamento. "
        "Abra uma nova descarga ou selecione um lote existente."
    )
