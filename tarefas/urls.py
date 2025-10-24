"""
URLs ATUALIZADAS - ARQUITETURA LIMPA
Sistema de 5 Níveis de Criticidade

Arquivo: tarefas/urls.py
"""

from django.urls import path
from . import views

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
    
    
]