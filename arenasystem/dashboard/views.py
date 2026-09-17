from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import timedelta

from arena.models import Mensalidade, Matricula, Quadra
from aulas.models import CheckIn, Turma
from loja.models import Venda
from manutencao.models import Manutencao


@staff_member_required
def dashboard(request):
    """Renderiza a página principal do dashboard."""
    hoje = timezone.now().date()
    inicio_mes = hoje.replace(day=1)
    ultimos_30 = hoje - timedelta(days=30)

    # 💰 Financeiro
    receita_mensalidades = Mensalidade.objects.filter(
        status='pago', data_pagamento__gte=inicio_mes
    ).aggregate(t=Sum('valor'))['t'] or 0

    receita_loja = Venda.objects.filter(
        status='paga', data__gte=inicio_mes
    ).aggregate(t=Sum('total'))['t'] or 0

    inadimplencia = Mensalidade.objects.filter(
        status__in=['pendente', 'atrasado'],
        vencimento__lt=hoje
    ).aggregate(t=Sum('valor'))['t'] or 0

    # 👥 Alunos
    alunos_ativos = Matricula.objects.filter(ativa=True).count()
    novos_alunos = Matricula.objects.filter(data_inicio__gte=inicio_mes).count()

    # 🏐 Frequência
    checkins_30d = CheckIn.objects.filter(
        data__gte=ultimos_30, presente=True
    ).count()
    turmas_ativas = Turma.objects.filter(ativa=True).count()

    # 🔧 Operacional
    manutencoes_pendentes = Manutencao.objects.filter(
        status__in=['agendada', 'em_andamento']
    ).count()

    context = {
        'receita_mensalidades': receita_mensalidades,
        'receita_loja': receita_loja,
        'receita_total': receita_mensalidades + receita_loja,
        'inadimplencia': inadimplencia,
        'alunos_ativos': alunos_ativos,
        'novos_alunos': novos_alunos,
        'checkins_30d': checkins_30d,
        'turmas_ativas': turmas_ativas,
        'manutencoes_pendentes': manutencoes_pendentes,
    }
    return render(request, 'dashboard/index.html', context)


# ─────────────────────────────────────────────────────────
#   ENDPOINTS JSON (dados para os gráficos e futura API)
# ─────────────────────────────────────────────────────────

@staff_member_required
def api_receita_mensal(request):
    """Receita por mês nos últimos 12 meses."""
    inicio = timezone.now().date() - timedelta(days=365)

    mensalidades = (
        Mensalidade.objects
        .filter(status='pago', data_pagamento__gte=inicio)
        .annotate(mes=TruncMonth('data_pagamento'))
        .values('mes')
        .annotate(total=Sum('valor'))
        .order_by('mes')
    )

    vendas = (
        Venda.objects
        .filter(status='paga', data__gte=inicio)
        .annotate(mes=TruncMonth('data'))
        .values('mes')
        .annotate(total=Sum('total'))
        .order_by('mes')
    )

    # Formata para o Chart.js
    dados = {
        'mensalidades': [
            {'mes': m['mes'].strftime('%b/%Y'), 'total': float(m['total'] or 0)}
            for m in mensalidades
        ],
        'loja': [
            {'mes': v['mes'].strftime('%b/%Y'), 'total': float(v['total'] or 0)}
            for v in vendas
        ],
    }
    return JsonResponse(dados)


@staff_member_required
def api_ranking_frequencia(request):
    """Top 10 alunos mais frequentes nos últimos 30 dias."""
    ultimos_30 = timezone.now().date() - timedelta(days=30)
    dados = (
        CheckIn.objects
        .filter(data__gte=ultimos_30, presente=True)
        .values('aluno__first_name', 'aluno__last_name', 'aluno__username')
        .annotate(total=Count('id'))
        .order_by('-total')[:10]
    )

    resultado = [
        {
            'nome': f"{d['aluno__first_name']} {d['aluno__last_name']}".strip()
                    or d['aluno__username'],
            'total': d['total'],
        }
        for d in dados
    ]
    return JsonResponse(resultado, safe=False)


@staff_member_required
def api_status_mensalidades(request):
    """Distribuição de status das mensalidades do mês atual."""
    inicio_mes = timezone.now().date().replace(day=1)
    dados = (
        Mensalidade.objects
        .filter(mes_referencia=inicio_mes)
        .values('status')
        .annotate(total=Count('id'))
    )
    return JsonResponse(list(dados), safe=False)


@staff_member_required
def api_ocupacao_quadras(request):
    """Quantos check-ins por quadra nos últimos 30 dias."""
    ultimos_30 = timezone.now().date() - timedelta(days=30)
    dados = (
        CheckIn.objects
        .filter(data__gte=ultimos_30, presente=True)
        .values('turma__quadra__nome')
        .annotate(total=Count('id'))
        .order_by('-total')
    )

    resultado = [
        {'quadra': d['turma__quadra__nome'] or 'Sem quadra', 'total': d['total']}
        for d in dados
    ]
    return JsonResponse(resultado, safe=False)