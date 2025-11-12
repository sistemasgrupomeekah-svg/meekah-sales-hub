import os
from pathlib import Path
import environ 
# import dj_database_url # (Não é necessário, o django-environ já o inclui)

BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env(
    # Define o valor padrão para DEBUG como False (Produção)
    DEBUG=(bool, False) 
)
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

SECRET_KEY = env('DJANGO_SECRET_KEY')

# --- (ATUALIZADO) DEBUG e ALLOWED_HOSTS ---
# Lê o DEBUG do .env. Se não existir, assume 'False' (Produção)
DEBUG = env.bool('DEBUG', default=False)

# Lê os hosts do .env. Em produção, deve ser:
# ALLOWED_HOSTS=subdominio.awsapprunner.com,meudominio.com
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])
# Se DEBUG=True, adiciona o localhost para facilitar
if DEBUG:
    ALLOWED_HOSTS.extend(['localhost', '127.0.0.1'])


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'common.apps.CommonConfig',
    'comissoes.apps.ComissoesConfig',
    'vendas',
    'storages',
    'django.contrib.humanize',
    
]
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
ROOT_URLCONF = 'core.urls'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
WSGI_APPLICATION = 'core.wsgi.application'

# --- (ATUALIZADO) Banco de Dados ---
# Lê o 'DATABASE_URL' do .env (ex: postgres://user:pass@host/db)
# Se não encontrar, usa o sqlite3 local (para desenvolvimento)
DATABASES = {
    'default': env.db(
        'DATABASE_URL', 
        default=f'sqlite:///{BASE_DIR / "db.sqlite3"}'
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]

# --- Configs de Localização ---
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_L10N = True 
USE_TZ = True
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_URL = 'login'

# --- (ATUALIZADO) Configuração de Ficheiros Estáticos (CSS, JS) e Mídia (Uploads) ---

if DEBUG:
    # --- MODO DESENVOLVIMENTO (DEBUG=True) ---
    # (Servindo localmente, como estava antes)
    
    STATIC_URL = 'static/'
    STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static'),]
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles') # Pasta para 'collectstatic' local
    
    MEDIA_URL = '/media/'
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media') # Onde os uploads locais ficam

else:
    # --- MODO PRODUÇÃO (DEBUG=False) ---
    # (Servindo a partir do AWS S3)
    
    # 1. Credenciais AWS (lidas do .env)
    AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME')
    
    # 2. Configurações do S3
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400', # Cache de 1 dia
    }
    AWS_DEFAULT_ACL = env('AWS_DEFAULT_ACL', default=None) # Permite que os ficheiros sejam vistos publicamente
    AWS_QUERYSTRING_AUTH = False # Remove URLs assinadas (mais limpo)

    # 3. ESTÁTICOS (CSS/JS - ficheiros da aplicação)
    # Define a pasta "raiz" dentro do S3 para o 'collectstatic'
    AWS_LOCATION = 'static'
    STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{AWS_LOCATION}/'
    
    # 4. MÍDIA (Uploads do utilizador - comprovativos, contratos, etc.)
    # Usamos um Storage customizado (ver Ficheiro 2) para os colocar na pasta /media/
    DEFAULT_FILE_STORAGE = 'vendas.storage_backends.MediaStorage'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'

    # O 'STATIC_ROOT' local não é mais tão relevante, mas é bom tê-lo
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles_prod')