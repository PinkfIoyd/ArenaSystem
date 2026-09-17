from rest_framework import serializers
from .models import Notificacao, NotificacaoAdmin


class NotificacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notificacao
        fields = ['id', 'tipo', 'titulo', 'mensagem', 'lida', 'criada_em']
        read_only_fields = fields


class NotificacaoAdminSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)

    class Meta:
        model = NotificacaoAdmin
        fields = [
            'id', 'tipo', 'tipo_display',
            'titulo', 'mensagem', 'url',
            'lida', 'criada_em', 'lida_em',
        ]
        read_only_fields = fields  # admin não edita nada manualmente
