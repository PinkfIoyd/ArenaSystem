from django.contrib import admin
from django.utils import timezone
from .models import (
    AccessIntegrationEvent, AccessPoint, AccessVisit, ArenaOperationalSettings,
    Matricula, Mensalidade, PlanAccessWindow, Plano, Quadra,
)


@admin.register(Quadra)
class QuadraAdmin(admin.ModelAdmin):
    list_display = ('nome', 'tipo_areia', 'ativa')
    list_filter = ('ativa',)


@admin.register(Plano)
class PlanoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'valor', 'tipo_acesso', 'frequencia_semanal', 'ativo')
    list_filter = ('tipo_acesso', 'ativo')


admin.site.register(PlanAccessWindow)
admin.site.register(ArenaOperationalSettings)
admin.site.register(AccessVisit)
admin.site.register(AccessPoint)
admin.site.register(AccessIntegrationEvent)


@admin.register(Matricula)
class MatriculaAdmin(admin.ModelAdmin):
    list_display = ('aluno', 'plano', 'data_inicio', 'ativa')
    list_filter = ('ativa', 'plano')
    search_fields = ('aluno__username', 'aluno__first_name', 'aluno__last_name')


@admin.register(Mensalidade)
class MensalidadeAdmin(admin.ModelAdmin):
    list_display = ('matricula', 'mes_referencia', 'valor', 'vencimento', 'status')
    list_filter = ('status', 'mes_referencia')
    search_fields = ('matricula__aluno__username',)
    actions = ['marcar_como_pago']

    def marcar_como_pago(self, request, queryset):
        queryset.update(status='pago', data_pagamento=timezone.now().date())
    marcar_como_pago.short_description = "Marcar selecionadas como pagas"
