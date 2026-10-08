# Deploy no Render

## 1. Criar o servico

1. No Render, crie um **Web Service** conectado a este repositorio.
2. Se o Blueprint for detectado, aceite o arquivo `render.yaml`.
3. Confirme que o build usa `pip install --no-cache-dir -r requirements.txt`.
4. Confirme que o start command usa `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.

## 2. Variaveis de ambiente

Cadastre no painel do Render:

```text
DATABASE_URL=postgresql+psycopg2://USER:PASSWORD@HOST:5432/postgres?sslmode=require
ENVIRONMENT=production
CORS_ORIGINS=https://seu-dominio.example
```

Use a URL de conexao PostgreSQL obtida no painel do Supabase. Caso a senha tenha caracteres reservados, codifique-os na URL.

Nao registre segredos no GitHub, em `render.yaml`, em logs ou em documentacao publica.

## 3. Validacao

Apos o deploy, valide:

```text
GET /health
GET /health/database
```

`/health` confirma que a API iniciou. `/health/database` confirma que o Render alcança o banco. Se o segundo endpoint responder 503, revise `DATABASE_URL`, senha, SSL e a conectividade do banco.

## 4. Operacao

- O Render fornece a porta atraves de `$PORT`; nao fixe uma porta propria.
- O health check configurado e `/health` para evitar tornar a disponibilidade do processo dependente de uma verificacao de banco.
- Faça deploy com cache limpo quando houver alteracao em `requirements.txt`.
- Mantenha os logs sem URLs de banco, tokens ou senhas.
