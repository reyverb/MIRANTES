# Render

O serviço usa o `DATABASE_URL` já configurado e executa `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Abra `/` para a interface, `/docs` para a API, `/health` e `/health/database` para verificações.

Todos os dados operacionais devem ser persistidos no Supabase. O sistema não grava SQLite/estado durável no filesystem do Render, portanto hibernação ou redeploy não remove registros do banco.

Antes do deploy da branch feature, verifique que a migration SQL corresponde às tabelas existentes e preserve `DATABASE_URL` como Environment Secret no Render.
