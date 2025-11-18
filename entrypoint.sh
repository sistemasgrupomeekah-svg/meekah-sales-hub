#!/bin/sh

# Isto garante que o script falhe se qualquer comando falhar
set -e

# Redirecionar stdout para stderr para aparecer nos logs do App Runner
exec 2>&1

echo "========================================" >&2
echo "🚀 INICIANDO ENTRYPOINT.SH" >&2
echo "========================================" >&2

# 1. Verificar integridade do banco
echo "1️⃣ Checking Database Integrity..." >&2
/usr/local/bin/python fix_db.py 2>&1 || echo "⚠️ fix_db.py falhou, continuando..." >&2

# 2. Executa as Migrações da Base de Dados
echo "2️⃣ Applying database migrations..." >&2
/usr/local/bin/python manage.py migrate 2>&1

# 3. Cria superuser
echo "3️⃣ Creating superuser (if env vars present)..." >&2
/usr/local/bin/python create_superuser.py 2>&1 || echo "⚠️ Superuser não criado" >&2

# 4. Executa o Collectstatic (para o S3)
echo "4️⃣ Collecting static files..." >&2
echo "📦 Bucket: $AWS_STORAGE_BUCKET_NAME" >&2
echo "🌎 Region: $AWS_S3_REGION_NAME" >&2
/usr/local/bin/python manage.py collectstatic --noinput 2>&1

# 5. Inicia o Servidor Gunicorn
echo "5️⃣ Starting Gunicorn server..." >&2
echo "========================================" >&2
exec gunicorn core.wsgi:application --bind 0.0.0.0:8000 --access-logfile - --error-logfile -