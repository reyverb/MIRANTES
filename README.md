# NAVIMAR PESCADOS — aplicação operacional

FastAPI serve a interface em `/` e a API em `/docs`, com persistência no PostgreSQL do Supabase via `DATABASE_URL` no Render.

A nomenclatura de banco segue `app.txt`: `descargas(id, barco, proprietario, data_hora, status)` e `pecas(id, id_descarga, numero_peca, peso_kg, categoria, segundo_furo, lombo, destino, data_registro)`.

A migration `database/migrations/001_operational_schema.sql` é manual; compare e faça backup do banco Supabase existente antes de executá-la. Ela não roda durante startup.
