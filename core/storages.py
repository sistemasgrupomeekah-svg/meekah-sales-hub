from storages.backends.s3boto3 import S3Boto3Storage

class StaticStorage(S3Boto3Storage):
    """Storage para arquivos estáticos (CSS, JS, imagens do site)"""
    location = 'static'
    file_overwrite = False

class MediaStorage(S3Boto3Storage):
    """Storage para arquivos de upload dos usuários"""
    location = 'media'
    file_overwrite = False
    querystring_auth = True  # Gera URLs assinadas
    querystring_expire = 3600  # Expira em 1 hora