# 1. Imagem Base
# Usamos a imagem "slim" que é mais leve
FROM python:3.11-slim

# 2. Variáveis de Ambiente
# Garante que o output do Python vá direto para o terminal (logs)
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 3. Diretório de Trabalho
# Define o diretório padrão dentro do container
WORKDIR /app

# 4. Instalação de Dependências
# Copia o requirements.txt primeiro para aproveitar o cache do Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copia do Código
# Copia todo o código do projeto para o diretório /app
COPY . .

# 6. Exposição da Porta
# Expõe a porta 8000 (porta padrão do Django/Gunicorn)
EXPOSE 8000

# 7. Comando Padrão (para Produção)
# Este comando será usado em produção. Para desenvolvimento, vamos
# sobrescrevê-lo no docker-compose.yml.
# Assumindo que nosso projeto Django se chamará 'core'
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000"]
