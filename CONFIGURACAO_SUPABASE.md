# Supabase

A conexão é PostgreSQL via SQLAlchemy e variável `DATABASE_URL` no Render. Os identificadores seguem fielmente `app.txt`: `descargas.data_hora`; `pecas.id_descarga`, `numero_peca`, `peso_kg`, `segundo_furo`, `lombo`, `destino`, `data_registro`.

Não execute a migration antes de verificar o schema atual, exportar backup e confirmar que não há tabelas/colunas incompatíveis. A migration não é executada automaticamente. Mantenha URL, senha e chaves fora do GitHub.
