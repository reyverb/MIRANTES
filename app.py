import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from PIL import Image
import os

# --- 1. CARREGAMENTO DA IMAGEM COM PROTEÇÃO ---
try:
    logo = Image.open("logo.png") 
except FileNotFoundError:
    logo = "🐟"

# --- 2. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="NAVIMAR PESCADOS", layout="centered", page_icon=logo)

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
</style>
""", unsafe_allow_html=True)

# --- 4. CONEXÃO E CRIAÇÃO DA BASE DE DADOS (CRÍTICO PARA A NUVEM) ---
conn = sqlite3.connect("porto_atum.db", check_same_thread=False)
cursor = conn.cursor()

# Cria as tabelas ANTES de qualquer consulta do Pandas
cursor.execute("""
CREATE TABLE IF NOT EXISTS descargas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    barco TEXT NOT NULL,
    proprietario TEXT NOT NULL,
    data_hora TEXT NOT NULL,
    status TEXT DEFAULT 'Em Andamento'
)
""")

cursor.execute("""
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
""")

# Garante que a coluna 'lombo' exista caso o banco já existisse antes
try:
    cursor.execute("ALTER TABLE pecas ADD COLUMN lombo INTEGER DEFAULT 0")
except sqlite3.OperationalError:
    pass

conn.commit()


# --- 5. LÓGICA DO APLICATIVO ---
def classificar_faixa(peso):
    if peso < 15.0:
        return "< 15kg (Refugo/Local)"
    elif 15.0 <= peso < 25.0:
        return "15-24kg"
    elif 25.0 <= peso < 40.0:
        return "25-39kg"
    else:
        return "40+kg (Exportação)"

st.title("🐟 NAVIMAR PESCADOS")

barcos_ativos = pd.read_sql("SELECT id, barco, proprietario FROM descargas WHERE status = 'Em Andamento'", conn)
descargas_concluidas = pd.read_sql("SELECT id, barco, proprietario, data_hora FROM descargas WHERE status = 'Concluída' ORDER BY id DESC", conn)

with st.expander("⚙ Gestão de Descargas / Selecionar Barco", expanded=barcos_ativos.empty):
    tab1, tab2, tab3 = st.tabs(["Nova Descarga", "Descargas Ativas", "Histórico Concluído"])
    
    with tab1:
        novo_barco = st.text_input("Nome da Embarcação:")
        proprietario = st.text_input("Armador / Proprietário:")
        if st.button("Iniciar Descarga", use_container_width=True):
            if novo_barco and proprietario:
                cursor.execute(
                    "INSERT INTO descargas (barco, proprietario, data_hora) VALUES (?, ?, ?)",
                    (novo_barco, proprietario, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                )
                conn.commit()
                st.success("Nova descarga iniciada com sucesso!")
                st.rerun()
            else:
                st.warning("Por favor, preencha o nome da embarcação e o armador.")
                
    with tab2:
        if not barcos_ativos.empty:
            escolha = st.selectbox(
                "Embarcação em operação:",
                barcos_ativos["id"],
                format_func=lambda x: f"{barcos_ativos.loc[barcos_ativos['id']==x, 'barco'].values[0]} ({barcos_ativos.loc[barcos_ativos['id']==x, 'proprietario'].values[0]})"
            )
            st.session_state["id_descarga"] = escolha
        else:
            st.info("Não existem descargas em andamento no momento.")

    with tab3:
        if not descargas_concluidas.empty:
            st.dataframe(descargas_concluidas, hide_index=True, use_container_width=True)
        else:
            st.info("Nenhuma descarga concluída registada.")


# --- OPERAÇÃO DA DESCARGA SELECIONADA ---
if not barcos_ativos.empty:
    id_descarga = st.session_state.get("id_descarga", barcos_ativos["id"].iloc[-1])
    dados_barco = barcos_ativos[barcos_ativos["id"] == id_descarga].iloc[0]

    df_pecas = pd.read_sql(f"SELECT * FROM pecas WHERE id_descarga = {id_descarga} ORDER BY id DESC", conn)
    proxima_peca = len(df_pecas) + 1

    st.subheader(f"Barco: {dados_barco['barco']}")
    col_m1, col_m2 = st.columns(2)
    col_m1.metric("Peças Registradas", f"{len(df_pecas)}")
    col_m2.metric("Peso Total Acumulado", f"{df_pecas['peso_kg'].sum():,.1f} kg" if not df_pecas.empty else "0.0 kg")

    st.markdown("---")

    if "peso_counter" not in st.session_state:
        st.session_state.peso_counter = 0
    if "ultimo_destino" not in st.session_state:
        st.session_state.ultimo_destino = "Caminhão"

    # --- FORMULÁRIO DE ENTRADA ---
    with st.form("form_pesagem", clear_on_submit=True):
        st.write(f"### Peça Nº **{proxima_peca}**")

        peso_input = st.number_input(
            "Peso da Peça (kg):",
            min_value=0.0,
            max_value=350.0,
            value=None,
            step=0.5,
            format="%.2f",
            key=f"peso_input_{st.session_state.peso_counter}"
        )

        col1, col2 = st.columns(2)
        with col1:
            segundo_furo = st.checkbox("🚩 2º Furo")
        with col2:
            lombo = st.checkbox("🔪 Lombo")

        destinos = ["Caminhão"]
        idx_destino = destinos.index(st.session_state.ultimo_destino) if st.session_state.ultimo_destino in destinos else 0
        destino = st.radio(
            "Destino imediato:",
            destinos,
            index=idx_destino,
            horizontal=True
        )

        submit = st.form_submit_button("➕ Salvar e Próxima Peça", use_container_width=True)

        if submit:
            if peso_input is not None and peso_input >= 5.0:
                categoria = classificar_faixa(peso_input)
                cursor.execute("""
                    INSERT INTO pecas (id_descarga, numero_peca, peso_kg, categoria, segundo_furo, lombo, destino, data_registro)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    int(id_descarga),
                    proxima_peca,
                    peso_input,
                    categoria,
                    1 if segundo_furo else 0,
                    1 if lombo else 0,
                    destino,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))
                conn.commit()

                st.session_state.ultimo_destino = destino
                st.session_state.peso_counter += 1

                st.toast(f"Peça #{proxima_peca} ({peso_input:.2f} kg) registrada!", icon="✅")
                st.rerun()
            else:
                st.error("Informe um peso válido (mínimo de 5.0 kg).")

    # --- HISTÓRICO RECENTE ---
    if not df_pecas.empty:
        st.write("#### Últimos Lançamentos")
        st.dataframe(
            df_pecas[["numero_peca", "peso_kg", "categoria", "segundo_furo", "lombo", "destino"]].head(5),
            column_config={
                "numero_peca": "Nº",
                "peso_kg": st.column_config.NumberColumn("Peso (kg)", format="%.2f kg"),
                "categoria": "Peso",
                "segundo_furo": st.column_config.CheckboxColumn("2º Furo"),
                "lombo": st.column_config.CheckboxColumn("Lombo"),
                "destino": "Destino"
            },
            hide_index=True,
            use_container_width=True
        )

        if st.button("🗑️ Excluir Última Peça Inserida", type="secondary", use_container_width=True):
            id_para_excluir = df_pecas.iloc[0]["id"]
            cursor.execute("DELETE FROM pecas WHERE id = ?", (int(id_para_excluir),))
            conn.commit()
            st.warning(f"Peça #{df_pecas.iloc[0]['numero_peca']} removida com sucesso.")
            st.rerun()

        st.markdown("---")
        st.subheader("🏁 Conclusão da Descarga")
        
        with st.expander("Encerrar Lote e Gerar Balanço Final"):
            st.write(f"Confirme o fecho da descarga do lote **{dados_barco['barco']}**.")
            
            total_kg = df_pecas["peso_kg"].sum()
            total_pecas = len(df_pecas)
            media_kg = total_kg / total_pecas if total_pecas > 0 else 0
            qtd_furo = df_pecas["segundo_furo"].sum()
            qtd_lombo = df_pecas["lombo"].sum() if "lombo" in df_pecas.columns else 0

            c1, c2, c3 = st.columns(3)
            c1.metric("Total Peças", total_pecas)
            c2.metric("Total (kg)", f"{total_kg:,.1f} kg")
            c3.metric("Média/Peça", f"{media_kg:,.1f} kg")

            if qtd_furo > 0 or qtd_lombo > 0:
                st.caption(f"⚠️ Peças com 2º Furo: **{qtd_furo}** | Peças como Lombo: **{qtd_lombo}**")

            csv_data = df_pecas.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descarregar Relatório (CSV)",
                data=csv_data,
                file_name=f"descarga_{dados_barco['barco']}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True
            )

            if st.button("✅ Concluir e Fechar Descarga", type="primary", use_container_width=True):
                cursor.execute("UPDATE descargas SET status = 'Concluída' WHERE id = ?", (int(id_descarga),))
                conn.commit()
                st.success(f"Descarga de **{dados_barco['barco']}** finalizada e arquivada com sucesso!")
                st.balloons()
                st.rerun()

else:
    st.info("Nenhuma descarga em andamento. Abra uma nova descarga ou selecione um lote existente no menu acima.")
