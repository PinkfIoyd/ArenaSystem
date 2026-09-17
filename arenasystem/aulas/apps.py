from django.apps import AppConfig


class AulasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'aulas'

    def ready(self):
        # Importa os signals quando o app carrega
        from . import signals  # noqa