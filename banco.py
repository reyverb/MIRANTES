"""
Camada de banco de dados do app NAVIMAR PESCADOS.
Usa PostgreSQL (Supabase) quando houver uma URL de conexão configurada e
SQLite local como alternativa para desenvolvimento.
"""
import os
import re
from pathlib import Path

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text

BASE_DIR = Path(__file__).resolve().parent
SQLITE_LOCAL = f"sqlite:///{BASE_DIR / 'porto_atum.db'}"

def _obter_url() -> str:
    url = None
    try:
        url = st.secrets["supabase"]["db_url"]
    except Exception:
        pass
    if not url:
        try:
            url = st.secrets["DATABASE_URL"]
        except Exception:
            pass
    url = url or os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DB_URL")
    if not url:
        return SQLITE_LOCAL
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url

def _converter(sql: str, params):
    """Converte os "?" do código original em parâmetros nomeados."""
    params = tuple(params or ())
    nomes = {}
    contador = iter(range(len(params)))

    def troca(_):
        i = next(contador)
        nomes[f"p{i}"] = params[i]
        return f":p{i}"
    
    return text(re.sub(r"\?", troca, sql)), nomes

class Banco:
    def __init__(self, engine):
        self.engine = engine

    def cursor(self):
        return self

    def execute(self, sql, params=()):
        comando, nomes = _converter(sql, params)
        with self.engine.begin() as con:
            con.execute(comando, nomes)

    def commit(self):
        """Cada execute já é confirmado automaticamente."""
        pass

    def read_sql(self, sql, params=()):
        comando, nomes = _converter(sql, params)
        with self.engine.connect() as con:
            return pd.read_sql_query(comando, con, params=nomes)

def _criar_tabelas(engine):
    postgres = engine.dialect.name == "postgresql"
    pk = "SERIAL PRIMARY KEY" if postgres else "INTEGER PRIMARY KEY AUTOINCREMENT"
    real = "DOUBLE PRECISION" if postgres else "REAL"
    with engine.begin() as con:
        con.execute(text(f"""
            CREATE TABLE IF NOT EXISTS descargas (
                id {pk},
                barco TEXT NOT NULL,
                proprietario TEXT NOT NULL,
                data_hora TEXT NOT NULL,
                status TEXT DEFAULT 'Em Andamento'
            )
        """))
        con.execute(text(f"""
            CREATE TABLE IF NOT EXISTS pecas (
                id {pk},
                id_descarga INTEGER REFERENCES descargas(id),
                numero_peca INTEGER,
                peso_kg {real},
                categoria TEXT,
                segundo_furo INTEGER,
                lombo INTEGER DEFAULT 0,
                destino TEXT,
                data_registro TEXT
            )
        """))
        if postgres:
            con.execute(text(
                "ALTER TABLE pecas ADD COLUMN IF NOT EXISTS lombo INTEGER DEFAULT 0"
            ))

@st.cache_resource
def get_database() -> Banco:
    url = _obter_url()
    argumentos = {"pool_pre_ping": True, "pool_recycle": 300}
    if url.startswith("sqlite"):
        argumentos["connect_args"] = {"check_same_thread": False}
    engine = create_engine(url, **argumentos)
    _criar_tabelas(engine)
    return Banco(engine)

conn = get_database()
cursor = conn.cursor()

def consultar(sql, _conexao=None, params=None):
    """Substitui pd.read_sql(sql, conn, params=...) do código original."""
    return conn.read_sql(sql, params or ())
