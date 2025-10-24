from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import View, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import logout 
from django.db import models
from django.db.models import Avg, Count, Q, Subquery, OuterRef
from django.db.models.functions import Coalesce
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Case, When, IntegerField
from datetime import date

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json

from tarefas.models import Tarefa
from usuarios.models import CustomUser


def teste_visual(request):
    return render(request, 'teste_visual.html')


class DashboardView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        user = request.user

        # 1. DASHBOARD DO COORDENADOR
        if user.groups.filter(name='Coordenador').exists():
            return self.dashboard_coordenador(request)

        # 2. DASHBOARD DO SERVIDOR
        elif user.groups.filter(name='Servidor').exists():
            return self.dashboard_servidor(request, user)
        
        # 3. DASHBOARD ADMIN
        else:
            context = {
                'user': user,
                'total_usuarios': CustomUser.objects.count(),
                'total_tarefas': Tarefa.objects.count(),
            }
            return render(request, 'dashboards/dashboard_admin.html', context)

    def dashboard_coordenador(self, request):
        """Dashboard completo do Coordenador com KPIs, gráficos e tabelas"""
        
        # ========================================
        # FILTROS DA URL (INCLUINDO NOVOS FILTROS)
        # ========================================
        filtro_gex = request.GET.get('gex', '')
        filtro_siape = request.GET.get('siape', '')
        filtro_tipo_alerta = request.GET.get('tipo_alerta', '')
        filtro_status = request.GET.get('status', '')
        filtro_prazo_vencido = request.GET.get('prazo_vencido', '')  # ← NOVO FILTRO
        filtro_reaberta = request.GET.get('reaberta', '')  # ← NOVO FILTRO
        
        # ========================================
        # QUERYSET BASE DE TAREFAS
        # ========================================
        tarefas_queryset = Tarefa.objects.select_related('siape_responsavel').all()
        
        # Aplica filtros
        if filtro_gex:
            tarefas_queryset = tarefas_queryset.filter(nome_gex_responsavel__icontains=filtro_gex)
        if filtro_siape:
            tarefas_queryset = tarefas_queryset.filter(siape_responsavel__siape=filtro_siape)
        if filtro_status:
            tarefas_queryset = tarefas_queryset.filter(status_tarefa=filtro_status)
        
        # ← NOVO: Filtro por prazo vencido
        if filtro_prazo_vencido == '1':
            tarefas_queryset = tarefas_queryset.filter(
                data_prazo__isnull=False,
                data_prazo__lt=date.today()
            )
        
        # ← NOVO: Filtro por tarefas reabertas
        if filtro_reaberta == '1':
            tarefas_queryset = tarefas_queryset.filter(indicador_tarefa_reaberta=1)
        
        # ========================================
        # KPIs PRINCIPAIS (INCLUINDO NOVOS KPIs)
        # ========================================
        total_tarefas = tarefas_queryset.count()
        
        # Calcula tarefas com alerta usando as properties do modelo
        tarefas_com_alerta = [t for t in tarefas_queryset if t.tem_alerta]
        total_com_alertas = len(tarefas_com_alerta)
        
        # Conta por tipo de alerta
        alertas_tipo_1 = sum(1 for t in tarefas_com_alerta if t.tipo_alerta == 'PENDENTE_SEM_MOVIMENTACAO')
        alertas_tipo_2 = sum(1 for t in tarefas_com_alerta if t.tipo_alerta == 'EXIGENCIA_VENCIDA')
        alertas_tipo_3 = sum(1 for t in tarefas_com_alerta if t.tipo_alerta == 'EXIGENCIA_CUMPRIDA_PENDENTE')
        
        # ← NOVO: KPIs de prazos
        tarefas_com_prazo = tarefas_queryset.filter(data_prazo__isnull=False)
        total_com_prazo = tarefas_com_prazo.count()
        tarefas_prazo_vencido = [t for t in tarefas_com_prazo if t.prazo_vencido]
        total_prazo_vencido = len(tarefas_prazo_vencido)
        
        # ← NOVO: KPI de tarefas reabertas
        total_reabertas = tarefas_queryset.filter(indicador_tarefa_reaberta=1).count()
        
        # Conta servidores únicos
        total_servidores = CustomUser.objects.filter(
            groups__name='Servidor',
            is_active=True
        ).count()
        
        # Tarefas por status
        tarefas_pendentes = tarefas_queryset.filter(status_tarefa='Pendente').count()
        tarefas_cumprimento = tarefas_queryset.filter(status_tarefa='Cumprimento de exigência').count()
        
        kpis = {
            'total_tarefas': total_tarefas,
            'total_com_alertas': total_com_alertas,
            'total_servidores': total_servidores,
            'alertas_tipo_1': alertas_tipo_1,
            'alertas_tipo_2': alertas_tipo_2,
            'alertas_tipo_3': alertas_tipo_3,
            'tarefas_pendentes': tarefas_pendentes,
            'tarefas_cumprimento': tarefas_cumprimento,
            'percentual_alertas': round((total_com_alertas / total_tarefas * 100) if total_tarefas > 0 else 0, 1),
            # ← NOVOS KPIs
            'total_com_prazo': total_com_prazo,
            'total_prazo_vencido': total_prazo_vencido,
            'total_reabertas': total_reabertas,
            'percentual_prazo_vencido': round((total_prazo_vencido / total_com_prazo * 100) if total_com_prazo > 0 else 0, 1),
            'percentual_reabertas': round((total_reabertas / total_tarefas * 100) if total_tarefas > 0 else 0, 1),
        }
        
        # ========================================
        # GRÁFICO 1: TAREFAS POR STATUS (PIZZA)
        # ========================================
        status_counts = tarefas_queryset.values('status_tarefa').annotate(
            total=Count('numero_protocolo_tarefa')
        ).order_by('-total')
        
        grafico_status = go.Figure(data=[go.Pie(
            labels=[item['status_tarefa'] for item in status_counts],
            values=[item['total'] for item in status_counts],
            hole=0.4,
            marker=dict(
                colors=['#0e2238', '#3b7ddd', '#28a745', '#ffc107', '#dc3545'],
                line=dict(color='white', width=2)
            ),
            textinfo='label+percent',
            textposition='outside',
            hovertemplate='<b>%{label}</b><br>Tarefas: %{value}<br>Percentual: %{percent}<extra></extra>'
        )])
        
        grafico_status.update_layout(
            title=dict(
                text='Distribuição de Tarefas por Status',
                font=dict(size=16, family='Poppins'),
                x=0.5,
                xanchor='center'
            ),
            showlegend=True,
            height=350,
            margin=dict(l=20, r=20, t=50, b=20),
            paper_bgcolor='white',
            plot_bgcolor='white',
            font=dict(size=12, family='Poppins')
        )
        
        grafico_status_json = grafico_status.to_json()
        
        # ========================================
        # GRÁFICO 2: TIPOS DE ALERTAS (BARRAS)
        # ========================================
        grafico_alertas = go.Figure(data=[
            go.Bar(
                x=['Sem Movimentação', 'Exigência Vencida', 'Exigência Cumprida'],
                y=[alertas_tipo_1, alertas_tipo_2, alertas_tipo_3],
                marker=dict(
                    color=['#ffc107', '#dc3545', '#3b7ddd'],
                    line=dict(color='white', width=1)
                ),
                text=[alertas_tipo_1, alertas_tipo_2, alertas_tipo_3],
                textposition='outside',
                hovertemplate='<b>%{x}</b><br>Tarefas: %{y}<extra></extra>'
            )
        ])
        
        grafico_alertas.update_layout(
            title=dict(
                text='Tarefas com Alerta por Tipo',
                font=dict(size=16, family='Poppins'),
                x=0.5,
                xanchor='center'
            ),
            xaxis=dict(title='Tipo de Alerta', tickangle=-15),
            yaxis=dict(title='Quantidade de Tarefas'),
            height=350,
            margin=dict(l=50, r=20, t=50, b=80),
            paper_bgcolor='white',
            plot_bgcolor='white',
            font=dict(size=12, family='Poppins'),
            showlegend=False
        )
        
        grafico_alertas_json = grafico_alertas.to_json()
        
        # ========================================
        # ← NOVO: GRÁFICO 3: SITUAÇÃO DOS PRAZOS (PIZZA)
        # ========================================
        if total_com_prazo > 0:
            prazos_ok = total_com_prazo - total_prazo_vencido
            
            grafico_prazos = go.Figure(data=[go.Pie(
                labels=['Prazos OK', 'Prazos Vencidos'],
                values=[prazos_ok, total_prazo_vencido],
                hole=0.4,
                marker=dict(
                    colors=['#28a745', '#dc3545'],
                    line=dict(color='white', width=2)
                ),
                textinfo='label+value+percent',
                textposition='outside',
                hovertemplate='<b>%{label}</b><br>Tarefas: %{value}<br>Percentual: %{percent}<extra></extra>'
            )])
            
            grafico_prazos.update_layout(
                title=dict(
                    text='Situação dos Prazos',
                    font=dict(size=16, family='Poppins'),
                    x=0.5,
                    xanchor='center'
                ),
                showlegend=True,
                height=350,
                margin=dict(l=20, r=20, t=50, b=20),
                paper_bgcolor='white',
                plot_bgcolor='white',
                font=dict(size=12, family='Poppins')
            )
            
            grafico_prazos_json = grafico_prazos.to_json()
        else:
            grafico_prazos_json = None
        
        # ========================================
        # GRÁFICO 4: TOP 10 SERVIDORES COM MAIS ALERTAS
        # ========================================
        # Agrupa tarefas por servidor e conta alertas
        servidores_com_tarefas = {}
        for tarefa in tarefas_queryset:
            if tarefa.tem_alerta and tarefa.nome_profissional_responsavel:
                nome = tarefa.nome_profissional_responsavel
                if nome not in servidores_com_tarefas:
                    servidores_com_tarefas[nome] = 0
                servidores_com_tarefas[nome] += 1
        
        # Ordena e pega top 10
        top_servidores = sorted(
            servidores_com_tarefas.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        if top_servidores:
            nomes_servidores = [item[0] for item in top_servidores]
            valores_servidores = [item[1] for item in top_servidores]
            
            grafico_top_servidores = go.Figure(data=[
                go.Bar(
                    y=nomes_servidores,
                    x=valores_servidores,
                    orientation='h',
                    marker=dict(
                        color=valores_servidores,
                        colorscale='Reds',
                        line=dict(color='white', width=1)
                    ),
                    text=valores_servidores,
                    textposition='outside',
                    hovertemplate='<b>%{y}</b><br>Tarefas com alerta: %{x}<extra></extra>'
                )
            ])
            
            grafico_top_servidores.update_layout(
                title=dict(
                    text='Top 10 Servidores com Mais Alertas',
                    font=dict(size=16, family='Poppins'),
                    x=0.5,
                    xanchor='center'
                ),
                xaxis=dict(title='Quantidade de Tarefas com Alerta'),
                yaxis=dict(title=''),
                height=450,
                margin=dict(l=200, r=50, t=50, b=50),
                paper_bgcolor='white',
                plot_bgcolor='white',
                font=dict(size=11, family='Poppins'),
                showlegend=False
            )
        else:
            grafico_top_servidores = go.Figure()
            grafico_top_servidores.update_layout(
                title='Top 10 Servidores com Mais Alertas',
                annotations=[dict(
                    text="Nenhum servidor com alertas",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=14)
                )],
                height=400
            )
        
        grafico_top_servidores_json = grafico_top_servidores.to_json()
        
        # ========================================
        # GRÁFICO 5: TOP 10 GEX POR QUANTIDADE DE TAREFAS
        # ========================================
        gex_counts = tarefas_queryset.values('nome_gex_responsavel').annotate(
            total=Count('numero_protocolo_tarefa')
        ).order_by('-total')[:10]
        
        if gex_counts:
            nomes_gex = [item['nome_gex_responsavel'] or 'Sem GEX' for item in gex_counts]
            valores_gex = [item['total'] for item in gex_counts]
            
            grafico_gex = go.Figure(data=[
                go.Bar(
                    y=nomes_gex,
                    x=valores_gex,
                    orientation='h',
                    marker=dict(
                        color=valores_gex,
                        colorscale='Blues',
                        line=dict(color='white', width=1)
                    ),
                    text=valores_gex,
                    textposition='outside',
                    hovertemplate='<b>%{y}</b><br>Tarefas: %{x}<extra></extra>'
                )
            ])
            
            grafico_gex.update_layout(
                title=dict(
                    text='Top 10 GEX por Quantidade de Tarefas',
                    font=dict(size=16, family='Poppins'),
                    x=0.5,
                    xanchor='center'
                ),
                xaxis=dict(title='Quantidade de Tarefas'),
                yaxis=dict(title=''),
                height=450,
                margin=dict(l=250, r=50, t=50, b=50),
                paper_bgcolor='white',
                plot_bgcolor='white',
                font=dict(size=11, family='Poppins'),
                showlegend=False
            )
        else:
            grafico_gex = go.Figure()
            grafico_gex.update_layout(
                title='Top 10 GEX por Quantidade de Tarefas',
                annotations=[dict(
                    text="Nenhuma tarefa encontrada",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=14)
                )],
                height=400
            )
        
        grafico_gex_json = grafico_gex.to_json()
        
        # ========================================
        # TABELA DE TAREFAS COM ALERTAS (Paginada)
        # ========================================
        if filtro_tipo_alerta:
            tarefas_alerta_list = [
                t for t in tarefas_queryset 
                if t.tipo_alerta == filtro_tipo_alerta
            ]
        else:
            tarefas_alerta_list = tarefas_com_alerta
        
        # Ordena por dias com servidor (decrescente)
        tarefas_alerta_list.sort(key=lambda x: x.dias_com_servidor, reverse=True)
        
        # Paginação das tarefas com alerta
        paginator_alertas = Paginator(tarefas_alerta_list, 20)
        page_alertas = request.GET.get('page_alertas', 1)
        
        try:
            tarefas_alertas_paginadas = paginator_alertas.page(page_alertas)
        except PageNotAnInteger:
            tarefas_alertas_paginadas = paginator_alertas.page(1)
        except EmptyPage:
            tarefas_alertas_paginadas = paginator_alertas.page(paginator_alertas.num_pages)
        
        # ========================================
        # LISTA DE GEX E STATUS PARA FILTROS
        # ========================================
        lista_gex = Tarefa.objects.values_list(
            'nome_gex_responsavel', flat=True
        ).distinct().order_by('nome_gex_responsavel')
        
        lista_status = Tarefa.objects.values_list(
            'status_tarefa', flat=True
        ).distinct().order_by('status_tarefa')
        
        # ========================================
        # LISTA DE SERVIDORES (Paginada)
        # ========================================
        total_tarefas_subquery = Subquery(
            Tarefa.objects.filter(siape_responsavel=OuterRef('siape'))
            .values('siape_responsavel')
            .annotate(count=Count('numero_protocolo_tarefa'))
            .values('count'),
            output_field=models.IntegerField()
        )

        tarefas_pendentes_subquery = Subquery(
            Tarefa.objects.filter(
                siape_responsavel=OuterRef('siape'),
                status_tarefa='Pendente'
            )
            .values('siape_responsavel')
            .annotate(count=Count('numero_protocolo_tarefa'))
            .values('count'),
            output_field=models.IntegerField()
        )

        tarefas_cumprimento_subquery = Subquery(
            Tarefa.objects.filter(
                siape_responsavel=OuterRef('siape'),
                status_tarefa='Cumprimento de exigência'
            )
            .values('siape_responsavel')
            .annotate(count=Count('numero_protocolo_tarefa'))
            .values('count'),
            output_field=models.IntegerField()
        )

        servidores_list = CustomUser.objects.filter(
            groups__name='Servidor',
            is_active=True
        ).annotate(
            total_tarefas=Coalesce(total_tarefas_subquery, 0),
            tarefas_pendentes=Coalesce(tarefas_pendentes_subquery, 0),
            tarefas_cumprimento=Coalesce(tarefas_cumprimento_subquery, 0),
        ).order_by('nome_completo')

        # Paginação dos servidores
        paginator_servidores = Paginator(servidores_list, 50)
        page_servidores = request.GET.get('page_servidores', 1)

        try:
            servidores_paginados = paginator_servidores.page(page_servidores)
        except PageNotAnInteger:
            servidores_paginados = paginator_servidores.page(1)
        except EmptyPage:
            servidores_paginados = paginator_servidores.page(paginator_servidores.num_pages)

        # ========================================
        # CONTEXT FINAL (COM NOVOS DADOS)
        # ========================================
        context = {
            'kpis': kpis,
            'grafico_status': grafico_status_json,
            'grafico_alertas': grafico_alertas_json,
            'grafico_prazos': grafico_prazos_json,  # ← NOVO GRÁFICO
            'grafico_top_servidores': grafico_top_servidores_json,
            'grafico_gex': grafico_gex_json,
            'tarefas_alertas': tarefas_alertas_paginadas,
            'servidores': servidores_paginados,
            'lista_gex': lista_gex,
            'lista_status': lista_status,
            'filtro_gex': filtro_gex,
            'filtro_siape': filtro_siape,
            'filtro_tipo_alerta': filtro_tipo_alerta,
            'filtro_status': filtro_status,
            'filtro_prazo_vencido': filtro_prazo_vencido,  # ← NOVO FILTRO
            'filtro_reaberta': filtro_reaberta,  # ← NOVO FILTRO
        }
        
        return render(request, 'dashboards/dashboard_coordenador.html', context)

    def dashboard_servidor(self, request, user):
        """Dashboard do Servidor individual"""
        tarefas = Tarefa.objects.filter(siape_responsavel=user.siape)
        tarefas_pendentes = tarefas.filter(status_tarefa='Pendente')
        tarefas_cumprimento = tarefas.filter(status_tarefa='Cumprimento de exigência')
        
        # ← NOVOS: Contadores de prazos e reabertas
        tarefas_com_prazo = tarefas.filter(data_prazo__isnull=False)
        tarefas_prazo_vencido = tarefas_com_prazo.filter(data_prazo__lt=date.today())
        tarefas_reabertas = tarefas.filter(indicador_tarefa_reaberta=1)

        kpis = {
            'total': tarefas.count(),
            'pendentes': tarefas_pendentes.count(),
            'cumprimento': tarefas_cumprimento.count(),
            'media_pendencia': tarefas_pendentes.aggregate(
                media=Avg('tempo_em_pendencia_em_dias')
            )['media'] or 0,
            'mais_antiga': tarefas_pendentes.order_by('data_distribuicao_tarefa').first(),
            # ← NOVOS KPIs
            'total_prazo_vencido': tarefas_prazo_vencido.count(),
            'total_reabertas': tarefas_reabertas.count(),
        }
        
        context = {
            'tarefas': tarefas, 
            'kpis': kpis,
            'ultima_carga': Tarefa.objects.order_by('-data_processamento_tarefa').first().data_processamento_tarefa if Tarefa.objects.exists() else None,
        }
        return render(request, 'dashboards/dashboard_servidor.html', context)


class ServidorDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboards/dashboard_servidor.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not self.request.user.groups.filter(name='Coordenador').exists():
            return context
        
        servidor_siape = self.kwargs.get('siape')
        servidor = get_object_or_404(CustomUser, siape=servidor_siape)
        
        tarefas = Tarefa.objects.filter(siape_responsavel=servidor.siape)
        tarefas_pendentes = tarefas.filter(status_tarefa='Pendente')
        tarefas_cumprimento = tarefas.filter(status_tarefa='Cumprimento de exigência')
        
        # ← NOVOS: Contadores de prazos e reabertas
        tarefas_com_prazo = tarefas.filter(data_prazo__isnull=False)
        tarefas_prazo_vencido = tarefas_com_prazo.filter(data_prazo__lt=date.today())
        tarefas_reabertas = tarefas.filter(indicador_tarefa_reaberta=1)

        kpis = {
            'total': tarefas.count(),
            'pendentes': tarefas_pendentes.count(),
            'cumprimento': tarefas_cumprimento.count(),
            'media_pendencia': tarefas_pendentes.aggregate(
                media=Avg('tempo_em_pendencia_em_dias')
            )['media'] or 0,
            'mais_antiga': tarefas_pendentes.order_by('data_distribuicao_tarefa').first(),
            # ← NOVOS KPIs
            'total_prazo_vencido': tarefas_prazo_vencido.count(),
            'total_reabertas': tarefas_reabertas.count(),
        }
        
        context['tarefas'] = tarefas
        context['kpis'] = kpis
        context['servidor_selecionado'] = servidor
        context['ultima_carga'] = Tarefa.objects.order_by('-data_processamento_tarefa').first().data_processamento_tarefa if Tarefa.objects.exists() else None
        return context


def logout_view(request):
    """Desloga o usuário e o redireciona para a página de login"""
    logout(request)
    return redirect('login')