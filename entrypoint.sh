#!/bin/sh

# Isto garante que o script falhe se qualquer comando falhar
set -e

# 1. Verificar integridade do banco
echo "1. Checking Database Integrity..."
/usr/local/bin/python fix_db.py

# 2. Executa as Migrações da Base de Dados
echo "2. Applying database migrations..."
/usr/local/bin/python manage.py migrate

# 3. Cria superuser
echo "3. Creating superuser (if env vars present)..."
/usr/local/bin/python create_superuser.py

# 4. Executa o Collectstatic (para o S3)
echo "4. Collecting static files..."
echo "Bucket: $AWS_STORAGE_BUCKET_NAME"
echo "Region: $AWS_S3_REGION_NAME"
/usr/local/bin/python manage.py collectstatic --noinput

# 5. Inicia o Servidor Gunicorn
echo "5. Starting Gunicorn server..."
exec gunicorn core.wsgi:application --bind 0.0.0.0:8000