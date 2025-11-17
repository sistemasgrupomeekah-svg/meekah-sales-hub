import os
from pathlib import Path
import environ 

BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env(
    # Define o valor padrão para DEBUG como False (Produção)
    DEBUG=(bool, False) 
)
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

SECRET_KEY = env('DJANGO_SECRET_KEY')

# --- (ATUALIZADO) DEBUG, ALLOWED_HOSTS e CSRF ---
# Lê o DEBUG do .env. Se não encontrar, assume 'False' (Produção)
DEBUG = env.bool('DJANGO_DEBUG', default=False)

# Lê os hosts do .env. Em produção, deve ser:
# ALLOWED_HOSTS=subdominio.awsapprunner.com,meudominio.com
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])

# Lista de origens confiáveis para CSRF (Necessário para o App Runner / HTTPS)
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[])

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
    
    # Apps do Projeto
    'common.apps.CommonConfig',
    'comissoes.apps.ComissoesConfig',
    'vendas',
    
    # Terceiros
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

# --- Banco de Dados ---
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

# Login
LOGIN_URL = 'login'

# --- Configuração de Ficheiros Estáticos (CSS, JS) e Mídia (Uploads) ---

if DEBUG:
    # --- MODO DESENVOLVIMENTO (DEBUG=True) ---
    
    STATIC_URL = 'static/'
    STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static'),]
    # Pasta onde o collectstatic coloca os ficheiros localmente
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles') 
    
    MEDIA_URL = '/media/'
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media') 

else:
    # --- MODO PRODUÇÃO (DEBUG=False) ---
    # (Servindo a partir do AWS S3)
    
    # 1. Credenciais AWS (lidas do .env)
    AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = env('AWS_S3_REGION_NAME', default='us-east-2')
    AWS_S3_SIGNATURE_VERSION = "s3v4"
    
    # 2. Configurações do S3
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com'
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400', # Cache de 1 dia
    }
    
    # Lê do .env; se não encontrar, usa None como padrão (recomendado)
    AWS_DEFAULT_ACL = env('AWS_DEFAULT_ACL', default=None)
    
    AWS_QUERYSTRING_AUTH = False 

    # 3. ESTÁTICOS (CSS/JS)
    AWS_LOCATION = 'static'
    STATICFILES_STORAGE = "storages.backends.s3boto3.S3StaticStorage"
    STATIC_URL = f"https://{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/"
    
    # 4. MÍDIA (Uploads)
    # Usa o storage customizado em vendas/storage_backends.py
    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
    MEDIA_URL = f"https://{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/"

    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles_prod')