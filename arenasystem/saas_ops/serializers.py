from rest_framework import serializers

from .models import (
    DataSubjectRequest, FeatureBlock, LegalConsent, LegalDocumentVersion,
    OperationalTask, SupportMessage, SupportTicket,
)


class SupportMessageSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = SupportMessage
        fields = ['id', 'author_name', 'body', 'internal', 'created_at']
        read_only_fields = ['id', 'author_name', 'created_at']

    def get_author_name(self, obj):
        return obj.author.get_full_name() or obj.author.username


class SupportTicketSerializer(serializers.ModelSerializer):
    arena_name = serializers.CharField(source='arena.nome', read_only=True)
    created_by_name = serializers.SerializerMethodField()
    messages = serializers.SerializerMethodField()

    class Meta:
        model = SupportTicket
        fields = [
            'id', 'arena_name', 'subject', 'category', 'priority', 'status',
            'created_by_name', 'assigned_to', 'sla_due_at', 'resolved_at',
            'created_at', 'updated_at', 'messages',
        ]
        read_only_fields = ['id', 'arena_name', 'created_by_name', 'sla_due_at', 'resolved_at', 'created_at', 'updated_at', 'messages']

    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name() or obj.created_by.username

    def get_messages(self, obj):
        request = self.context.get('request')
        queryset = obj.messages.select_related('author')
        if not request or getattr(request.user, 'papel_efetivo', None) != 'superadmin_saas':
            queryset = queryset.filter(internal=False)
        return SupportMessageSerializer(queryset, many=True).data


class FeatureBlockSerializer(serializers.ModelSerializer):
    arena_name = serializers.CharField(source='arena.nome', read_only=True)

    class Meta:
        model = FeatureBlock
        fields = ['id', 'arena', 'arena_name', 'feature', 'reason', 'active', 'expires_at', 'created_at']
        read_only_fields = ['id', 'arena_name', 'created_at']


class LegalDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = LegalDocumentVersion
        fields = ['id', 'document_type', 'version', 'title', 'content', 'status', 'effective_at', 'created_at']
        read_only_fields = ['id', 'created_at']


class LegalConsentSerializer(serializers.ModelSerializer):
    class Meta:
        model = LegalConsent
        fields = ['id', 'document', 'purpose', 'accepted_at']
        read_only_fields = ['id', 'accepted_at']


class DataSubjectRequestSerializer(serializers.ModelSerializer):
    requested_by_name = serializers.SerializerMethodField()

    class Meta:
        model = DataSubjectRequest
        fields = ['id', 'kind', 'status', 'description', 'resolution', 'export_ready', 'requested_by_name', 'created_at', 'completed_at']
        read_only_fields = ['id', 'export_ready', 'requested_by_name', 'created_at']

    def get_requested_by_name(self, obj):
        return obj.requested_by.get_full_name() or obj.requested_by.username


class OperationalTaskSerializer(serializers.ModelSerializer):
    arena_name = serializers.CharField(source='arena.nome', read_only=True)

    class Meta:
        model = OperationalTask
        fields = ['id', 'title', 'description', 'arena', 'arena_name', 'assigned_to', 'status', 'due_at', 'created_at', 'updated_at']
        read_only_fields = ['id', 'arena_name', 'created_at', 'updated_at']
