from django.apps import AppConfig


class NotificacoesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notificacoes'
    verbose_name = 'Notificações'

    def ready(self):
        # Registra os signals quando o app é carregado
        import notificacoes.signals