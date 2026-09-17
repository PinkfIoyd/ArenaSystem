from django.contrib import admin
from .models import Notificacao


@admin.register(Notificacao)
class NotificacaoAdmin(admin.ModelAdmin):
    list_display = (
        'destinatario', 'tipo', 'titulo',
        'lida', 'enviada_email', 'criada_em'
    )
    list_filter = ('tipo', 'lida', 'enviada_email', 'criada_em')
    search_fields = ('destinatario__username', 'titulo', 'mensagem')
    date_hierarchy = 'criada_em'
    readonly_fields = ('criada_em', 'enviada_email')
    actions = ['marcar_como_lida']

    def marcar_como_lida(self, request, queryset):
        queryset.update(lida=True)
    marcar_como_lida.short_description = "Marcar como lida"
from .models import NotificacaoAdmin


@admin.register(NotificacaoAdmin)
class NotificacaoAdminAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'tipo', 'destinatario', 'lida', 'criada_em']
    list_filter = ['tipo', 'lida', 'criada_em']
    search_fields = ['titulo', 'mensagem']
    readonly_fields = ['criada_em', 'lida_em']