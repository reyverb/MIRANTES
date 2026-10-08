# 🚀 Guia de Deploy no Render (Free Tier)

Deploy do app MIRANTES no Render com plano gratuito.

## 📋 Plano Free

- ✅ 750 horas/mês (app 24/7)
- ✅ 512 MB RAM
- ❌ Hiberna após 15 min inatividade (cold start ~30s)
- ❌ Sem custom domain

**Para 50 registros/mês: free tier é suficiente!**

---

## 🛠️ Passo a Passo

### 1️⃣ Criar Conta

1. Acesse https://render.com
2. **Get Started for Free** → **Continue with GitHub**

### 2️⃣ Criar Web Service

1. Dashboard → **New +** → **Web Service**
2. Conecte GitHub
3. Selecione: **`reyverb/MIRANTES`**

### 3️⃣ Configurar

| Campo | Valor |
|-------|-------|
| **Name** | `mirantes-app` |
| **Region** | Oregon, USA |
| **Branch** | `main` |
| **Runtime** | Python 3 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `streamlit run app.py --server.address 0.0.0.0 --server.port $PORT` |
| **Instance Type** | Free |

### 4️⃣ Variáveis de Ambiente

**Advanced** → **Add Environment Variable**:

| Key | Value |
|-----|-------|
| `PYTHON_VERSION` | `3.11.0` |
| `SUPABASE_URL` | `https://SEU_PROJETO.supabase.co` |
| `SUPABASE_KEY` | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` |

**Onde pegar:** Supabase → Settings → API

### 5️⃣ Deploy

1. **Create Web Service**
2. Aguarde build (~2-5 min)
3. Clique na URL quando aparecer **Live**

---

## 📁 render.yaml

O arquivo [`render.yaml`](render.yaml) já está configurado com auto-deploy.

---

## ❓ Problemas Comuns

### "ModuleNotFoundError"
Verifique `requirements.txt`: `streamlit`, `supabase`, `pandas`, `plotly`

### "Credenciais não encontradas"
Configure `SUPABASE_URL` e `SUPABASE_KEY` em **Environment**

### App hiberna
Normal no free! Dados **NÃO** se perdem (estão no Supabase) ✅

---

## 🔗 Links

- [Render Dashboard](https://dashboard.render.com)
- [Docs Render](https://render.com/docs)
