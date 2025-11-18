from storages.backends.s3boto3 import S3Boto3Storage

class StaticStorage(S3Boto3Storage):
    """Storage para arquivos estáticos (CSS, JS, imagens do site)"""
    location = "static"
    default_acl = "public-read"

class MediaStorage(S3Boto3Storage):
    """Storage para uploads de usuários (documentos, anexos, vendas)"""
    location = "media"
    default_acl = "private"  # 🔒 Privado por segurança
    file_overwrite = False   # Não sobrescrever arquivos com mesmo nome