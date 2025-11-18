import os
import sys
from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(DEBUG=(bool, False))

# 🔧 SÓ LÊ O .ENV SE NÃO ESTIVER EM PRODUÇÃO
# Detecta se está rodando no AWS (App Runner, ECS, Lambda, etc.)
if not os.environ.get('AWS_EXECUTION_ENV') and not os.environ.get('AWS_REGION'):
    env_file = os.path.join(BASE_DIR, '.env')
    if os.path.exists(env_file):
        environ.Env.read_env(env_file)
        print("📄 Lendo .env local", file=sys.stderr)
    else:
        print("⚠️ Arquivo .env não encontrado", file=sys.stderr)
else:
    print("☁️ Ambiente AWS detectado - usando variáveis de ambiente", file=sys.stderr)

SECRET_KEY = env('DJANGO_SECRET_KEY')

# --- DEBUG / HOSTS / CSRF ---
DEBUG = env.bool('DJANGO_DEBUG', default=False)

# 🔍 DEBUG TEMPORÁRIO
print(f"🔍 DEBUG: {DEBUG}", file=sys.stderr)
print(f"🔍 DJANGO_DEBUG env var: {os.environ.get('DJANGO_DEBUG')}", file=sys.stderr)
print(f"🔍 AWS_STORAGE_BUCKET_NAME: {os.environ.get('AWS_STORAGE_BUCKET_NAME')}", file=sys.stderr)

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[])

if DEBUG:
    ALLOWED_HOSTS.extend(['localhost', '127.0.0.1'])
    print("⚠️ MODO DESENVOLVIMENTO - USANDO STORAGE LOCAL", file=sys.stderr)
else:
    print("✅ MODO PRODUÇÃO - USANDO S3", file=sys.stderr)


# --- APPS ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Apps do projeto
    'common.apps.CommonConfig',
    'comissoes.apps.ComissoesConfig',
    'vendas',

    # Terceiros
    'storages',
    'django.contrib.humanize',
]


# --- MIDDLEWARE ---
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


# --- Templates ---
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


# --- Banco de dados ---
DATABASES = {
    'default': env.db(
        'DATABASE_URL',
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}"
    )
}


# --- Validações de senha ---
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# --- Localização ---
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_L10N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# --- Login ---
LOGIN_URL = 'login'


# ============================================================
# ⚙️ CONFIGURAÇÃO DE STATIC E MEDIA
# ============================================================

if DEBUG:
    # --- MODO DESENVOLVIMENTO ---
    STATIC_URL = '/static/'
    STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

    MEDIA_URL = '/media/'
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

else:
    # --- MODO PRODUÇÃO (DEBUG=False) ---
    AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = env('AWS_S3_REGION_NAME', default='us-east-2')
    AWS_S3_SIGNATURE_VERSION = "s3v4"

    AWS_S3_FILE_OVERWRITE = False
    AWS_DEFAULT_ACL = None

    # Caminhos de static e media no bucket
    STATICFILES_STORAGE = "core.storages.StaticStorage"
    DEFAULT_FILE_STORAGE = "core.storages.MediaStorage"

    # URLs públicas para cada tipo
    STATIC_URL = f"https://{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com/static/"
    MEDIA_URL = f"https://{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com/media/"

    # Local temporário dentro do container
    STATIC_ROOT = "/app/staticfiles_prod"