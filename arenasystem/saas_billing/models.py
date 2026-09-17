import secrets

from django.conf import settings
from django.db import models


class SaasPlan(models.Model):
    code = models.SlugField(max_length=40, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    published = models.BooleanField(default=False)
    currency = models.CharField(max_length=3, default='BRL')
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    annual_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    trial_days = models.PositiveSmallIntegerField(default=14)
    grace_days = models.PositiveSmallIntegerField(default=7)
    max_admins = models.PositiveIntegerField(default=3)
    max_professors = models.PositiveIntegerField(default=10)
    max_students = models.PositiveIntegerField(default=150)
    max_courts = models.PositiveIntegerField(default=4)
    storage_mb = models.PositiveIntegerField(default=512)
    features = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['monthly_price', 'name']

    def __str__(self):
        return self.name

    def price_for(self, billing_cycle):
        return self.annual_price if billing_cycle == 'annual' else self.monthly_price


class SaasSubscription(models.Model):
    BILLING_CYCLES = [('monthly', 'Mensal'), ('annual', 'Anual')]
    STATUSES = [
        ('trialing', 'Em teste'),
        ('active', 'Ativa'),
        ('past_due', 'Em atraso'),
        ('suspended', 'Suspensa'),
        ('cancel_at_period_end', 'Cancela ao fim do ciclo'),
        ('canceled', 'Cancelada'),
    ]

    arena = models.OneToOneField('arena.Arena', on_delete=models.CASCADE, related_name='saas_subscription')
    plan = models.ForeignKey(SaasPlan, on_delete=models.PROTECT, related_name='subscriptions')
    pending_plan = models.ForeignKey(
        SaasPlan, on_delete=models.PROTECT, related_name='pending_subscriptions', null=True, blank=True,
    )
    billing_cycle = models.CharField(max_length=10, choices=BILLING_CYCLES, default='monthly')
    pending_billing_cycle = models.CharField(max_length=10, choices=BILLING_CYCLES, blank=True)
    status = models.CharField(max_length=30, choices=STATUSES, default='trialing', db_index=True)
    trial_started_at = models.DateTimeField(null=True, blank=True)
    trial_ends_at = models.DateTimeField(null=True, blank=True)
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    grace_ends_at = models.DateTimeField(null=True, blank=True)
    canceled_at = models.DateTimeField(null=True, blank=True)
    provider = models.CharField(max_length=40, default='mercado_pago')
    provider_preapproval_id = models.CharField(max_length=160, blank=True, db_index=True)
    provider_payer_id = models.CharField(max_length=160, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.arena} - {self.plan}'


class SaasInvoice(models.Model):
    KINDS = [('subscription', 'Assinatura'), ('upgrade', 'Upgrade'), ('adjustment', 'Ajuste')]
    STATUSES = [
        ('pending', 'Pendente'), ('paid', 'Paga'), ('failed', 'Falhou'),
        ('canceled', 'Cancelada'), ('refunded', 'Estornada'),
    ]

    arena = models.ForeignKey('arena.Arena', on_delete=models.CASCADE, related_name='saas_invoices')
    subscription = models.ForeignKey(SaasSubscription, on_delete=models.CASCADE, related_name='invoices')
    kind = models.CharField(max_length=20, choices=KINDS, default='subscription')
    status = models.CharField(max_length=20, choices=STATUSES, default='pending', db_index=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='BRL')
    period_start = models.DateTimeField(null=True, blank=True)
    period_end = models.DateTimeField(null=True, blank=True)
    due_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    external_reference = models.CharField(max_length=160, unique=True, db_index=True)
    provider_payment_id = models.CharField(max_length=160, blank=True, db_index=True)
    provider_checkout_id = models.CharField(max_length=160, blank=True)
    checkout_url = models.URLField(blank=True)
    receipt_url = models.URLField(blank=True)
    plan_snapshot = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.external_reference:
            self.external_reference = f'saas:{self.arena_id}:{secrets.token_urlsafe(16)}'
        super().save(*args, **kwargs)


class SaasWebhookEvent(models.Model):
    provider = models.CharField(max_length=40, default='mercado_pago')
    event_id = models.CharField(max_length=180)
    event_type = models.CharField(max_length=80, blank=True)
    action = models.CharField(max_length=100, blank=True)
    arena = models.ForeignKey(
        'arena.Arena', on_delete=models.CASCADE, related_name='saas_webhook_events', null=True, blank=True,
    )
    signature_valid = models.BooleanField(default=False)
    payload = models.JSONField(default=dict, blank=True)
    processed = models.BooleanField(default=False)
    processing_error = models.CharField(max_length=500, blank=True)
    received_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['provider', 'event_id'], name='unique_saas_provider_event'),
        ]
        ordering = ['-received_at']


class SaasMetricSnapshot(models.Model):
    date = models.DateField(unique=True)
    metrics = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

