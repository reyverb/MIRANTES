import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# Configuração da página para utilização móvel no cais
st.set_page_config(page_title="Recepção de Atum", layout="centered", page_icon="🐟")

# --- CONEXÃO COM A BASE DE DADOS LOCAL ---
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

# --- REGRA DE CLASSIFICAÇÃO AUTOMÁTICA POR CALIBRE ---
def classificar_faixa(peso):
    if peso < 15.0:
        return "< 15kg (Refugo/Local)"
    elif 15.0 <= peso < 25.0:
        return "15-24kg"
    elif 25.0 <= peso < 40.0:
        return "25-39kg"
    else:
        return "40+kg (Exportação)"

# --- SELEÇÃO OU ABERTURA DE DESCARGA / LOTE ---
st.title("🐟 Desembarque de Atum")

barcos_ativos = pd.read_sql("SELECT id, barco, proprietario FROM descargas WHERE status = 'Em Andamento'", conn)
descargas_concluidas = pd.read_sql("SELECT id, barco, proprietario, data_hora FROM descargas WHERE status = 'Concluída' ORDER BY id DESC", conn)

with st.expander("⚙️️ Gestão de Descargas / Selecionar Barco", expanded=barcos_ativos.empty):
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

    # Obter histórico de peças do lote atual
    df_pecas = pd.read_sql(f"SELECT * FROM pecas WHERE id_descarga = {id_descarga} ORDER BY id DESC", conn)
    proxima_peca = len(df_pecas) + 1

    # Cabeçalho operacional com métricas em tempo real
    st.subheader(f"Barco: {dados_barco['barco']}")
    col_m1, col_m2 = st.columns(2)
    col_m1.metric("Peças Registadas", f"{len(df_pecas)}")
    col_m2.metric("Peso Total Acumulado", f"{df_pecas['peso_kg'].sum():,.1f} kg" if not df_pecas.empty else "0.0 kg")

    st.markdown("---")

    # Inicialização de estados para reset do campo de peso e memória de destino
    if "peso_counter" not in st.session_state:
        st.session_state.peso_counter = 0
    if "ultimo_destino" not in st.session_state:
        st.session_state.ultimo_destino = "Caminhão"

    # --- FORMULÁRIO DE ENTRADA RÁPIDA (PESAGEM) ---
    with st.form("form_pesagem", clear_on_submit=True):
        st.write(f"### Peça Nº **{proxima_peca}**")

        # A chave dinâmica garante que o input zere após cada inserção bem-sucedida
        peso_input = st.number_input(
            "Peso da Peça (kg):",
            min_value=0.0,
            max_value=350.0,
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

                # Preserva o último destino para a próxima peça
                st.session_state.ultimo_destino = destino

                # Incrementa o contador para zerar o campo no ciclo seguinte
                st.session_state.peso_counter += 1

                st.toast(f"Peça #{proxima_peca} ({peso_input:.2f} kg) registada!", icon="✅")
                st.rerun()
            else:
                st.error("Informe um peso válido (mínimo de 5.0 kg).")

    # --- HISTÓRICO RECENTE E CORREÇÃO RÁPIDA ---
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

        # --- PARTE DE CONCLUSÃO / ENCERRAMENTO DA DESCARGA ---
        st.markdown("---")
        st.subheader("🏁 Conclusão da Descarga")
        
        with st.expander("Encerrar Lote e Gerar Balanço Final"):
            st.write(f"Confirme o fecho da descarga do lote **{dados_barco['barco']}**.")
            
            # Resumo prévio do lote
            total_kg = df_pecas["peso_kg"].sum()
            total_pecas = len(df_pecas)
            media_kg = total_kg / total_pecas if total_pecas > 0 else 0
            qtd_furo = df_pecas["segundo_furo"].sum()

            c1, c2, c3 = st.columns(3)
            c1.metric("Total Peças", total_pecas)
            c2.metric("Total (kg)", f"{total_kg:,.1f} kg")
            c3.metric("Média/Peça", f"{media_kg:,.1f} kg")

            if qtd_furo > 0:
                st.caption(f"⚠️ Peças com 2º Furo: **{qtd_furo}**")

            # Opção de descarregar dados em CSV antes ou após fechar
            csv_data = df_pecas.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descarregar Relatório (CSV)",
                data=csv_data,
                file_name=f"descarga_{dados_barco['barco']}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True
            )

            # Botão de confirmação de conclusão
            if st.button("✅ Concluir e Fechar Descarga", type="primary", use_container_width=True):
                cursor.execute("UPDATE descargas SET status = 'Concluída' WHERE id = ?", (int(id_descarga),))
                conn.commit()
                st.success(f"Descarga de **{dados_barco['barco']}** finalizada e arquivada com sucesso!")
                st.balloons()
                st.rerun()

else:
    st.info("Nenhuma descarga em andamento. Abra uma nova descarga ou selecione um lote existente no menu acima.")
