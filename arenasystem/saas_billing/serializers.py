from rest_framework import serializers

from .models import SaasInvoice, SaasPlan, SaasSubscription
from .services import effective_limits, subscription_usage


class SaasPlanSerializer(serializers.ModelSerializer):
    monthly_price = serializers.DecimalField(max_digits=10, decimal_places=2, coerce_to_string=True, allow_null=True)
    annual_price = serializers.DecimalField(max_digits=10, decimal_places=2, coerce_to_string=True, allow_null=True)

    class Meta:
        model = SaasPlan
        fields = [
            'id', 'code', 'name', 'description', 'published', 'currency',
            'monthly_price', 'annual_price', 'trial_days', 'grace_days',
            'max_admins', 'max_professors', 'max_students', 'max_courts',
            'storage_mb', 'features',
        ]
        read_only_fields = ['id']

    def validate(self, attrs):
        published = attrs.get('published', getattr(self.instance, 'published', False))
        monthly = attrs.get('monthly_price', getattr(self.instance, 'monthly_price', None))
        annual = attrs.get('annual_price', getattr(self.instance, 'annual_price', None))
        if published and (not monthly or monthly <= 0 or not annual or annual <= 0):
            raise serializers.ValidationError({'published': 'Informe precos mensal e anual positivos antes de publicar.'})
        for field in ('max_admins', 'max_professors', 'max_students', 'max_courts', 'storage_mb'):
            value = attrs.get(field, getattr(self.instance, field, None))
            if value is not None and value < 1:
                raise serializers.ValidationError({field: 'O limite deve ser maior que zero.'})
        return attrs


class SaasInvoiceSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, coerce_to_string=True)

    class Meta:
        model = SaasInvoice
        fields = [
            'id', 'kind', 'status', 'amount', 'currency', 'period_start', 'period_end',
            'due_at', 'paid_at', 'receipt_url', 'plan_snapshot', 'created_at',
        ]


class SaasSubscriptionSerializer(serializers.ModelSerializer):
    plan = SaasPlanSerializer(read_only=True)
    pending_plan = SaasPlanSerializer(read_only=True)
    usage = serializers.SerializerMethodField()
    limits = serializers.SerializerMethodField()

    class Meta:
        model = SaasSubscription
        fields = [
            'id', 'status', 'billing_cycle', 'plan', 'pending_plan', 'pending_billing_cycle',
            'trial_started_at', 'trial_ends_at', 'current_period_start', 'current_period_end',
            'grace_ends_at', 'canceled_at', 'usage', 'limits', 'updated_at',
        ]

    def get_usage(self, obj):
        return subscription_usage(obj.arena)

    def get_limits(self, obj):
        return effective_limits(obj)


class CheckoutSerializer(serializers.Serializer):
    plan_id = serializers.IntegerField(required=False)
    billing_cycle = serializers.ChoiceField(choices=SaasSubscription.BILLING_CYCLES, default='monthly')


class ChangePlanSerializer(serializers.Serializer):
    plan_id = serializers.IntegerField()
    billing_cycle = serializers.ChoiceField(choices=SaasSubscription.BILLING_CYCLES, required=False)

