# 📋 Guia de Configuração do Supabase

Este guia explica como configurar o banco de dados Supabase para o app MIRANTES.

## 🎯 Visão Geral

Com esta configuração, seu app vai:
- ✅ Salvar dados de descargas de forma **permanente**
- ✅ **Não perder dados** ao reiniciar o app (Render, Streamlit Cloud, etc.)
- ✅ Funcionar tanto no **Streamlit Cloud** quanto no **Render/Railway**

---

## 📝 Passo 1: Criar Conta no Supabase

1. Acesse https://supabase.com
2. Clique em **"Start your project"** ou **"Sign In"**
3. Escolha **"Continue with GitHub"** (recomendado) ou use email/senha
4. Complete o cadastro

---

## 📝 Passo 2: Criar Projeto

1. No dashboard, clique em **"New Project"**
2. Preencha:
   - **Organization**: (crie uma nova ou use a padrão)
   - **Project name**: `mirantes-db` (ou outro nome)
   - **Database password**: **⚠️ ANOTE ESTA SENHA!**
   - **Region**: **South America (Brazil)** (mais próximo)
3. Clique em **"Create new project"**
4. Aguarde 2-5 minutos

---

## 📝 Passo 3: Criar Tabela no Banco

1. No dashboard, clique em **"SQL Editor"** (menu lateral)
2. Clique em **"New Query"**
3. Copie e cole o conteúdo do arquivo [`database/schema.sql`](database/schema.sql) deste repositório
4. Clique em **"Run"** ou pressione `Ctrl+Enter`

Você deve ver: *"Success. No rows returned"*

### ✅ Verificar tabela criada

1. Menu lateral → **Table Editor**
2. Você deve ver a tabela **`descargas`**
3. Colunas esperadas: `id`, `data_hora`, `data`, `volume`, `produto`, `observacoes`, `created_at`, `updated_at`

---

## 📝 Passo 4: Pegar Credenciais da API

1. Menu lateral → **Settings** (engrenagem) → **API**
2. Em **Project API keys**, copie:
   - **Project URL**: `https://xxxxx.supabase.co`
   - **anon public**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` (chave longa)

**⚠️ IMPORTANTE:** Use a chave **`anon`** (pública), **NUNCA** a `service_role` no app.

---

## 📝 Passo 5: Configurar no App

### Opção A: Streamlit Cloud

1. No seu computador, crie `.streamlit/secrets.toml` (**não commit no GitHub!**):

```toml
[supabase]
url = "https://SEU_PROJETO.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

2. No **Streamlit Cloud**:
   - Vá em **"Advanced"** → **"Secrets"**
   - Cole o conteúdo acima
   - Salve

3. Redeploy do app (se necessário)

### Opção B: Render / Railway

1. No dashboard, vá em **"Environment Variables"**
2. Adicione:
   - `SUPABASE_URL = https://SEU_PROJETO.supabase.co`
   - `SUPABASE_KEY = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`
3. Redeploy do app

### Opção C: Local (desenvolvimento)

1. Crie `.streamlit/secrets.toml` na raiz do projeto
2. Execute: `streamlit run app.py`

---

## 📝 Passo 6: Testar Conexão

Adicione este código temporário no `app.py`:

```python
from utils.database import get_supabase_client, salvar_descarga, carregar_historico
import streamlit as st
from datetime import datetime

# Testar conexão
try:
    client = get_supabase_client()
    st.success("✅ Conectado ao Supabase!")
except Exception as e:
    st.error(f"❌ Erro: {e}")

# Testar salvamento
if st.button("Testar Salvamento"):
    resultado = salvar_descarga(datetime.now(), 100.5, "Produto Teste", "Teste")
    st.success(f"✅ Salvou! ID: {resultado.get('id')}")

# Testar leitura
if st.button("Testar Leitura"):
    df = carregar_historico()
    st.dataframe(df) if not df.empty else st.info("Sem dados")
```

---

## 🔍 Monitorar Uso

1. Menu lateral → **Settings** → **Usage**
2. Veja **Database Size** (limite free: 500 MB)

**Seu uso (50 registros/mês):**
- Mensal: ~18 KB
- 500 MB duraria **~2.300 anos** 🎉

---

## ❓ Problemas Comuns

### "Credenciais não encontradas"

Verifique se `.streamlit/secrets.toml` existe ou variáveis de ambiente estão setadas.

### "Table 'descargas' doesn't exist"

Execute o SQL do arquivo `database/schema.sql` no SQL Editor.

### "Permission denied"

Execute este SQL no **SQL Editor**:

```sql
ALTER TABLE descargas ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Enable all operations" ON descargas
FOR ALL USING (true) WITH CHECK (true);
```

---

## 🔗 Links Úteis

- [Dashboard Supabase](https://supabase.com/dashboard)
- [Documentação](https://supabase.com/docs)
- [Streamlit + Supabase](https://docs.streamlit.io/develop/tutorials/databases/supabase)
