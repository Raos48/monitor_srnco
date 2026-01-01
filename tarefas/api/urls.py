"""
URLs da API REST para integração com robô externo.
"""
from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    # Health check
    path('health/', views.health_check, name='health_check'),

    # Bloqueios
    path(
        'solicitacoes/bloqueios/pendentes/',
        views.listar_bloqueios_pendentes,
        name='bloqueios_pendentes'
    ),
    path(
        'solicitacoes/bloqueios/resposta/',
        views.processar_resposta_bloqueio,
        name='bloqueios_resposta'
    ),

    # Notificações
    path(
        'solicitacoes/notificacoes/pendentes/',
        views.listar_notificacoes_pendentes,
        name='notificacoes_pendentes'
    ),
    path(
        'solicitacoes/notificacoes/resposta/',
        views.processar_resposta_notificacao,
        name='notificacoes_resposta'
    ),
]
