import io
import json
import zipfile
from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, Q, Sum
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response

from arena.models import Arena
from arena.tenant import get_user_arena
from gestao.audit import client_ip, registrar_auditoria, sanitize_audit_text
from saas_billing.models import SaasInvoice, SaasMetricSnapshot, SaasSubscription, SaasWebhookEvent
from usuarios.permissions import IsSaasSuperAdmin, papel_usuario

from .models import DataSubjectRequest, FeatureBlock, LegalConsent, LegalDocumentVersion, OperationalTask, SupportMessage, SupportTicket
from .serializers import (
    DataSubjectRequestSerializer, FeatureBlockSerializer, LegalConsentSerializer,
    LegalDocumentSerializer, OperationalTaskSerializer, SupportTicketSerializer,
)
from .services import account_health
from .tasks import prepare_data_export


class SupportTicketViewSet(viewsets.ModelViewSet):
    serializer_class = SupportTicketSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = SupportTicket.objects.select_related('arena', 'created_by', 'assigned_to').prefetch_related('messages__author')
        if papel_usuario(self.request.user) == 'superadmin_saas':
            arena_id = self.request.headers.get('X-Arena-ID')
            return queryset.filter(arena_id=arena_id) if arena_id else queryset
        return queryset.filter(arena=get_user_arena(self.request.user))

    def perform_create(self, serializer):
        arena = get_user_arena(self.request.user)
        hours = {'low': 72, 'normal': 48, 'high': 24, 'urgent': 4}[serializer.validated_data.get('priority', 'normal')]
        ticket = serializer.save(arena=arena, created_by=self.request.user, sla_due_at=timezone.now() + timedelta(hours=hours))
        registrar_auditoria(self.request, arena, 'support.ticket_created', ticket, novos={'subject': ticket.subject, 'priority': ticket.priority})

    def partial_update(self, request, *args, **kwargs):
        ticket = self.get_object()
        if papel_usuario(request.user) != 'superadmin_saas' and set(request.data).difference({'status'}):
            return Response({'detail': 'Somente o suporte SaaS pode alterar estes campos.'}, status=status.HTTP_403_FORBIDDEN)
        response = super().partial_update(request, *args, **kwargs)
        if response.data.get('status') in {'resolved', 'closed'} and not ticket.resolved_at:
            ticket.refresh_from_db()
            ticket.resolved_at = timezone.now()
            ticket.save(update_fields=['resolved_at'])
        registrar_auditoria(request, ticket.arena, 'support.ticket_updated', ticket, novos=request.data)
        return response

    @action(detail=True, methods=['post'])
    def messages(self, request, pk=None):
        ticket = self.get_object()
        body = sanitize_audit_text(request.data.get('body'), 5000)
        internal = bool(request.data.get('internal', False))
        if not body:
            return Response({'detail': 'Escreva uma mensagem.'}, status=status.HTTP_400_BAD_REQUEST)
        if internal and papel_usuario(request.user) != 'superadmin_saas':
            return Response({'detail': 'Notas internas sao exclusivas do suporte SaaS.'}, status=status.HTTP_403_FORBIDDEN)
        SupportMessage.objects.create(ticket=ticket, author=request.user, body=body, internal=internal)
        return Response(SupportTicketSerializer(ticket, context={'request': request}).data, status=status.HTTP_201_CREATED)


class FeatureBlockViewSet(viewsets.ModelViewSet):
    serializer_class = FeatureBlockSerializer
    permission_classes = [IsSaasSuperAdmin]
    queryset = FeatureBlock.objects.select_related('arena').all()

    def perform_create(self, serializer):
        block = serializer.save(created_by=self.request.user)
        registrar_auditoria(self.request, block.arena, 'saas.feature_blocked', block, novos={'feature': block.feature, 'reason': block.reason})


