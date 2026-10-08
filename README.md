# NAVIMAR PESCADOS — aplicação operacional

Aplicação web FastAPI servida pelo mesmo Render, com banco PostgreSQL persistente no Supabase. A interface abre em `/`; a API documentada fica em `/docs`.

## Funcionalidades
- Criar, listar, operar e concluir descargas.
- Registrar peças (5 a 350 kg), classificação automática, 2º furo, lombo e destino.
- Indicadores por lote, histórico, fechamento comercial, CSV e PDF.
- Persistência exclusivamente PostgreSQL/Supabase. O Render não guarda SQLite nem arquivos de dados locais.

## Schema Supabase
Revise `database/migrations/001_operational_schema.sql` e execute manualmente no SQL Editor do Supabase uma vez. A aplicação não cria nem altera tabelas automaticamente.

## Ambiente local
Defina `DATABASE_URL` e instale `requirements.txt`; execute `uvicorn app.main:app --reload`.
