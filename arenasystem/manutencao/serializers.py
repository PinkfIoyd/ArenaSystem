from rest_framework import serializers

from .models import Manutencao


class ManutencaoSerializer(serializers.ModelSerializer):
    quadra_nome = serializers.CharField(source='quadra.nome', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Manutencao
        fields = [
            'id', 'quadra', 'quadra_nome', 'tipo', 'tipo_display',
            'descricao', 'data_agendada', 'data_conclusao',
            'custo', 'status', 'status_display', 'responsavel',
        ]
