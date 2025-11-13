#!/bin/sh

# Isto garante que o script falhe se qualquer comando falhar
set -e

# 1. Executa as Migrações da Base de Dados
echo "Applying database migrations..."
/usr/local/bin/python manage.py migrate

# 2. Executa o Collectstatic (para o S3)
echo "Collecting static files..."
/usr/local/bin/python manage.py collectstatic --noinput

# 3. Inicia o Servidor Gunicorn
echo "Starting Gunicorn server..."
exec gunicorn core.wsgi:application --bind 0.0.0.0:8000

# 4. Cria superuser
echo "Creating superuser (if env vars present)..."
/usr/local/bin/python create_superuser.py