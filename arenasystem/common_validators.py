from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from PIL import Image, UnidentifiedImageError


def validate_image_upload(file):
    if not file:
        return
    if file.size <= 0:
        raise ValidationError('Arquivo vazio nao e permitido.')
    if file.size > settings.IMAGE_UPLOAD_MAX_SIZE:
        raise ValidationError('Imagem excede o tamanho maximo permitido.')

    extension = Path(file.name).suffix.lower().lstrip('.')
    if extension not in settings.ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError('Formato de imagem nao permitido.')

    content_type = getattr(file, 'content_type', '')
    if content_type and content_type not in settings.ALLOWED_IMAGE_MIME_TYPES:
        raise ValidationError('Tipo MIME de imagem nao permitido.')

    position = file.tell() if hasattr(file, 'tell') else None
    try:
        image = Image.open(file)
        image.verify()
    except (UnidentifiedImageError, OSError):
        raise ValidationError('Arquivo de imagem invalido ou corrompido.')
    finally:
        if position is not None:
            file.seek(position)
