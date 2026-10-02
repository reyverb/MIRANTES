import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- CONFIGURAÇÃO MOBILE ---
st.set_page_config(
    page_title="Recepção de Atum - Cais",
    page_icon="🐟",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Estilização para operação no cais (botões e inputs grandes)
st.markdown("""
<style>
    input[type="number"], input[type="text"] {
        font-size: 1.4rem !important;
        font-weight: 700 !important;
        min-height: 50px !important;
    }
    div.stButton > button[kind="primary"] {
        width: 100%;
        min-height: 56px;
        font-size: 1.25rem !important;
        font-weight: 800 !important;
        border-radius: 8px;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.6rem !important;
    }
</style>
""", unsafe_allow_html=True)

# --- BANCO DE DADOS LOCAL ---
@st.cache_resource
def get_db():
    conn = sqlite3.connect("porto_atum.db", check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

conn = get_db()

def init_db():
    with conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS descargas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barco TEXT NOT NULL,
            proprietario TEXT NOT NULL,
            data_hora TEXT NOT NULL,
            status TEXT DEFAULT 'Em Andamento'
        )
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS pecas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_descarga INTEGER NOT NULL,
            numero_peca INTEGER NOT NULL,
            peso_kg REAL NOT NULL,
            categoria TEXT NOT NULL,
            segundo_furo INTEGER DEFAULT 0,
            destino TEXT NOT NULL,
            data_registro TEXT NOT NULL,
            FOREIGN KEY(id_descarga) REFERENCES descargas(id)
        )
        """)

init_db()

# --- REGRAS DE NEGÓCIO ---
def classificar_faixa(peso: float) -> str:
    if peso < 15.0:
        return "< 15kg (Refugo/Local)"
    elif 15.0 <= peso < 25.0:
        return "15-24kg"
    elif 25.0 <= peso < 40.0:
        return "25-39kg"
    return "40+kg (Exportação)"

def obter_proxima_peca(id_descarga: int) -> int:
    cursor = conn.cursor()
    cursor.execute("SELECT COALESCE(MAX(numero_peca), 0) + 1 FROM pecas WHERE id_descarga = ?", (id_descarga,))
    return cursor.fetchone()[0]

# --- SESSÃO ---
if "ultimo_destino" not in st.session_state:
    st.session_state["ultimo_destino"] = "Caminhão"
if "id_descarga" not in st.session_state:
    st.session_state["id_descarga"] = None

st.title("🐟 Desembarque de Atum")

# Botão direto para o painel analítico
st.page_link("pages/dashboard.py", label="Abrir Painel Gerencial & Romaneio", icon="📊")

# --- GESTÃO DE LOTES ---
barcos_ativos = pd.read_sql("SELECT id, barco, proprietario FROM descargas WHERE status = 'Em Andamento'", conn)

with st.expander("⚙️ Selecionar ou Abrir Lote de Barco", expanded=(st.session_state["id_descarga"] is None)):
    tab1, tab2 = st.tabs(["Lotes em Andamento", "Novo Barco"])
    
    with tab1:
        if not barcos_ativos.empty:
            opcoes_barco = {
                row["id"]: f"{row['barco']} — Armador: {row['proprietario']} (Lote #{row['id']})"
                for _, row in barcos_ativos.iterrows()
            }
            barco_selecionado = st.selectbox(
                "Embarcação em operação:",
                options=list(opcoes_barco.keys()),
                format_func=lambda x: opcoes_barco[x]
            )
            if st.button("Fixar para Digitação", use_container_width=True):
                st.session_state["id_descarga"] = barco_selecionado
                st.rerun()
        else:
            st.info("Nenhuma descarga ativa no momento.")

    with tab2:
        novo_barco = st.text_input("Nome do Barco:")
        proprietario = st.text_input("Proprietário / Armador:")
        if st.button("Iniciar Nova Descarga", use_container_width=True):
            if novo_barco.strip() and proprietario.strip():
                with conn:
                    cur = conn.cursor()
                    cur.execute(
                        "INSERT INTO descargas (barco, proprietario, data_hora, status) VALUES (?, ?, ?, 'Em Andamento')",
                        (novo_barco.strip(), proprietario.strip(), datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    )
                    st.session_state["id_descarga"] = cur.lastrowid
                st.success("Descarga iniciada!")
                st.rerun()
            else:
                st.error("Preencha o nome do barco e do armador.")

# --- TELA DE DIGITAÇÃO NO CAIS ---
if st.session_state["id_descarga"] is not None:
    id_descarga = int(st.session_state["id_descarga"])
    info_barco = pd.read_sql("SELECT barco, proprietario FROM descargas WHERE id = ?", conn, params=(id_descarga,))
    
    if not info_barco.empty:
        nome_barco = info_barco.iloc[0]["barco"]
        
        df_pecas = pd.read_sql(
            "SELECT id, numero_peca, peso_kg, categoria, segundo_furo, destino, data_registro "
            "FROM pecas WHERE id_descarga = ? ORDER BY numero_peca DESC",
            conn,
            params=(id_descarga,)
        )
        
        proxima_peca = obter_proxima_peca(id_descarga)
        total_pecas = len(df_pecas)
        total_peso = df_pecas["peso_kg"].sum() if not df_pecas.empty else 0.0

        st.markdown(f"### 🚢 Barco: **{nome_barco}** (Lote #{id_descarga})")
        c1, c2 = st.columns(2)
        c1.metric("Peças Registradas", f"{total_pecas}")
        c2.metric("Total Acumulado", f"{total_peso:,.1f} kg")
        st.divider()

        # Entrada de Peso
        st.markdown(f"#### 🏷️ PEÇA Nº **{proxima_peca}**")
        peso_input = st.number_input(
            label="PESO DA PEÇA (KG):",
            min_value=0.0,
            max_value=400.0,
            step=0.1,
            value=None,
            placeholder="0.0",
            format="%.2f"
        )

        segundo_furo = st.checkbox("🚩 2º Furo (Carne reavaliada)")

        opcoes_destino = ["Caminhão", "Câmara Fria"]
        idx_destino_padrao = opcoes_destino.index(st.session_state["ultimo_destino"])
        destino_selecionado = st.radio(
            "DESTINO IMEDIATO:",
            opcoes_destino,
            index=idx_destino_padrao,
            horizontal=True
        )

        if st.button("➕ SALVAR E PRÓXIMA PEÇA", type="primary", use_container_width=True):
            if peso_input is not None and peso_input >= 5.0:
                categoria = classificar_faixa(peso_input)
                data_agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                with conn:
                    conn.execute("""
                    INSERT INTO pecas (id_descarga, numero_peca, peso_kg, categoria, segundo_furo, destino, data_registro)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        id_descarga,
                        proxima_peca,
                        float(peso_input),
                        categoria,
                        1 if segundo_furo else 0,
                        destino_selecionado,
                        data_agora
                    ))

                st.session_state["ultimo_destino"] = destino_selecionado
                st.toast(f"Peça #{proxima_peca} ({peso_input:.1f} kg) registrada!", icon="✅")
                st.rerun()
            else:
                st.error("Informe um peso válido (mínimo de 5.0 kg).")

        # Histórico recente e safety net
        st.divider()
        st.markdown("#### 📋 Últimas Peças Registradas")
        
        if not df_pecas.empty:
            ultimas_tres = df_pecas.head(3).copy()
            ultimas_tres["2º Furo"] = ultimas_tres["segundo_furo"].apply(lambda x: "Sim" if x == 1 else "Não")

            st.dataframe(
                ultimas_tres[["numero_peca", "peso_kg", "categoria", "2º Furo", "destino"]],
                column_config={
                    "numero_peca": st.column_config.NumberColumn("Nº", format="#%d"),
                    "peso_kg": st.column_config.NumberColumn("Peso", format="%.2f kg"),
                    "categoria": "Calibre",
                    "2º Furo": "2º Furo",
                    "destino": "Destino"
                },
                hide_index=True,
                use_container_width=True
            )

            ultima_peca = df_pecas.iloc[0]
            if st.button(f"🚨 Excluir Peça #{int(ultima_peca['numero_peca'])}", use_container_width=True):
                with conn:
                    conn.execute("DELETE FROM pecas WHERE id = ?", (int(ultima_peca["id"]),))
                st.warning(f"Peça #{int(ultima_peca['numero_peca'])} removida.")
                st.rerun()

            # Encerramento do lote
            with st.expander("⚠️ Concluir e Fechar Descarga"):
                if st.button("🏁 Finalizar Operação deste Barco", type="primary", use_container_width=True):
                    with conn:
                        conn.execute("UPDATE descargas SET status = 'Finalizada' WHERE id = ?", (id_descarga,))
                    st.session_state["id_descarga"] = None
                    st.success("Descarga concluída com sucesso!")
                    st.rerun()
        else:
            st.info("Aguardando registro da primeira peça.")
