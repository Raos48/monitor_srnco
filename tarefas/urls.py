"""
URLs ATUALIZADAS - ARQUITETURA LIMPA
Sistema de 5 Níveis de Criticidade

Arquivo: tarefas/urls.py
"""

from django.urls import path
from . import views
from . import views, views_justificativas

app_name = 'tarefas'

urlpatterns = [
    # ============================================
    # REDIRECIONAMENTO PÓS-LOGIN
    # ============================================
    path('', views.redirect_after_login, name='redirect_after_login'),
   
    
    # ============================================
    # DASHBOARDS
    # ============================================
    # Dashboard do coordenador (LIMPO - só KPIs + Gráficos)
    path('dashboard/coordenador/', views.dashboard_coordenador, name='dashboard_coordenador'),
    
    # Dashboard do servidor (redireciona para detalhes)
    path('dashboard/servidor/', views.dashboard_servidor, name='dashboard_servidor'),
    
    # ============================================
    # FILAS DE TRABALHO (NOVO)
    # ============================================
    # Detalhamento de uma fila específica
    path('fila/<str:codigo_fila>/', views.detalhe_fila, name='detalhe_fila'),

    # Exportação de relatório Excel de tarefas por fila/servidor
    path('fila/<str:codigo_fila>/exportar-excel/', views.exportar_tarefas_fila_servidor_excel, name='exportar_tarefas_fila_servidor_excel'),

    # ============================================
    # LISTAGENS (PÁGINAS SEPARADAS)
    # ============================================
    # Lista completa de tarefas (com filtros)
    path('lista/', views.lista_tarefas, name='lista_tarefas'),

    # Lista de servidores (com filtros)
    path('servidores/lista/', views.lista_servidores, name='lista_servidores'),

    # Detalhes de um servidor específico
    path('servidores/<str:siape>/', views.detalhe_servidor, name='detalhe_servidor'),
    
    # ============================================
    # API JSON (OPCIONAL)
    # ============================================
    path('api/estatisticas/', views.api_estatisticas_json, name='api_estatisticas'),
    
    # ============================================
    # ADICIONE A URL EM tarefas/urls.py
    # ============================================
    path('tarefa/<str:protocolo>/', views.detalhe_tarefa, name='detalhe_tarefa'),    
    
    # ============================================
    # SERVIDOR - JUSTIFICATIVAS
    # ============================================
    path(
        'tarefa/<str:protocolo>/justificar/',
        views_justificativas.submeter_justificativa,
        name='submeter_justificativa'
    ),
    path(
        'minhas-justificativas/',
        views_justificativas.minhas_justificativas,
        name='minhas_justificativas'
    ),
    
    # ============================================
    # SERVIDOR - SOLICITAÇÕES DE AJUDA
    # ============================================
    path(
        'tarefa/<str:protocolo>/solicitar-ajuda/',
        views_justificativas.solicitar_ajuda,
        name='solicitar_ajuda'
    ),
    path(
        'minhas-solicitacoes/',
        views_justificativas.minhas_solicitacoes,
        name='minhas_solicitacoes'
    ),
    
    # ============================================
    # EQUIPE VOLANTE - DASHBOARD
    # ============================================
    path(
        'equipe-volante/painel/',
        views_justificativas.painel_equipe_volante,
        name='painel_equipe_volante'
    ),
    
    # ============================================
    # EQUIPE VOLANTE - JUSTIFICATIVAS
    # ============================================
    path(
        'equipe-volante/justificativas/',
        views_justificativas.lista_justificativas_analise,
        name='lista_justificativas_analise'
    ),
    path(
        'equipe-volante/justificativa/<int:justificativa_id>/',
        views_justificativas.detalhe_justificativa,
        name='detalhe_justificativa'
    ),
    path(
        'equipe-volante/justificativa/<int:justificativa_id>/avaliar/',
        views_justificativas.avaliar_justificativa,
        name='avaliar_justificativa'
    ),
    
    # ============================================
    # EQUIPE VOLANTE - SOLICITAÇÕES
    # ============================================
    path(
        'equipe-volante/solicitacoes/',
        views_justificativas.lista_solicitacoes_ajuda,
        name='lista_solicitacoes_ajuda'
    ),
    path(
        'equipe-volante/solicitacao/<int:solicitacao_id>/',
        views_justificativas.detalhe_solicitacao,
        name='detalhe_solicitacao'
    ),
    path(
        'equipe-volante/solicitacao/<int:solicitacao_id>/atender/',
        views_justificativas.atender_solicitacao,
        name='atender_solicitacao'
    ),
    
    # ============================================
    # COORDENADOR - RELATÓRIOS
    # ============================================
    path(
        'coordenador/relatorio-justificativas/',
        views_justificativas.relatorio_justificativas_coordenador,
        name='relatorio_justificativas_coordenador'
    ),
    path(
        'coordenador/relatorio-solicitacoes/',
        views_justificativas.relatorio_solicitacoes_coordenador,
        name='relatorio_solicitacoes_coordenador'
    ),

    # ============================================
    # CONFIGURAÇÕES DO SISTEMA
    # ============================================
    path(
        'configuracoes/',
        views.configuracoes,
        name='configuracoes'
    ),
    path(
        'configuracoes/recalcular-criticidades/',
        views.recalcular_criticidades,
        name='recalcular_criticidades'
    ),

    # ============================================
    # AÇÕES AUTOMATIZADAS
    # ============================================
    path(
        'servidor/<str:siape>/bloqueio/solicitar/',
        views.solicitar_bloqueio_servidor,
        name='solicitar_bloqueio_servidor'
    ),
    path(
        'servidor/<str:siape>/desbloqueio/solicitar/',
        views.solicitar_desbloqueio_servidor,
        name='solicitar_desbloqueio_servidor'
    ),
    path(
        'servidor/<str:siape>/notificacao/solicitar/',
        views.solicitar_notificacao_pgb,
        name='solicitar_notificacao_pgb'
    ),
    path(
        'servidor/<str:siape>/email/enviar/',
        views.enviar_email_servidor,
        name='enviar_email_servidor'
    ),
    path(
        'servidor/<str:siape>/status/',
        views.verificar_status_servidor,
        name='verificar_status_servidor'
    ),

    # ============================================
    # AÇÕES EM LOTE - GERAÇÃO DE ARQUIVO CSV
    # ============================================
    path(
        'servidor/<str:siape>/fila/<str:codigo_fila>/servicos/',
        views.obter_servicos_servidor_fila,
        name='obter_servicos_servidor_fila'
    ),
    path(
        'servidor/<str:siape>/fila/<str:codigo_fila>/gerar-arquivo-lote/',
        views.gerar_arquivo_acao_lote,
        name='gerar_arquivo_acao_lote'
    ),
]