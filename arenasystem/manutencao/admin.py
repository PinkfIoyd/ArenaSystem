from django.contrib import admin
from django.utils import timezone
from .models import Manutencao


@admin.register(Manutencao)
class ManutencaoAdmin(admin.ModelAdmin):
    list_display = (
        'quadra', 'tipo', 'data_agendada', 'status',
        'custo', 'responsavel'
    )
    list_filter = ('status', 'tipo', 'quadra')
    search_fields = ('descricao', 'responsavel', 'quadra__nome')
    date_hierarchy = 'data_agendada'
    actions = ['marcar_concluida', 'marcar_em_andamento']

    fieldsets = (
        ('Informações principais', {
            'fields': ('quadra', 'tipo', 'descricao', 'status')
        }),
        ('Datas', {
            'fields': ('data_agendada', 'data_conclusao')
        }),
        ('Financeiro e responsável', {
            'fields': ('custo', 'responsavel')
        }),
    )

    def marcar_concluida(self, request, queryset):
        queryset.update(status='concluida', data_conclusao=timezone.now().date())
    marcar_concluida.short_description = "Marcar como concluída"

    def marcar_em_andamento(self, request, queryset):
        queryset.update(status='em_andamento')
    marcar_em_andamento.short_description = "Marcar como em andamento"