class LegalDocumentViewSet(viewsets.ModelViewSet):
    serializer_class = LegalDocumentSerializer
    queryset = LegalDocumentVersion.objects.all()

    def get_permissions(self):
        if self.action in {'list', 'retrieve'}:
            return [permissions.AllowAny()]
        return [IsSaasSuperAdmin()]

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_authenticated or papel_usuario(self.request.user) != 'superadmin_saas':
            queryset = queryset.filter(status='published', effective_at__lte=timezone.now())
        document_type = self.request.query_params.get('type')
        return queryset.filter(document_type=document_type) if document_type else queryset


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def accept_legal_document(request):
    serializer = LegalConsentSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    document = serializer.validated_data['document']
    if document.status != 'published' or document.effective_at and document.effective_at > timezone.now():
        return Response({'detail': 'Documento nao esta vigente.'}, status=status.HTTP_409_CONFLICT)
    arena = get_user_arena(request.user)
    consent, created = LegalConsent.objects.get_or_create(
        arena=arena, user=request.user, document=document,
        purpose=serializer.validated_data['purpose'],
        defaults={'ip_address': client_ip(request), 'user_agent': sanitize_audit_text(request.headers.get('User-Agent'), 500)},
    )
    return Response(LegalConsentSerializer(consent).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class DataSubjectRequestViewSet(viewsets.ModelViewSet):
    serializer_class = DataSubjectRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'patch', 'head', 'options']

    def get_queryset(self):
        queryset = DataSubjectRequest.objects.select_related('arena', 'requested_by')
        if papel_usuario(self.request.user) == 'superadmin_saas':
            return queryset
        return queryset.filter(arena=get_user_arena(self.request.user), requested_by=self.request.user)

    def perform_create(self, serializer):
        arena = get_user_arena(self.request.user)
        data_request = serializer.save(arena=arena, requested_by=self.request.user, status='pending', resolution='', completed_at=None)
        registrar_auditoria(self.request, arena, 'privacy.request_created', data_request, novos={'kind': data_request.kind})
        if data_request.kind == 'export':
            prepare_data_export.delay(data_request.id)

    def partial_update(self, request, *args, **kwargs):
        if papel_usuario(request.user) != 'superadmin_saas':
            return Response({'detail': 'Somente o time SaaS pode revisar solicitacoes.'}, status=status.HTTP_403_FORBIDDEN)
        return super().partial_update(request, *args, **kwargs)

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        data_request = self.get_object()
        if data_request.kind != 'export' or not data_request.export_ready:
            return Response({'detail': 'Exportacao ainda nao esta pronta.'}, status=status.HTTP_409_CONFLICT)
        arena = data_request.arena
        payloads = {
            'arena.json': {'id': arena.id, 'nome': arena.nome, 'slug': arena.slug, 'email_contato': arena.email_contato},
            'usuarios.json': list(arena.usuarios.values('id', 'username', 'first_name', 'last_name', 'email', 'tipo', 'papel', 'is_active')),
            'assinatura.json': list(SaasSubscription.objects.filter(arena=arena).values('status', 'billing_cycle', 'created_at', 'updated_at')),
            'cobrancas.json': list(SaasInvoice.objects.filter(arena=arena).values('kind', 'status', 'amount', 'currency', 'paid_at', 'created_at')),
            'suporte.json': list(SupportTicket.objects.filter(arena=arena).values('id', 'subject', 'category', 'priority', 'status', 'created_at')),
        }
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
            for filename, content in payloads.items():
                archive.writestr(filename, json.dumps(content, default=str, ensure_ascii=False, indent=2))
        data_request.status = 'completed'
        data_request.completed_at = timezone.now()
        data_request.save(update_fields=['status', 'completed_at'])
        response = HttpResponse(buffer.getvalue(), content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="arenaflow-export-{arena.slug}.zip"'
        response['Cache-Control'] = 'no-store, private'
        return response


class OperationalTaskViewSet(viewsets.ModelViewSet):
    serializer_class = OperationalTaskSerializer
    permission_classes = [IsSaasSuperAdmin]
    queryset = OperationalTask.objects.select_related('arena', 'assigned_to').all()


@api_view(['GET'])
@permission_classes([IsSaasSuperAdmin])
def saas_operations_dashboard(request):
    now = timezone.now()
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    subscriptions = SaasSubscription.objects.select_related('plan', 'arena')
    mrr = Decimal('0')
    for subscription in subscriptions.filter(status__in=['active', 'cancel_at_period_end']):
        price = subscription.plan.price_for(subscription.billing_cycle) or Decimal('0')
        mrr += price / Decimal('12') if subscription.billing_cycle == 'annual' else price
    start_snapshot = SaasMetricSnapshot.objects.filter(date__lte=start.date()).order_by('-date').first()
    active_at_start = 0
    if start_snapshot:
        statuses = start_snapshot.metrics.get('statuses', {})
        active_at_start = statuses.get('active', 0) + statuses.get('cancel_at_period_end', 0)
    cancellations = subscriptions.filter(canceled_at__gte=start, canceled_at__lte=now).count()
    return Response({
        'period': {'start': start, 'end': now},
        'mrr': format(mrr.quantize(Decimal('0.01')), '.2f'),
        'revenue_received': format(SaasInvoice.objects.filter(status='paid', paid_at__gte=start).aggregate(total=Sum('amount'))['total'] or Decimal('0'), '.2f'),
        'revenue_overdue': format(SaasInvoice.objects.filter(status='failed').aggregate(total=Sum('amount'))['total'] or Decimal('0'), '.2f'),
        'statuses': {value: subscriptions.filter(status=value).count() for value, _ in SaasSubscription.STATUSES},
        'new_arenas': Arena.objects.filter(criada_em__gte=start).count(),
        'churn_percent': format(Decimal(cancellations) / Decimal(active_at_start) * 100, '.2f') if active_at_start else None,
        'trials_ending_7d': subscriptions.filter(status='trialing', trial_ends_at__range=(now, now + timedelta(days=7))).count(),
        'payment_failures': SaasInvoice.objects.filter(status='failed', updated_at__gte=start).count(),
        'webhook_failures': SaasWebhookEvent.objects.filter(processed=False, received_at__gte=start).exclude(processing_error='').count(),
        'open_tickets': SupportTicket.objects.filter(status__in=['open', 'in_progress']).count(),
        'plan_distribution': list(subscriptions.values('plan__code', 'plan__name').annotate(total=Count('id')).order_by('plan__name')),
    })


@api_view(['GET'])
@permission_classes([IsSaasSuperAdmin])
def account_health_list(request):
    queryset = Arena.objects.all().order_by('nome')
    arena_id = request.query_params.get('arena_id')
    if arena_id:
        queryset = queryset.filter(id=arena_id)
    return Response([{'arena': {'id': arena.id, 'nome': arena.nome}, **account_health(arena)} for arena in queryset])
