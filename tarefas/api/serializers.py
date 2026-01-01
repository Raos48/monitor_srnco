"""
Serializers para a API REST.

Converte os modelos Django em JSON para comunicação com o robô externo.
"""
from rest_framework import serializers
from tarefas.models import BloqueioServidor, SolicitacaoNotificacao


class BloqueioServidorSerializer(serializers.ModelSerializer):
    """
    Serializer para solicitações de bloqueio/desbloqueio.
    """
    siape_servidor = serializers.CharField(source='servidor.siape', read_only=True)
    nome_servidor = serializers.SerializerMethodField()
    tipo_acao_display = serializers.CharField(source='get_tipo_acao_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = BloqueioServidor
        fields = [
            'id',
            'siape_servidor',
            'nome_servidor',
            'codigo_fila',
            'tipo_acao',
            'tipo_acao_display',
            'status',
            'status_display',
            'data_solicitacao',
            'data_processamento',
            'data_conclusao',
            'observacoes',
        ]
        read_only_fields = ['id', 'data_solicitacao']

    def get_nome_servidor(self, obj):
        """Retorna o nome completo do servidor."""
        return obj.servidor.get_full_name() or obj.servidor.username


class BloqueioRespostaSerializer(serializers.Serializer):
    """
    Serializer para receber resposta do robô sobre bloqueios.
    """
    bloqueio_id = serializers.IntegerField()
    sucesso = serializers.BooleanField()
    resposta_robo = serializers.CharField(required=False, allow_blank=True)
    mensagem_erro = serializers.CharField(required=False, allow_blank=True)


class SolicitacaoNotificacaoSerializer(serializers.ModelSerializer):
    """
    Serializer para solicitações de notificação PGB.
    """
    siape_servidor = serializers.CharField(source='servidor.siape', read_only=True)
    nome_servidor = serializers.SerializerMethodField()
    email_servidor = serializers.CharField(source='servidor.email', read_only=True)
    tipo_notificacao_display = serializers.CharField(source='get_tipo_notificacao_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = SolicitacaoNotificacao
        fields = [
            'id',
            'siape_servidor',
            'nome_servidor',
            'email_servidor',
            'tipo_notificacao',
            'tipo_notificacao_display',
            'status',
            'status_display',
            'data_solicitacao',
            'data_processamento',
            'data_conclusao',
            'numero_protocolo_criado',
            'observacoes',
        ]
        read_only_fields = ['id', 'data_solicitacao']

    def get_nome_servidor(self, obj):
        """Retorna o nome completo do servidor."""
        return obj.servidor.get_full_name() or obj.servidor.username


class NotificacaoRespostaSerializer(serializers.Serializer):
    """
    Serializer para receber resposta do robô sobre notificações.
    """
    notificacao_id = serializers.IntegerField()
    sucesso = serializers.BooleanField()
    numero_protocolo = serializers.CharField(required=False, allow_blank=True)
    resposta_robo = serializers.CharField(required=False, allow_blank=True)
    mensagem_erro = serializers.CharField(required=False, allow_blank=True)
