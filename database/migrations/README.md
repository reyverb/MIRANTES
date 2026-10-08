# Migrations PostgreSQL

Execute migrations manual e explicitamente no SQL Editor do Supabase. Não rode migration destrutiva em produção sem backup. Migration 001 cria as tabelas de domínio para instalações novas. Para um projeto já provisionado, compare o schema real e crie uma migration de adaptação não destrutiva antes de executar.