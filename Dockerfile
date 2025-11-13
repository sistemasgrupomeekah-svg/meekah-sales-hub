# 1. Imagem Base
FROM python:3.11-slim

# 2. Variáveis de Ambiente
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 3. Diretório de Trabalho
WORKDIR /app

# 4. Instalação de Dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copia o Código
COPY . .

# 6. Correção do manage.py (Remove caracteres do Windows por segurança)
RUN apt-get update && apt-get install -y dos2unix && \
    dos2unix /app/manage.py && \
    chmod +x /app/manage.py && \
    rm -rf /var/lib/apt/lists/*

# 7. CRIAÇÃO DO SCRIPT PYTHON (Superusuário)
#    Criado internamente para evitar erros de formatação
RUN printf 'import os\n\
import django\n\
from django.contrib.auth import get_user_model\n\
from django.db import IntegrityError\n\
\n\
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")\n\
django.setup()\n\
\n\
User = get_user_model()\n\
username = os.environ.get("DJANGO_SUPERUSER_USERNAME")\n\
email = os.environ.get("DJANGO_SUPERUSER_EMAIL")\n\
password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")\n\
\n\
if username and email and password:\n\
    try:\n\
        if not User.objects.filter(username=username).exists():\n\
            print(f"Criando superusuario: {username}")\n\
            User.objects.create_superuser(username=username, email=email, password=password)\n\
        else:\n\
            print(f"Superusuario {username} ja existe.")\n\
    except IntegrityError:\n\
        print(f"Aviso: O usuario {username} ja existia. Continuando...")\n\
else:\n\
    print("Variaveis de superusuario nao encontradas. Pulando.")\n' > /app/create_superuser.py

# 8. CRIAÇÃO DO ENTRYPOINT (O Script de Arranque)
#    Criado internamente para garantir quebras de linha Linux (\n)
RUN printf '#!/bin/sh\n\
set -e\n\
echo "Applying database migrations..."\n\
python manage.py migrate\n\
echo "Checking for superuser creation..."\n\
python create_superuser.py\n\
echo "Collecting static files..."\n\
python manage.py collectstatic --noinput\n\
echo "Starting Gunicorn..."\n\
exec gunicorn core.wsgi:application --bind 0.0.0.0:8000\n' > /app/entrypoint.sh

# 9. Permissões de Execução
RUN chmod +x /app/entrypoint.sh

# 10. Exposição da Porta
EXPOSE 8000

# 11. Comando Padrão
CMD ["/app/entrypoint.sh"]