# 1. Imagem Base
FROM python:3.11-slim

# 2. Instala 'dos2unix' (para corrigir quebras de linha do Windows)
#    Isto é essencial para o 'entrypoint.sh' funcionar.
RUN apt-get update && apt-get install -y dos2unix && rm -rf /var/lib/apt/lists/*

# 3. Variáveis de Ambiente
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 4. Diretório de Trabalho
WORKDIR /app

# 5. Instalação de Dependências
#    Copiamos o requirements.txt primeiro para aproveitar o cache do Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copia TODO o código (incluindo entrypoint.sh)
COPY . .

# 7. Corrige e prepara o script de arranque
#    Executa o dos2unix DEPOIS de o ficheiro ser copiado
RUN dos2unix /app/entrypoint.sh
RUN dos2unix /app/manage.py
RUN chmod +x /app/entrypoint.sh

# 8. Exposição da Porta
EXPOSE 8000

# 9. Comando Padrão (agora aponta para o script corrigido)
CMD ["/app/entrypoint.sh"]