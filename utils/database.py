import os
import re
from pathlib import Path
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text

BASE_DIR = Path(__file__).resolve().parent.parent
SQLITE_LOCAL = f"sqlite:///{BASE_DIR / 'porto_atum.db'}"

def _obter_url() -> str:
    url = os.getenv("DATABASE_URL")
    
    if not url:
        try:
            url = st.secrets["supabase"]["db_url"]
        except Exception:
            pass

    if not url:
        return SQLITE_LOCAL

    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url

def _converter(sql: str, params):
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
        pass

    def read_sql(self, sql, params=()):
        comando, nomes = _converter(sql, params)
        with self.engine.connect() as con:
            return pd.read_sql_query(comando, con, params=nomes)

@st.cache_resource
def get_database() -> Banco:
    url = _obter_url()
    argumentos = {"pool_pre_ping": True, "pool_recycle": 300}
    if url.startswith("sqlite"):
        argumentos["connect_args"] = {"check_same_thread": False}
    engine = create_engine(url, **argumentos)
    return Banco(engine)

conn = get_database()
cursor = conn.cursor()

def consultar(sql, _conexao=None, params=None):
    return conn.read_sql(sql, params or ())
