# 1. Imagem Base
FROM python:3.11-slim

# 2. Variáveis de Ambiente
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 3. Diretório de Trabalho
WORKDIR /app

# 4. Dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copia o Código
COPY . .

# 6. Correção de formatação (Windows -> Linux)
RUN apt-get update && apt-get install -y dos2unix && \
    dos2unix /app/manage.py && \
    chmod +x /app/manage.py && \
    rm -rf /var/lib/apt/lists/*

# 7. CRIAÇÃO DO SCRIPT DE CORREÇÃO DE BANCO (O SALVADOR)
#    Este script verifica se as tabelas faltam e limpa o histórico para forçar a criação.
RUN printf 'import os\n\
import django\n\
from django.db import connection\n\
from django.db.migrations.recorder import MigrationRecorder\n\
\n\
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")\n\
django.setup()\n\
\n\
def fix_migrations():\n\
    print("Verificando integridade do banco de dados...")\n\
    tables = connection.introspection.table_names()\n\
    # Mapeamento App -> Tabela Principal\n\
    apps_check = {\n\
        "common": "vendas_cliente",\n\
        "comissoes": "vendas_lotepagamentocomissao",\n\
        "vendas": "vendas_venda"\n\
    }\n\
    \n\
    recorder = MigrationRecorder(connection)\n\
    for app, table in apps_check.items():\n\
        if table not in tables:\n\
            print(f"ALERTA: Tabela {table} nao existe. Limpando historico de {app} para recriar...")\n\
            recorder.migration_qs.filter(app=app).delete()\n\
        else:\n\
            print(f"Tabela {table} existe. OK.")\n\
\n\
if __name__ == "__main__":\n\
    try:\n\
        fix_migrations()\n\
    except Exception as e:\n\
        print(f"Erro ao verificar banco (pode ser a primeira execucao): {e}")\n' > /app/fix_db.py

# 8. CRIAÇÃO DO SCRIPT DE SUPERUSUÁRIO
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
    except IntegrityError:\n\
        print("Aviso: Usuario ja existe. Continuando.")\n' > /app/create_superuser.py

# 9. CRIAÇÃO DO ENTRYPOINT (Atualizado com o fix_db.py)
RUN printf '#!/bin/sh\n\
set -e\n\
echo "1. Checking Database Integrity..."\n\
python fix_db.py\n\
echo "2. Applying migrations..."\n\
python manage.py migrate\n\
echo "3. Checking Superuser..."\n\
python create_superuser.py\n\
echo "4. Collecting statics..."\n\
python manage.py collectstatic --noinput\n\
echo "5. Starting Server..."\n\
exec gunicorn core.wsgi:application --bind 0.0.0.0:8000\n' > /app/entrypoint.sh

RUN chmod +x /app/entrypoint.sh

# 10. Exposição e Comando
EXPOSE 8000
CMD ["/app/entrypoint.sh"]