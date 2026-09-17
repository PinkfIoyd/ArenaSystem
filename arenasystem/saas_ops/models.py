from django.conf import settings
from django.db import models


class SupportTicket(models.Model):
    CATEGORIES = [('billing', 'Cobranca'), ('technical', 'Tecnico'), ('onboarding', 'Onboarding'), ('other', 'Outro')]
    PRIORITIES = [('low', 'Baixa'), ('normal', 'Normal'), ('high', 'Alta'), ('urgent', 'Urgente')]
    STATUSES = [('open', 'Aberto'), ('in_progress', 'Em andamento'), ('waiting_customer', 'Aguardando cliente'), ('resolved', 'Resolvido'), ('closed', 'Fechado')]
    arena = models.ForeignKey('arena.Arena', on_delete=models.CASCADE, related_name='support_tickets')
    subject = models.CharField(max_length=180)
    category = models.CharField(max_length=20, choices=CATEGORIES, default='other')
    priority = models.CharField(max_length=20, choices=PRIORITIES, default='normal')
    status = models.CharField(max_length=30, choices=STATUSES, default='open', db_index=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='created_support_tickets')
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_support_tickets',
    )
    sla_due_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']


class SupportMessage(models.Model):
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name='messages')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    body = models.TextField(max_length=5000)
    internal = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']


class SupportContact(models.Model):
    arena = models.ForeignKey('arena.Arena', on_delete=models.CASCADE, related_name='support_contacts')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    channel = models.CharField(max_length=30)
    summary = models.CharField(max_length=500)
    occurred_at = models.DateTimeField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='registered_support_contacts')
    created_at = models.DateTimeField(auto_now_add=True)


class FeatureBlock(models.Model):
    arena = models.ForeignKey('arena.Arena', on_delete=models.CASCADE, related_name='feature_blocks')
    feature = models.CharField(max_length=100)
    reason = models.CharField(max_length=500)
    active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['arena', 'feature'], condition=models.Q(active=True), name='unique_active_feature_block')]
        ordering = ['-created_at']


class LegalDocumentVersion(models.Model):
    TYPES = [('terms', 'Termos de uso'), ('privacy', 'Politica de privacidade'), ('dpa', 'Acordo de tratamento')]
    STATUSES = [('draft', 'Rascunho'), ('published', 'Publicado'), ('retired', 'Retirado')]
    document_type = models.CharField(max_length=20, choices=TYPES)
    version = models.CharField(max_length=30)
    title = models.CharField(max_length=180)
    content = models.TextField()
    status = models.CharField(max_length=20, choices=STATUSES, default='draft')
    effective_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['document_type', 'version'], name='unique_legal_document_version')]
        ordering = ['document_type', '-created_at']


class LegalConsent(models.Model):
    arena = models.ForeignKey('arena.Arena', on_delete=models.CASCADE, related_name='legal_consents')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='legal_consents')
    document = models.ForeignKey(LegalDocumentVersion, on_delete=models.PROTECT, related_name='consents')
    purpose = models.CharField(max_length=100)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    accepted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['user', 'document', 'purpose'], name='unique_legal_consent')]


class DataSubjectRequest(models.Model):
    KINDS = [('export', 'Exportacao'), ('correction', 'Correcao'), ('deletion', 'Exclusao'), ('anonymization', 'Anonimizacao')]
    STATUSES = [('pending', 'Pendente'), ('reviewing', 'Em analise'), ('approved', 'Aprovada'), ('rejected', 'Recusada'), ('completed', 'Concluida')]
    arena = models.ForeignKey('arena.Arena', on_delete=models.CASCADE, related_name='data_requests')
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='data_requests')
    kind = models.CharField(max_length=20, choices=KINDS)
    status = models.CharField(max_length=20, choices=STATUSES, default='pending', db_index=True)
    description = models.TextField(blank=True, max_length=2000)
    resolution = models.TextField(blank=True, max_length=4000)
    export_ready = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']


class OperationalTask(models.Model):
    STATUSES = [('open', 'Aberta'), ('in_progress', 'Em andamento'), ('blocked', 'Bloqueada'), ('done', 'Concluida')]
    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    arena = models.ForeignKey('arena.Arena', on_delete=models.CASCADE, null=True, blank=True, related_name='operational_tasks')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUSES, default='open')
    due_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['status', 'due_at', '-created_at']

