from django.contrib import admin

from .models import SaasInvoice, SaasMetricSnapshot, SaasPlan, SaasSubscription, SaasWebhookEvent


@admin.register(SaasPlan)
class SaasPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'published', 'monthly_price', 'annual_price')
    list_filter = ('published',)
    search_fields = ('name', 'code')


@admin.register(SaasSubscription)
class SaasSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('arena', 'plan', 'billing_cycle', 'status', 'current_period_end')
    list_filter = ('status', 'billing_cycle', 'plan')
    search_fields = ('arena__nome', 'provider_preapproval_id')
    readonly_fields = ('provider_preapproval_id', 'created_at', 'updated_at')


@admin.register(SaasInvoice)
class SaasInvoiceAdmin(admin.ModelAdmin):
    list_display = ('arena', 'kind', 'status', 'amount', 'created_at')
    list_filter = ('kind', 'status')
    search_fields = ('arena__nome', 'external_reference', 'provider_payment_id')
    readonly_fields = ('external_reference', 'provider_payment_id', 'created_at', 'updated_at')


admin.site.register(SaasWebhookEvent)
admin.site.register(SaasMetricSnapshot)

