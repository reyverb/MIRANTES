# Supabase para NAVIMAR PESCADOS

A aplicação conecta ao PostgreSQL por SQLAlchemy usando `DATABASE_URL` configurada no Render. Prefira connection string Session Pooler do Supabase adequada a backend persistente IPv4. Use SSL e mantenha a senha codificada na URL se contiver caracteres reservados.

## Schema

Antes de executar SQL em banco com dados, faça backup e inspecione tabelas. A migration `database/migrations/001_operational_schema.sql` cria `descargas` e `pecas`, com as colunas esperadas pelo app antigo. Revise-a e execute manualmente no SQL Editor. O serviço não executa DDL ao iniciar.

## Segurança

A aplicação usa conexão direta PostgreSQL server-side; nunca exponha `DATABASE_URL` no browser. Não use chaves Supabase no JavaScript nem habilite acesso público irrestrito. Planeje autenticação e autorização antes de disponibilizar o endereço publicamente.
