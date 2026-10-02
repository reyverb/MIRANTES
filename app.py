import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# Configuração da página para ocupar a tela cheia no mobile
st.set_page_config(page_title="Recepção de Atum", layout="centered", page_icon="🐟")

# --- CONEXÃO COM O BANCO DE DADOS LOCAL ---
conn = sqlite3.connect("porto_atum.db", check_same_thread=False)
cursor = conn.cursor()

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
    destino TEXT,
    data_registro TEXT,
    FOREIGN KEY(id_descarga) REFERENCES descargas(id)
)
""")
conn.commit()

# --- REGRA DE CLASSIFICAÇÃO AUTOMÁTICA ---
def classificar_faixa(peso):
    if peso < 15.0:
        return "< 15kg (Refugo/Local)"
    elif 15.0 <= peso < 25.0:
        return "15-24kg"
    elif 25.0 <= peso < 40.0:
        return "25-39kg"
    else:
        return "40+kg (Exportação)"

# --- SELEÇÃO OU ABERTURA DE LOTE DO BARCO ---
st.title("🐟 Desembarque de Atum")

barcos_ativos = pd.read_sql("SELECT id, barco, proprietario FROM descargas WHERE status = 'Em Andamento'", conn)

with st.expander("⚙️ Abrir Nova Descarga / Selecionar Barco", expanded=barcos_ativos.empty):
    tab1, tab2 = st.tabs(["Nova Descarga", "Selecionar Ativa"])
    
    with tab1:
        novo_barco = st.text_input("Nome do Barco:")
        proprietario = st.text_input("Proprietário / Armador:")
        if st.button("Iniciar Descarga", use_container_width=True):
            if novo_barco and proprietario:
                cursor.execute(
                    "INSERT INTO descargas (barco, proprietario, data_hora) VALUES (?, ?, ?)",
                    (novo_barco, proprietario, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                )
                conn.commit()
                st.success("Descarga iniciada!")
                st.rerun()
            else:
                st.warning("Preencha o nome do barco e o proprietário.")
                
    with tab2:
        if not barcos_ativos.empty:
            escolha = st.selectbox(
                "Barco em operação:",
                barcos_ativos["id"],
                format_func=lambda x: f"{barcos_ativos.loc[barcos_ativos['id']==x, 'barco'].values[0]} ({barcos_ativos.loc[barcos_ativos['id']==x, 'proprietario'].values[0]})"
            )
            st.session_state["id_descarga"] = escolha

# Se houver um barco ativo selecionado
if not barcos_ativos.empty:
    id_descarga = st.session_state.get("id_descarga", barcos_ativos["id"].iloc[-1])
    dados_barco = barcos_ativos[barcos_ativos["id"] == id_descarga].iloc[0]

    # Obter histórico de peças do barco atual
    df_pecas = pd.read_sql(f"SELECT * FROM pecas WHERE id_descarga = {id_descarga} ORDER BY id DESC", conn)
    proxima_peca = len(df_pecas) + 1

    # Cabeçalho operacional
    st.subheader(f"Barco: {dados_barco['barco']}")
    col_m1, col_m2 = st.columns(2)
    col_m1.metric("Peças Registradas", f"{len(df_pecas)}")
    col_m2.metric("Peso Total (kg)", f"{df_pecas['peso_kg'].sum():,.1f} kg" if not df_pecas.empty else "0.0 kg")

    st.markdown("---")

    # --- INICIALIZAÇÃO DE ESTADOS PARA RESET E MEMÓRIA ---
    if "peso_counter" not in st.session_state:
        st.session_state.peso_counter = 0
    if "ultimo_destino" not in st.session_state:
        st.session_state.ultimo_destino = "Caminhão"

    # --- FORMULÁRIO DE ENTRADA RÁPIDA (MOBILE) ---
    with st.form("form_pesagem", clear_on_submit=True):
        st.write(f"### Peça Nº **{proxima_peca}**")

        # A key dinâmica recria o widget com valor 0.0 a cada envio bem-sucedido
        peso_input = st.number_input(
            "Peso da Peça (kg):",
            min_value=0.0,
            max_value=300.0,
            value=0.0,
            step=0.5,
            format="%.2f",
            key=f"peso_input_{st.session_state.peso_counter}"
        )

        segundo_furo = st.checkbox("🚩 2º Furo (Carne reavaliada)")

        destinos = ["Caminhão", "Câmara Fria"]
        idx_destino = destinos.index(st.session_state.ultimo_destino) if st.session_state.ultimo_destino in destinos else 0
        destino = st.radio(
            "Destino imediato:",
            destinos,
            index=idx_destino,
            horizontal=True
        )

        submit = st.form_submit_button("➕ Salvar e Próxima Peça", use_container_width=True)

        if submit:
            if peso_input >= 5.0:
                categoria = classificar_faixa(peso_input)
                cursor.execute("""
                    INSERT INTO pecas (id_descarga, numero_peca, peso_kg, categoria, segundo_furo, destino, data_registro)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    int(id_descarga),
                    proxima_peca,
                    peso_input,
                    categoria,
                    1 if segundo_furo else 0,
                    destino,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))
                conn.commit()

                # Memoriza o último destino utilizado
                st.session_state.ultimo_destino = destino

                # Incrementa o contador para forçar o campo de peso a zerar no próximo ciclo
                st.session_state.peso_counter += 1

                st.toast(f"Peça #{proxima_peca} ({peso_input:.2f} kg) registrada com sucesso!", icon="✅")
                st.rerun()
            else:
                st.error("Informe um peso válido (mínimo 5 kg).")

    # --- ÚLTIMOS REGISTROS PARA CONFERÊNCIA ---
    if not df_pecas.empty:
        st.write("#### Últimos Lançamentos")
        st.dataframe(
            df_pecas[["numero_peca", "peso_kg", "categoria", "segundo_furo", "destino"]].head(5),
            column_config={
                "numero_peca": "Nº",
                "peso_kg": st.column_config.NumberColumn("Peso (kg)", format="%.2f kg"),
                "categoria": "Calibre",
                "segundo_furo": st.column_config.CheckboxColumn("2º Furo"),
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
else:
    st.info("Nenhuma descarga em andamento. Abra ou selecione uma descarga acima para iniciar os lançamentos.")

