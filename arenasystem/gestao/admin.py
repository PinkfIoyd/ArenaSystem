from django.contrib import admin

from .models import AuditLog, BloqueioQuadra, ContaFinanceira, ContratoMatricula, FaixaPrecoReserva, Lead, ReservaQuadra


@admin.register(ReservaQuadra)
class ReservaQuadraAdmin(admin.ModelAdmin):
    list_display = ('quadra', 'cliente_nome', 'data', 'hora_inicio', 'hora_fim', 'status', 'valor')
    list_filter = ('arena', 'status', 'data')
    search_fields = ('cliente_nome', 'cliente_telefone', 'quadra__nome')


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('nome', 'modalidade_interesse', 'etapa', 'origem', 'responsavel', 'criado_em')
    list_filter = ('arena', 'etapa', 'origem')
    search_fields = ('nome', 'telefone', 'email', 'modalidade_interesse')


@admin.register(ContaFinanceira)
class ContaFinanceiraAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'tipo', 'categoria', 'valor', 'vencimento', 'status')
    list_filter = ('arena', 'tipo', 'status', 'vencimento')
    search_fields = ('descricao', 'categoria', 'fornecedor')


@admin.register(ContratoMatricula)
class ContratoMatriculaAdmin(admin.ModelAdmin):
    list_display = ('matricula', 'status', 'data_aceite', 'criado_em')
    list_filter = ('arena', 'status')


@admin.register(BloqueioQuadra)
class BloqueioQuadraAdmin(admin.ModelAdmin):
    list_display = ('quadra', 'data', 'hora_inicio', 'hora_fim', 'categoria', 'motivo')
    list_filter = ('arena', 'categoria', 'data')


@admin.register(FaixaPrecoReserva)
class FaixaPrecoReservaAdmin(admin.ModelAdmin):
    list_display = ('quadra', 'dia_semana', 'hora_inicio', 'hora_fim', 'valor', 'ativa')
    list_filter = ('arena', 'dia_semana', 'ativa')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('acao', 'entidade_tipo', 'entidade_id', 'usuario', 'arena', 'criado_em')
    list_filter = ('arena', 'acao', 'entidade_tipo', 'criado_em')
    readonly_fields = ('arena', 'usuario', 'acao', 'entidade_tipo', 'entidade_id', 'valores_anteriores', 'valores_novos', 'metadados', 'ip', 'criado_em')
