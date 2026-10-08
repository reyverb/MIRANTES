# Configuracao do Supabase

## Banco PostgreSQL

1. Crie ou selecione o projeto no Supabase.
2. Execute o conteudo de `database/schema.sql` no SQL Editor do Supabase, depois de revisar o schema.
3. Obtenha a URL de conexao PostgreSQL apropriada para uma aplicacao hospedada externamente.
4. Guarde essa URL somente como `DATABASE_URL` no Render.

Formato esperado pela aplicacao:

```text
postgresql+psycopg2://USER:PASSWORD@HOST:5432/postgres?sslmode=require
```

## Seguranca

- Nao envie `DATABASE_URL`, senha, `service_role` ou outras chaves para o GitHub.
- Nao entregue chaves com privilegios administrativos a clientes web ou aplicativos externos.
- Use consultas parametrizadas e valide autorizacao no backend antes de ler ou alterar dados.
- Aplique constraints, indices e chaves estrangeiras no banco.
- Se usar Row Level Security, defina politicas explicitas e teste cada papel de acesso.

## Uso do SDK

A API usa SQLAlchemy para PostgreSQL. Adicione o SDK do Supabase apenas quando for necessario usar recursos como Auth, Storage ou Realtime. Caso seja adicionado, mantenha as chaves no Render e limite a chave `service_role` ao backend.
