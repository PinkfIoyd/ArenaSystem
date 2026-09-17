from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Turma, CheckIn


@login_required
def minhas_turmas(request):
    turmas = request.user.turmas.filter(ativa=True)
    return render(request, 'aulas/minhas_turmas.html', {'turmas': turmas})


@login_required
def fazer_checkin(request, turma_id):
    turma = get_object_or_404(Turma, id=turma_id, ativa=True)

    if request.user not in turma.alunos.all():
        messages.error(request, "Você não está matriculado nesta turma.")
        return redirect('minhas_turmas')

    hoje = timezone.now().date()
    checkin, criado = CheckIn.objects.get_or_create(
        aluno=request.user,
        turma=turma,
        data=hoje,
        defaults={'presente': True}
    )

    if criado:
        messages.success(request, f"Check-in realizado com sucesso na turma {turma.nome}! 🏐")
    else:
        messages.info(request, "Você já fez check-in hoje nesta turma.")

    return redirect('minhas_turmas')