"""
Views da API REST para integração com robô externo.

Endpoints para o robô consultar solicitações pendentes e enviar respostas.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from tarefas.models import BloqueioServidor, SolicitacaoNotificacao
from tarefas.services.acoes_service import AcoesService
from .serializers import (
    BloqueioServidorSerializer,
    BloqueioRespostaSerializer,
    SolicitacaoNotificacaoSerializer,
    NotificacaoRespostaSerializer
)


# Hash de autenticação simples (será substituído por token futuramente)
API_SECRET_HASH = getattr(settings, 'API_ROBO_SECRET_HASH', 'hash_secreto_padrao_trocar_em_producao')


def validar_autenticacao(request):
    """
    Valida o hash de autenticação do robô.

    Args:
        request: Request object

    Returns:
        bool: True se autenticado, False caso contrário
    """
    hash_fornecido = request.headers.get('X-API-Secret-Hash', '')
    return hash_fornecido == API_SECRET_HASH


@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])
def listar_bloqueios_pendentes(request):
    """
    GET /api/solicitacoes/bloqueios/pendentes/

    Retorna todas as solicitações de bloqueio/desbloqueio pendentes.
    """
    # Validar autenticação
    if not validar_autenticacao(request):
        return Response(
            {'erro': 'Autenticação inválida'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    # Buscar solicitações pendentes
    solicitacoes = AcoesService.obter_solicitacoes_bloqueio_pendentes()

    # Serializar
    serializer = BloqueioServidorSerializer(solicitacoes, many=True)

    return Response({
        'total': solicitacoes.count(),
        'solicitacoes': serializer.data
    })


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def processar_resposta_bloqueio(request):
    """
    POST /api/solicitacoes/bloqueios/resposta/

    Recebe a resposta do robô sobre uma solicitação de bloqueio.

    Body JSON:
    {
        "bloqueio_id": 1,
        "sucesso": true,
        "resposta_robo": "Bloqueio realizado com sucesso",
        "mensagem_erro": ""
    }
    """
    # Validar autenticação
    if not validar_autenticacao(request):
        return Response(
            {'erro': 'Autenticação inválida'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    # Validar dados
    serializer = BloqueioRespostaSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {'erro': 'Dados inválidos', 'detalhes': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Processar resposta
    try:
        bloqueio = AcoesService.processar_resposta_bloqueio(
            bloqueio_id=serializer.validated_data['bloqueio_id'],
            sucesso=serializer.validated_data['sucesso'],
            resposta_robo=serializer.validated_data.get('resposta_robo', ''),
            mensagem_erro=serializer.validated_data.get('mensagem_erro', '')
        )

        return Response({
            'mensagem': 'Resposta processada com sucesso',
            'bloqueio_id': bloqueio.id,
            'status': bloqueio.status
        })

    except BloqueioServidor.DoesNotExist:
        return Response(
            {'erro': 'Bloqueio não encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'erro': f'Erro ao processar resposta: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])
def listar_notificacoes_pendentes(request):
    """
    GET /api/solicitacoes/notificacoes/pendentes/

    Retorna todas as solicitações de notificação PGB pendentes.
    """
    # Validar autenticação
    if not validar_autenticacao(request):
        return Response(
            {'erro': 'Autenticação inválida'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    # Buscar solicitações pendentes
    solicitacoes = AcoesService.obter_solicitacoes_notificacao_pendentes()

    # Serializar
    serializer = SolicitacaoNotificacaoSerializer(solicitacoes, many=True)

    return Response({
        'total': solicitacoes.count(),
        'solicitacoes': serializer.data
    })


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def processar_resposta_notificacao(request):
    """
    POST /api/solicitacoes/notificacoes/resposta/

    Recebe a resposta do robô sobre uma solicitação de notificação.

    Body JSON:
    {
        "notificacao_id": 1,
        "sucesso": true,
        "numero_protocolo": "12345678901234567890",
        "resposta_robo": "Tarefa criada com sucesso",
        "mensagem_erro": ""
    }
    """
    # Validar autenticação
    if not validar_autenticacao(request):
        return Response(
            {'erro': 'Autenticação inválida'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    # Validar dados
    serializer = NotificacaoRespostaSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {'erro': 'Dados inválidos', 'detalhes': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Processar resposta
    try:
        notificacao = AcoesService.processar_resposta_notificacao(
            notificacao_id=serializer.validated_data['notificacao_id'],
            sucesso=serializer.validated_data['sucesso'],
            numero_protocolo=serializer.validated_data.get('numero_protocolo', ''),
            resposta_robo=serializer.validated_data.get('resposta_robo', ''),
            mensagem_erro=serializer.validated_data.get('mensagem_erro', '')
        )

        return Response({
            'mensagem': 'Resposta processada com sucesso',
            'notificacao_id': notificacao.id,
            'status': notificacao.status,
            'numero_protocolo': notificacao.numero_protocolo_criado
        })

    except SolicitacaoNotificacao.DoesNotExist:
        return Response(
            {'erro': 'Notificação não encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'erro': f'Erro ao processar resposta: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    GET /api/health/

    Endpoint para verificar se a API está funcionando.
    """
    return Response({
        'status': 'ok',
        'mensagem': 'API do Sistema SIGA está funcionando'
    })
