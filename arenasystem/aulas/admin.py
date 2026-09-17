from django.contrib import admin
from .models import Turma, CheckIn


@admin.register(Turma)
class TurmaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'professor', 'quadra', 'dias_semana', 'horario', 'vagas_disponiveis', 'ativa')
    list_filter = ('ativa', 'quadra', 'professor')
    filter_horizontal = ('alunos',)


@admin.register(CheckIn)
class CheckInAdmin(admin.ModelAdmin):
    list_display = ('aluno', 'turma', 'data', 'horario', 'presente')
    list_filter = ('presente', 'data', 'turma')
    search_fields = ('aluno__username', 'aluno__first_name')
    date_hierarchy = 'data'
from .models import SolicitacaoMatricula, FilaEspera


@admin.register(SolicitacaoMatricula)
class SolicitacaoMatriculaAdmin(admin.ModelAdmin):
    list_display = ['aluno', 'turma', 'tipo', 'status', 'data_solicitacao']
    list_filter = ['status', 'tipo', 'data_solicitacao']
    search_fields = ['aluno__username', 'aluno__first_name', 'turma__nome']
    readonly_fields = ['data_solicitacao', 'data_resposta']


@admin.register(FilaEspera)
class FilaEsperaAdmin(admin.ModelAdmin):
    list_display = ['turma', 'posicao', 'aluno', 'status', 'data_entrada']
    list_filter = ['status', 'turma']
    search_fields = ['aluno__username', 'turma__nome']
    ordering = ['turma', 'posicao']