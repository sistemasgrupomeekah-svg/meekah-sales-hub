# vendas/storage_backends.py

from storages.backends.s3boto3 import S3Boto3Storage

class MediaStorage(S3Boto3Storage):
    """
    Storage customizado para os ficheiros de Mídia (Uploads).
    Isto garante que eles sejam salvos na pasta 'media/' dentro do bucket S3.
    """
    location = 'media'
    file_overwrite = False # Não sobrescreve ficheiros com o mesmo nome