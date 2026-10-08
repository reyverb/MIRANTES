# Deploy e configuração Render

O serviço continua usando a variável secreta existente `DATABASE_URL`. Build: `pip install --no-cache-dir -r requirements.txt`. Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.

Configure o schema de negócio manualmente no Supabase executando `database/migrations/001_operational_schema.sql` após revisar. Não execute o mesmo schema cegamente num projeto que já contém dados ou tabelas antigas; primeiro faça backup e compare colunas/tipos.

Depois do deploy: abra `/` para interface operacional; `/docs` para API; `/health` e `/health/database` para checks. Todos os registros ficam em Supabase, então suspensão/redeploy do Render não apaga descargas e peças. Estado da página/navegador não é persistência de dados.

Defina `DATABASE_URL` somente no Environment do Render. Não grave credenciais no GitHub.
