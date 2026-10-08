"""
Módulo de conexão com Supabase para o app MIRANTES
Este módulo funciona tanto no Streamlit Cloud quanto no Render
"""

import streamlit as st
from supabase import create_client, Client
import os
from datetime import datetime
from typing import Optional, List, Dict
import pandas as pd


@st.cache_resource
def get_supabase_client() -> Client:
    """
    Conecta no Supabase (funciona em Streamlit Cloud e Render)
    
    Returns:
        Client: Cliente Supabase configurado
    """
    # Tenta pegar do secrets (Streamlit Cloud)
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
    except (KeyError, FileNotFoundError, AttributeError):
        # Fallback para variáveis de ambiente (Render, local)
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        raise ValueError(
            "Credenciais do Supabase não encontradas. "
            "Configure em .streamlit/secrets.toml ou nas variáveis de ambiente."
        )
    
    return create_client(url, key)


def salvar_descarga(
    data: datetime,
    volume: float,
    produto: str,
    observacoes: Optional[str] = None
) -> Dict:
    """
    Salva um registro de descarga no banco de dados
    
    Args:
        data: Data da descarga
        volume: Volume descarregado
        produto: Nome do produto
        observacoes: Observações adicionais (opcional)
    
    Returns:
        Dict: Dados do registro salvo
    """
    supabase = get_supabase_client()
    
    dados = {
        "data": data.strftime("%Y-%m-%d") if isinstance(data, datetime) else str(data),
        "volume": float(volume),
        "produto": produto,
        "observacoes": observacoes or ""
    }
    
    response = supabase.table("descargas").insert(dados).execute()
    
    return response.data[0] if response.data else {}


def carregar_historico(
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    produto: Optional[str] = None
) -> pd.DataFrame:
    """
    Carrega histórico de descargas do banco de dados
    
    Args:
        data_inicio: Filtrar por data inicial (YYYY-MM-DD)
        data_fim: Filtrar por data final (YYYY-MM-DD)
        produto: Filtrar por produto
    
    Returns:
        pd.DataFrame: DataFrame com histórico de descargas
    """
    supabase = get_supabase_client()
    
    # Construir query
    query = supabase.table("descargas").select("*").order("data", desc=True)
    
    # Aplicar filtros se fornecidos
    if data_inicio:
        query = query.gte("data", data_inicio)
    
    if data_fim:
        query = query.lte("data", data_fim)
    
    if produto:
        query = query.eq("produto", produto)
    
    response = query.execute()
    
    if not response.data:
        return pd.DataFrame()
    
    return pd.DataFrame(response.data)


def carregar_todos_produtos() -> List[str]:
    """
    Carrega lista de todos os produtos únicos cadastrados
    
    Returns:
        List[str]: Lista de nomes de produtos
    """
    supabase = get_supabase_client()
    
    response = supabase.table("descargas").select("produto").execute()
    
    if not response.data:
        return []
    
    # Extrair produtos únicos
    produtos = sorted(set(item["produto"] for item in response.data))
    return produtos


def deletar_descarga(id_descarga: int) -> bool:
    """
    Deleta um registro de descarga
    
    Args:
        id_descarga: ID do registro a deletar
    
    Returns:
        bool: True se deletado com sucesso
    """
    supabase = get_supabase_client()
    
    response = supabase.table("descargas").delete().eq("id", id_descarga).execute()
    
    return response.data is not None


def atualizar_descarga(
    id_descarga: int,
    data: Optional[str] = None,
    volume: Optional[float] = None,
    produto: Optional[str] = None,
    observacoes: Optional[str] = None
) -> Dict:
    """
    Atualiza um registro de descarga
    
    Args:
        id_descarga: ID do registro a atualizar
        data: Nova data (opcional)
        volume: Novo volume (opcional)
        produto: Novo produto (opcional)
        observacoes: Novas observações (opcional)
    
    Returns:
        Dict: Dados atualizados
    """
    supabase = get_supabase_client()
    
    dados_atualizar = {}
    
    if data:
        dados_atualizar["data"] = data
    if volume is not None:
        dados_atualizar["volume"] = float(volume)
    if produto:
        dados_atualizar["produto"] = produto
    if observacoes is not None:
        dados_atualizar["observacoes"] = observacoes
    
    if not dados_atualizar:
        return {}
    
    response = (
        supabase.table("descargas")
        .update(dados_atualizar)
        .eq("id", id_descarga)
        .execute()
    )
    
    return response.data[0] if response.data else {}


def get_resumo_descargas(
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None
) -> Dict:
    """
    Retorna resumo estatístico das descargas
    
    Args:
        data_inicio: Data inicial para filtro
        data_fim: Data final para filtro
    
    Returns:
        Dict: Resumo com total, média, etc.
    """
    df = carregar_historico(data_inicio=data_inicio, data_fim=data_fim)
    
    if df.empty:
        return {
            "total_descargas": 0,
            "volume_total": 0,
            "volume_medio": 0,
            "produtos_unicos": 0
        }
    
    return {
        "total_descargas": len(df),
        "volume_total": df["volume"].sum(),
        "volume_medio": df["volume"].mean(),
        "produtos_unicos": df["produto"].nunique()
    }
