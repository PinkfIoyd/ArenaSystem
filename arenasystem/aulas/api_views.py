from rest_framework import viewsets, permissions, serializers, status
from rest_framework.response import Response
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from datetime import datetime

from django.utils import timezone
from django.db import transaction
from django.db.models import Q

from .models import AulaOcorrencia, Turma, CheckIn, SolicitacaoMatricula, FilaEspera
from .serializers import (
    AulaOcorrenciaSerializer, TurmaSerializer, CheckInSerializer,
    SolicitacaoMatriculaSerializer, FilaEsperaSerializer,
)
from arena.tenant import get_user_arena
from arena.features import FeatureEnabledMixin
from arena.access_services import access_state
from arena.serializers import AccessVisitSerializer
from gestao.audit import registrar_auditoria, sanitize_audit_text
from usuarios.permissions import require_permission, tem_permissao
from usuarios.models import Usuario
from .checkin_services import (
    CheckInDomainError, active_enrollment_exists, checkin_state_for, ensure_occurrence,
    expire_pending_checkins, notify_checkin, request_mobile_checkin, turma_occurs_on,
)


# ══════════════════════════════════════════════
# TURMAS (já existia, com adições)
# ══════════════════════════════════════════════

class TurmaViewSet(FeatureEnabledMixin, viewsets.ReadOnlyModelViewSet):
    feature_key = 'classes'
    """
    Lista turmas com vagas em tempo real.
    GET /api/turmas/
    GET /api/turmas/{id}/
    POST /api/turmas/{id}/checkin/
    GET /api/turmas/minhas/
    POST /api/turmas/{id}/solicitar-matricula/
    POST /api/turmas/{id}/solicitar-cancelamento/
    POST /api/turmas/{id}/entrar-fila/
    """
    serializer_class = TurmaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Turma.objects.filter(arena=get_user_arena(self.request.user), ativa=True).select_related('professor', 'quadra')
        if self.request.user.papel_efetivo == 'professor':
            qs = qs.filter(professor=self.request.user)
        return qs

    @action(detail=False, methods=['get'])
    def minhas(self, request):
        turmas = request.user.turmas.filter(arena=get_user_arena(request.user), ativa=True)
        serializer = self.get_serializer(turmas, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def checkin(self, request, pk=None):
        turma = self.get_object()
        try:
            checkin = request_mobile_checkin(turma, request.user)
        except CheckInDomainError as exc:
            return Response(exc.payload(), status=exc.http_status)
        registrar_auditoria(
            request, turma.arena, 'checkin.requested', checkin,
            novos={'status': checkin.status, 'turma': turma.id, 'origem': checkin.origem},
        )
        return Response(
            {
                'detail': 'Check-in solicitado. Aguarde a validacao da arena.',
                'checkin': CheckInSerializer(checkin, context={'request': request}).data,
                'checkin_id': checkin.id,
                'turma_id': turma.id,
                'checkin_hoje': True,
            },
            status=status.HTTP_202_ACCEPTED,
        )

    @action(detail=True, methods=['get'])
    def roster(self, request, pk=None):
        turma = self.get_object()
        if request.user.papel_efetivo == 'professor':
            allowed = turma.professor_id == request.user.id and tem_permissao(request.user, 'checkin.own.manage')
        else:
            allowed = tem_permissao(request.user, 'checkin.manage')
        if not allowed:
            raise PermissionDenied('Voce nao pode consultar os alunos desta turma.')
        today = timezone.localdate()
        checkins = {
            item.aluno_id: item for item in CheckIn.objects.filter(arena=turma.arena, turma=turma, data=today)
        }
        students = []
        for student in turma.alunos.filter(arena=turma.arena, is_active=True).order_by('first_name', 'username'):
            item = checkins.get(student.id)
            students.append({
                'id': student.id,
                'name': student.get_full_name() or student.username,
                'photo': request.build_absolute_uri(student.foto.url) if student.foto else None,
                'checkin_id': item.id if item else None,
                'status': item.status if item else None,
                'active_enrollment': active_enrollment_exists(student, turma.arena, today),
            })
        return Response({'turma': turma.id, 'date': today, 'students': students})

    @action(detail=True, methods=['post'], url_path='solicitar-matricula')
    def solicitar_matricula(self, request, pk=None):
        """Aluno solicita ingresso na turma."""
        turma = self.get_object()
        usuario = request.user

        # Já matriculado?
        if usuario in turma.alunos.all():
            return Response(
                {'detail': 'Você já está matriculado nesta turma.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Já tem solicitação pendente?
        ja_existe = SolicitacaoMatricula.objects.filter(
            aluno=usuario, turma=turma, tipo='matricula', status='pendente'
        ).exists()
        if ja_existe:
            return Response(
                {'detail': 'Você já tem uma solicitação pendente para esta turma.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Cria a solicitação
        solicitacao = SolicitacaoMatricula.objects.create(
            arena=get_user_arena(request.user),
            aluno=usuario,
            turma=turma,
            tipo='matricula',
            observacao_aluno=request.data.get('observacao', ''),
        )

        return Response(
            {
                'detail': '✓ Solicitação enviada! Aguarde a aprovação da arena.',
                'solicitacao_id': solicitacao.id,
            },
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'], url_path='solicitar-cancelamento')
    def solicitar_cancelamento(self, request, pk=None):
        """Aluno pede para sair da turma."""
        turma = self.get_object()
        usuario = request.user

        if usuario not in turma.alunos.all():
            return Response(
                {'detail': 'Você não está matriculado nesta turma.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        ja_existe = SolicitacaoMatricula.objects.filter(
            aluno=usuario, turma=turma, tipo='cancelamento', status='pendente'
        ).exists()
        if ja_existe:
            return Response(
                {'detail': 'Você já solicitou cancelamento desta turma.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        turma.alunos.remove(usuario)
        registrar_auditoria(request, get_user_arena(request.user), 'matricula.cancelada_aluno', turma, anteriores={'aluno': usuario.id, 'turma': turma.id})
        solicitacao = SolicitacaoMatricula.objects.create(
            arena=get_user_arena(request.user),
            aluno=usuario,
            turma=turma,
            tipo='cancelamento',
            status='aprovada',
            data_resposta=timezone.now(),
            observacao_aluno=request.data.get('observacao', ''),
        )

        return Response(
            {
                'detail': 'Matrícula cancelada e aluno removido da turma.',
                'solicitacao_id': solicitacao.id,
            },
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'], url_path='entrar-fila')
    def entrar_fila(self, request, pk=None):
        """Aluno entra na fila de espera quando turma está cheia."""
        turma = self.get_object()
        usuario = request.user

        if usuario in turma.alunos.all():
            return Response(
                {'detail': 'Você já está matriculado nesta turma.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if turma.vagas_disponiveis > 0:
            return Response(
                {'detail': 'Há vagas! Solicite matrícula direto.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Já está na fila?
        ja_na_fila = FilaEspera.objects.filter(
            aluno=usuario, turma=turma, status='aguardando'
        ).exists()
        if ja_na_fila:
            return Response(
                {'detail': 'Você já está na fila de espera desta turma.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Calcula a próxima posição
        ultima_posicao = FilaEspera.objects.filter(
            turma=turma, status='aguardando'
        ).count()

        FilaEspera.objects.create(
            arena=get_user_arena(request.user),
            aluno=usuario,
            turma=turma,
            posicao=ultima_posicao + 1,
        )

        return Response(
            {'detail': '✓ Você entrou na fila de espera. Será avisado se uma vaga abrir.'},
            status=status.HTTP_201_CREATED
        )


# ══════════════════════════════════════════════
# CHECK-INS (já existia)
# ══════════════════════════════════════════════

class CheckInViewSet(FeatureEnabledMixin, viewsets.ReadOnlyModelViewSet):
    feature_key = 'classes'
    serializer_class = CheckInSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        expire_pending_checkins()
        user = self.request.user
        arena = get_user_arena(user)
        if tem_permissao(user, 'checkin.view'):
            if user.papel_efetivo == 'professor':
                return CheckIn.objects.filter(arena=arena, turma__professor=user).select_related('aluno', 'turma', 'turma__professor', 'ocorrencia')
            return CheckIn.objects.filter(arena=arena).select_related('aluno', 'turma', 'turma__professor', 'ocorrencia')
        return CheckIn.objects.filter(arena=arena, aluno=user).select_related('turma', 'turma__professor', 'ocorrencia')

    @action(detail=False, methods=['get'])
    def me(self, request):
        queryset = CheckIn.objects.filter(
            arena=get_user_arena(request.user), aluno=request.user,
        ).select_related('turma', 'turma__professor', 'ocorrencia')[:100]
        return Response(CheckInSerializer(queryset, many=True, context={'request': request}).data)


def _operator_can_manage(user, checkin):
    if user.papel_efetivo == 'professor':
        return checkin.turma.professor_id == user.id and tem_permissao(user, 'checkin.own.manage')
    return tem_permissao(user, 'checkin.manage')


def _is_admin_role(user):
    return user.papel_efetivo in {'dono', 'administrador', 'superadmin_saas'}


class CanManageCheckIn(permissions.BasePermission):
    def has_permission(self, request, view):
        return tem_permissao(request.user, 'checkin.manage') or tem_permissao(request.user, 'checkin.own.manage')


class AdminCheckInViewSet(FeatureEnabledMixin, viewsets.ReadOnlyModelViewSet):
    feature_key = 'classes'
    serializer_class = CheckInSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageCheckIn]

    def get_queryset(self):
        expire_pending_checkins()
        arena = get_user_arena(self.request.user)
        user = self.request.user
        if not (tem_permissao(user, 'checkin.manage') or tem_permissao(user, 'checkin.own.manage')):
            return CheckIn.objects.none()
        queryset = CheckIn.objects.filter(arena=arena).select_related(
            'aluno', 'turma', 'turma__professor', 'ocorrencia', 'validado_por',
        )
        if user.papel_efetivo == 'professor':
            queryset = queryset.filter(turma__professor=user)
        target_date = self.request.query_params.get('date') or timezone.localdate().isoformat()
        queryset = queryset.filter(data=target_date)
        if self.request.query_params.get('status'):
            queryset = queryset.filter(status=self.request.query_params['status'])
        if self.request.query_params.get('turma'):
            queryset = queryset.filter(turma_id=self.request.query_params['turma'])
        if self.request.query_params.get('professor'):
            queryset = queryset.filter(turma__professor_id=self.request.query_params['professor'])
        return queryset.order_by('turma__horario', 'solicitado_em', 'aluno__first_name')

    def _manageable(self):
        checkin = self.get_object()
        if not _operator_can_manage(self.request.user, checkin):
            raise PermissionDenied('Voce nao pode validar esta turma.')
        return checkin

    @action(detail=False, methods=['get'])
    def today(self, request):
        queryset = self.get_queryset().filter(data=timezone.localdate())
        return Response(CheckInSerializer(queryset, many=True, context={'request': request}).data)

    @action(detail=False, methods=['get', 'patch'], url_path='settings')
    def checkin_settings(self, request):
        if not tem_permissao(request.user, 'checkin.manage'):
            raise PermissionDenied('Voce nao pode alterar a configuracao de check-in.')
        arena = get_user_arena(request.user)
        if request.method == 'GET':
            return Response({
                'checkin_minutes_before': arena.checkin_minutes_before,
                'checkin_minutes_after': arena.checkin_minutes_after,
                'delinquent_checkin_policy': arena.delinquent_checkin_policy,
            })
        before = request.data.get('checkin_minutes_before', arena.checkin_minutes_before)
        after = request.data.get('checkin_minutes_after', arena.checkin_minutes_after)
        policy = request.data.get('delinquent_checkin_policy', arena.delinquent_checkin_policy)
        try:
            before, after = int(before), int(after)
        except (TypeError, ValueError):
            return Response({'detail': 'As janelas devem ser informadas em minutos inteiros.'}, status=400)
        if not 0 <= before <= 180 or not 0 <= after <= 180:
            return Response({'detail': 'Use uma janela entre 0 e 180 minutos.'}, status=400)
        if policy not in {'allow_with_warning', 'block'}:
            return Response({'detail': 'Politica financeira invalida.'}, status=400)
        previous = {
            'checkin_minutes_before': arena.checkin_minutes_before,
            'checkin_minutes_after': arena.checkin_minutes_after,
            'delinquent_checkin_policy': arena.delinquent_checkin_policy,
        }
        arena.checkin_minutes_before = before
        arena.checkin_minutes_after = after
        arena.delinquent_checkin_policy = policy
        arena.save(update_fields=['checkin_minutes_before', 'checkin_minutes_after', 'delinquent_checkin_policy'])
        registrar_auditoria(request, arena, 'checkin.settings_updated', arena, anteriores=previous, novos={
            'checkin_minutes_before': before,
            'checkin_minutes_after': after,
            'delinquent_checkin_policy': policy,
        })
        return Response({
            'checkin_minutes_before': before,
            'checkin_minutes_after': after,
            'delinquent_checkin_policy': policy,
        })

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def confirm(self, request, pk=None):
        checkin = self._manageable()
        checkin = CheckIn.objects.select_for_update().get(pk=checkin.pk)
        if checkin.status != 'pending':
            return Response({'code': 'checkin_not_pending', 'detail': 'Este check-in nao esta pendente.'}, status=409)
        checkin.status = 'confirmed'
        checkin.presente = True
        checkin.validado_em = timezone.now()
        checkin.validado_por = request.user
        checkin.save(update_fields=['status', 'presente', 'validado_em', 'validado_por'])
        notify_checkin(checkin, 'Check-in confirmado', f'Sua presenca em {checkin.turma.nome} foi confirmada.')
        registrar_auditoria(request, checkin.arena, 'checkin.confirmed', checkin, anteriores={'status': 'pending'}, novos={'status': 'confirmed'})
        return Response(CheckInSerializer(checkin, context={'request': request}).data)

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def reject(self, request, pk=None):
        checkin = self._manageable()
        reason = sanitize_audit_text(request.data.get('reason'), 300)
        if not reason:
            return Response({'reason': ['Informe o motivo da rejeicao.']}, status=400)
        checkin = CheckIn.objects.select_for_update().get(pk=checkin.pk)
        if checkin.status != 'pending':
            return Response({'code': 'checkin_not_pending', 'detail': 'Este check-in nao esta pendente.'}, status=409)
        checkin.status = 'rejected'
        checkin.presente = False
        checkin.motivo = reason
        checkin.validado_em = timezone.now()
        checkin.validado_por = request.user
        checkin.save(update_fields=['status', 'presente', 'motivo', 'validado_em', 'validado_por'])
        notify_checkin(checkin, 'Check-in rejeitado', f'Sua solicitacao para {checkin.turma.nome} foi rejeitada: {reason}')
        registrar_auditoria(request, checkin.arena, 'checkin.rejected', checkin, anteriores={'status': 'pending'}, novos={'status': 'rejected', 'motivo': reason})
        return Response(CheckInSerializer(checkin, context={'request': request}).data)

    @action(detail=False, methods=['post'], url_path='bulk-confirm')
    @transaction.atomic
    def bulk_confirm(self, request):
        ids = request.data.get('ids')
        if not isinstance(ids, list) or not ids or len(ids) > 200:
            return Response({'ids': ['Envie entre 1 e 200 check-ins.']}, status=400)
        allowed_ids = list(self.get_queryset().filter(pk__in=ids, status='pending').values_list('pk', flat=True))
        items = list(CheckIn.objects.select_for_update().filter(pk__in=allowed_ids).select_related('aluno', 'arena', 'turma'))
        now = timezone.now()
        for item in items:
            item.status = 'confirmed'
            item.presente = True
            item.validado_em = now
            item.validado_por = request.user
        CheckIn.objects.bulk_update(items, ['status', 'presente', 'validado_em', 'validado_por'])
        for item in items:
            notify_checkin(item, 'Check-in confirmado', f'Sua presenca em {item.turma.nome} foi confirmada.')
            registrar_auditoria(request, item.arena, 'checkin.confirmed', item, anteriores={'status': 'pending'}, novos={'status': 'confirmed', 'bulk': True})
        return Response({'confirmed': len(items), 'requested': len(ids)})

    @action(detail=False, methods=['post'])
    @transaction.atomic
    def manual(self, request):
        reason = sanitize_audit_text(request.data.get('reason'), 300)
        if not reason:
            return Response({'reason': ['Informe o motivo do check-in manual.']}, status=400)
        arena = get_user_arena(request.user)
        turma = Turma.objects.filter(pk=request.data.get('turma'), arena=arena, ativa=True).select_related('professor').first()
        student = Usuario.objects.filter(pk=request.data.get('aluno'), arena=arena, tipo='aluno', is_active=True).first()
        if not turma or not student:
            return Response({'detail': 'Aluno ou turma invalido.'}, status=400)
        provisional = CheckIn(turma=turma)
        if not _operator_can_manage(request.user, provisional):
            raise PermissionDenied('Voce nao pode validar esta turma.')
        today = timezone.localdate()
        if not turma.alunos.filter(pk=student.pk).exists() or not active_enrollment_exists(student, arena, today):
            return Response({'detail': 'Aluno sem matricula ativa nesta turma.'}, status=403)
        try:
            occurrence = ensure_occurrence(turma, today)
        except CheckInDomainError as exc:
            return Response(exc.payload(), status=exc.http_status)
        checkin, created = CheckIn.objects.select_for_update().get_or_create(
            arena=arena, aluno=student, turma=turma, data=today,
            defaults={
                'ocorrencia': occurrence, 'horario': timezone.localtime().time().replace(tzinfo=None),
                'presente': True, 'status': 'confirmed', 'origem': 'manual', 'motivo': reason,
                'validado_em': timezone.now(), 'validado_por': request.user,
            },
        )
        if not created:
            return Response({'code': 'checkin_already_requested', 'detail': 'Ja existe um check-in para esta aula.', 'checkin_id': checkin.id}, status=409)
        notify_checkin(checkin, 'Presenca registrada', f'Sua presenca em {turma.nome} foi registrada pela arena.')
        registrar_auditoria(request, arena, 'checkin.manual', checkin, novos={'status': 'confirmed', 'motivo': reason})
        return Response(CheckInSerializer(checkin, context={'request': request}).data, status=201)

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def correct(self, request, pk=None):
        checkin = self._manageable()
        reason = sanitize_audit_text(request.data.get('reason'), 300)
        target_status = request.data.get('status')
        if not reason or target_status not in {'confirmed', 'absent'}:
            return Response({'detail': 'Informe motivo e status confirmed ou absent.'}, status=400)
        if checkin.data != timezone.localdate() and not _is_admin_role(request.user):
            raise PermissionDenied('Apos o mesmo dia, somente administradores podem corrigir.')
        previous = checkin.status
        checkin.status = target_status
        checkin.presente = target_status == 'confirmed'
        checkin.motivo = reason
        checkin.validado_em = timezone.now()
        checkin.validado_por = request.user
        checkin.save(update_fields=['status', 'presente', 'motivo', 'validado_em', 'validado_por'])
        registrar_auditoria(request, checkin.arena, 'checkin.corrected', checkin, anteriores={'status': previous}, novos={'status': target_status, 'motivo': reason})
        return Response(CheckInSerializer(checkin, context={'request': request}).data)


class MobileHomeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        arena = get_user_arena(request.user)
        if request.user.papel_efetivo != 'aluno':
            return Response({'detail': 'Area disponivel somente para alunos.'}, status=403)
        expire_pending_checkins()
        now = timezone.localtime()
        operational = arena.get_operational_settings()
        turmas = request.user.turmas.filter(arena=arena, ativa=True).select_related('professor', 'quadra') if operational.classes_enabled else []
        candidates = []
        for offset in range(8):
            target_date = now.date() + timezone.timedelta(days=offset)
            for turma in turmas:
                if turma_occurs_on(turma, target_date):
                    occurrence, _ = AulaOcorrencia.objects.get_or_create(
                        turma=turma, data=target_date,
                        defaults={'arena': arena, 'horario_previsto': turma.horario},
                    )
                    starts = timezone.make_aware(datetime.combine(target_date, occurrence.horario_previsto), timezone.get_current_timezone())
                    if starts >= now - timezone.timedelta(minutes=arena.checkin_minutes_after):
                        candidates.append((starts, turma, occurrence))
        candidates.sort(key=lambda item: item[0])
        next_class = None
        if candidates:
            starts, turma, occurrence = candidates[0]
            next_class = {
                'occurrence': AulaOcorrenciaSerializer(occurrence).data,
                'turma': TurmaSerializer(turma, context={'request': request}).data,
                'starts_at': starts.isoformat(),
                'checkin': checkin_state_for(turma, request.user),
            }
        recent = CheckIn.objects.filter(arena=arena, aluno=request.user).select_related('turma', 'turma__professor', 'ocorrencia')[:10]
        open_access = access_state(request.user, arena)
        access_visit = open_access.pop('visit', None)
        return Response({
            'arena': {
                'id': arena.id, 'nome': arena.nome, 'tipo_negocio': arena.tipo_negocio,
                'terminologia': arena.terminologia,
            },
            'features': {
                'classes': operational.classes_enabled,
                'open_access': operational.open_access_enabled,
                'reservations': operational.reservations_enabled,
                'store': operational.store_enabled,
            },
            'access': {
                **open_access,
                'enabled': operational.open_access_enabled,
                'validation': operational.open_access_validation,
                'visit': AccessVisitSerializer(access_visit, context={'request': request}).data if access_visit else None,
            },
            'next_class': next_class,
            'recent_checkins': CheckInSerializer(recent, many=True, context={'request': request}).data,
        })


class AdminTurmaViewSet(FeatureEnabledMixin, viewsets.ModelViewSet):
    feature_key = 'classes'
    serializer_class = TurmaSerializer
    permission_classes = [require_permission('turmas.manage')]

    def get_queryset(self):
        return Turma.objects.filter(arena=get_user_arena(self.request.user)).select_related('professor', 'quadra').prefetch_related('alunos').order_by('nome')

    def perform_create(self, serializer):
        arena = get_user_arena(self.request.user)
        professor = serializer.validated_data['professor']
        quadra = serializer.validated_data['quadra']
        if professor.arena_id != arena.id or quadra.arena_id != arena.id:
            raise serializers.ValidationError({'detail': 'Professor ou quadra nao pertence a arena atual.'})
        serializer.save(arena=arena)


# ══════════════════════════════════════════════
# SOLICITAÇÕES — VISÃO DO ALUNO
# ══════════════════════════════════════════════

class MinhasSolicitacoesViewSet(FeatureEnabledMixin, viewsets.ModelViewSet):
    feature_key = 'classes'
    """
    Aluno vê e cancela as próprias solicitações.
    GET    /api/minhas-solicitacoes/
    DELETE /api/minhas-solicitacoes/{id}/
    """
    serializer_class = SolicitacaoMatriculaSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'delete', 'head', 'options']

    def get_queryset(self):
        return SolicitacaoMatricula.objects.filter(
            arena=get_user_arena(self.request.user),
            aluno=self.request.user
        ).select_related('turma', 'respondido_por')

    def destroy(self, request, *args, **kwargs):
        solicitacao = self.get_object()
        if solicitacao.status != 'pendente':
            return Response(
                {'detail': 'Só é possível cancelar solicitações pendentes.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        solicitacao.status = 'cancelada'
        solicitacao.save()
        return Response(
            {'detail': 'Solicitação cancelada.'},
            status=status.HTTP_200_OK
        )


# ══════════════════════════════════════════════
# SOLICITAÇÕES — VISÃO DO ADMIN
# ══════════════════════════════════════════════

class AdminSolicitacoesViewSet(FeatureEnabledMixin, viewsets.ReadOnlyModelViewSet):
    feature_key = 'classes'
    """
    Admin vê todas as solicitações e aprova/recusa.
    GET  /api/admin/solicitacoes/?status=pendente
    POST /api/admin/solicitacoes/{id}/aprovar/
    POST /api/admin/solicitacoes/{id}/recusar/
    """
    serializer_class = SolicitacaoMatriculaSerializer
    permission_classes = [require_permission('alunos.manage')]

    def get_queryset(self):
        qs = SolicitacaoMatricula.objects.filter(arena=get_user_arena(self.request.user)).select_related(
            'aluno', 'turma', 'respondido_por'
        )
        # Filtros via query params
        status_filtro = self.request.query_params.get('status')
        tipo_filtro = self.request.query_params.get('tipo')
        if status_filtro:
            qs = qs.filter(status=status_filtro)
        if tipo_filtro:
            qs = qs.filter(tipo=tipo_filtro)
        return qs

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def aprovar(self, request, pk=None):
        solicitacao = self.get_object()

        if solicitacao.status != 'pendente':
            return Response(
                {'detail': 'Esta solicitação já foi processada.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        turma = solicitacao.turma
        aluno = solicitacao.aluno

        if solicitacao.tipo == 'matricula':
    # TEMPORÁRIO: log para debug
            try:
                vagas_disp = turma.vagas_disponiveis
                print(f"🔍 DEBUG: Turma {turma.id} | Vagas: {turma.vagas} | Alunos: {turma.alunos.count()} | Disponíveis: {vagas_disp} (tipo: {type(vagas_disp).__name__})")
            except Exception as e:
                print(f"🔍 DEBUG: Erro ao acessar vagas_disponiveis: {e}")
                vagas_disp = 0
            
            # Verifica vagas
            if vagas_disp <= 0:
                return Response(
                    {'detail': f'Turma sem vagas. Vagas={turma.vagas}, Alunos={turma.alunos.count()}, Disp={vagas_disp}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            turma.alunos.add(aluno)

        elif solicitacao.tipo == 'cancelamento':
            turma.alunos.remove(aluno)
            registrar_auditoria(request, get_user_arena(request.user), 'matricula.cancelada_admin', solicitacao, anteriores={'aluno': aluno.id, 'turma': turma.id})
            # Se houver fila, dispara notificação (signal cuida disso)

        solicitacao.status = 'aprovada'
        solicitacao.data_resposta = timezone.now()
        solicitacao.respondido_por = request.user
        solicitacao.save()

        return Response({
            'detail': '✓ Solicitação aprovada com sucesso!',
            'solicitacao': SolicitacaoMatriculaSerializer(solicitacao).data,
        })

    @action(detail=True, methods=['post'])
    def recusar(self, request, pk=None):
        solicitacao = self.get_object()

        if solicitacao.status != 'pendente':
            return Response(
                {'detail': 'Esta solicitação já foi processada.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        motivo = request.data.get('motivo', '')

        solicitacao.status = 'recusada'
        solicitacao.data_resposta = timezone.now()
        solicitacao.respondido_por = request.user
        solicitacao.motivo_recusa = motivo
        solicitacao.save()

        return Response({
            'detail': 'Solicitação recusada.',
            'solicitacao': SolicitacaoMatriculaSerializer(solicitacao).data,
        })


# ══════════════════════════════════════════════
# FILA DE ESPERA — ADMIN
# ══════════════════════════════════════════════

class AdminFilaEsperaViewSet(FeatureEnabledMixin, viewsets.ReadOnlyModelViewSet):
    feature_key = 'classes'
    """
    Admin gerencia fila de espera.
    GET  /api/admin/fila-espera/?turma=ID
    POST /api/admin/fila-espera/{id}/chamar/
    POST /api/admin/fila-espera/{id}/remover/
    """
    serializer_class = FilaEsperaSerializer
    permission_classes = [require_permission('alunos.manage')]

    def get_queryset(self):
        qs = FilaEspera.objects.filter(arena=get_user_arena(self.request.user)).select_related('aluno', 'turma')
        turma_id = self.request.query_params.get('turma')
        status_filtro = self.request.query_params.get('status', 'aguardando')
        if turma_id:
            qs = qs.filter(turma_id=turma_id)
        if status_filtro:
            qs = qs.filter(status=status_filtro)
        return qs.order_by('turma', 'posicao')

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def chamar(self, request, pk=None):
        """Chama o aluno da fila — cria solicitação automática."""
        item = self.get_object()

        if item.status != 'aguardando':
            return Response(
                {'detail': 'Este aluno já foi chamado ou saiu da fila.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Marca como chamado
            item.status = 'chamado'
            item.data_chamada = timezone.now()
            item.chamado_por = request.user
            item.save()

            # Verifica se já existe solicitação pendente desse aluno pra essa turma
            ja_pendente = SolicitacaoMatricula.objects.filter(
                aluno=item.aluno,
                turma=item.turma,
                tipo='matricula',
                status='pendente'
            ).exists()

            if not ja_pendente:
                SolicitacaoMatricula.objects.create(
                    arena=get_user_arena(request.user),
                    aluno=item.aluno,
                    turma=item.turma,
                    tipo='matricula',
                    observacao_aluno='[Chamado da fila de espera]',
                )

            # Reordena posições restantes
            restantes = FilaEspera.objects.filter(
                turma=item.turma, status='aguardando'
            ).order_by('posicao')
            for i, r in enumerate(restantes, start=1):
                if r.posicao != i:
                    r.posicao = i
                    r.save()

            return Response({
                'detail': f'✓ {item.aluno.username} foi chamado da fila!',
            })
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(
                {'detail': f'Erro: {type(e).__name__}: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def remover(self, request, pk=None):
        """Remove um aluno da fila."""
        item = self.get_object()

        try:
            item.status = 'desistiu'
            item.save()

            # Reordena posições restantes
            restantes = FilaEspera.objects.filter(
                turma=item.turma, status='aguardando'
            ).order_by('posicao')
            for i, r in enumerate(restantes, start=1):
                if r.posicao != i:
                    r.posicao = i
                    r.save()

            return Response({'detail': 'Aluno removido da fila.'})
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(
                {'detail': f'Erro: {type(e).__name__}: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

