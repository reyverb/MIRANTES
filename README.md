# MIRANTES API

Backend Python para deploy no Render e persistencia de dados no PostgreSQL do Supabase.

## Objetivo

Este repositorio contem somente a API e a camada de dados. Ele nao inclui Streamlit, paginas de interface ou configuracoes de interface.

## Requisitos

- Python 3.11 ou superior
- Uma instancia PostgreSQL no Supabase
- Variavel `DATABASE_URL`

## Execucao local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

No Windows, ative o ambiente com `.venv\\Scripts\\activate`.

## Endpoints iniciais

- `GET /`: estado basico do servico
- `GET /health`: health check do processo
- `GET /health/database`: verifica a conexao PostgreSQL

## Deploy

O arquivo `render.yaml` configura um Render Web Service que executa:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Configure `DATABASE_URL` e `CORS_ORIGINS` no painel do Render. Nunca inclua chaves reais ou URLs com senha em commits.

Leia `DEPLOY_RENDER.md` e `CONFIGURACAO_SUPABASE.md` antes de publicar.
