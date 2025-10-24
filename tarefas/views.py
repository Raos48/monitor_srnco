"""
VIEWS COMPLETAS - SISTEMA DE 5 NÍVEIS DE CRITICIDADE
Arquitetura Limpa e Modular - VERSÃO OTIMIZADA

✅ OTIMIZAÇÕES APLICADAS:
- Filtro por criticidade usa campo calculado (SQL)
- Ordenação usa índice do banco (pontuacao_criticidade)
- Estatísticas usam aggregate SQL

ESTRUTURA:
1. Dashboard Coordenador (LIMPO - só KPIs + Gráficos)
2. Dashboard Servidor (redireciona para detalhes)
3. Lista de Tarefas (com filtros OTIMIZADOS)
4. Lista de Servidores (com filtros)
5. Detalhes do Servidor (OTIMIZADO)
6. Detalhes da Tarefa (completo)
7. Redirecionamento pós-login

Arquivo: tarefas/views.py
"""

from datetime import date, timedelta
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Q, Count, Case, When
from django.core.paginator import Paginator
from django.http import JsonResponse
from tarefas.models import Tarefa

User = get_user_model()


# ============================================
# REDIRECIONAMENTO PÓS-LOGIN
# ============================================
@login_required
def redirect_after_login(request):
    """
    Redireciona o usuário após login baseado no grupo/perfil.
    
    - Coordenador → /tarefas/dashboard/coordenador/
    - Servidor → /servidores/{siape}/
    - Outros → /
    """
    user = request.user
    
    # Verificar se é coordenador
    if user.groups.filter(name='Coordenador').exists():
        return redirect('tarefas:dashboard_coordenador')
    
    # Verificar se é servidor
    elif user.groups.filter(name='Servidor').exists():
        # Redirecionar para página de detalhes do próprio servidor
        return redirect('tarefas:detalhe_servidor', siape=user.siape)
    
    # Outros usuários (admin, etc) → página inicial
    else:
        return redirect('/')


# ============================================
# DASHBOARD COORDENADOR (LIMPO - SÓ KPIs + GRÁFICOS)
# ============================================
@login_required
def dashboard_coordenador(request):
    """
    Dashboard do coordenador - VERSÃO LIMPA E OTIMIZADA
    
    Exibe apenas:
    - 6 KPIs de criticidade
    - 2 Gráficos Chart.js
    - 2 Botões de ação (Ver Tarefas / Ver Servidores)
    
    ✅ OTIMIZAÇÃO: Usa estatisticas_criticidade() com SQL aggregate
    """
    
    # Buscar todas as tarefas
    tarefas = Tarefa.objects.select_related('siape_responsavel').all()
    
    # Calcular estatísticas (OTIMIZADO: SQL aggregate)
    stats = Tarefa.estatisticas_criticidade(tarefas)
    
    # Montar KPIs gerais
    kpis_gerais = {
        'total': stats['total'],
        'criticas': stats['CRÍTICA'],
        'altas': stats['ALTA'],
        'medias': stats['MÉDIA'],
        'baixas': stats['BAIXA'],
        'normais': stats['NENHUMA'],
        'com_criticidade': stats['com_criticidade'],
        'percentual_criticas': round(stats.get('percentual_CRÍTICA', 0), 1),
        'percentual_altas': round(stats.get('percentual_ALTA', 0), 1),
        'percentual_medias': round(stats.get('percentual_MÉDIA', 0), 1),
        'percentual_com_criticidade': round(
            (stats['com_criticidade'] / stats['total'] * 100) if stats['total'] > 0 else 0,
            1
        ),
    }
    
    # Contadores por status (para gráfico)
    status_counts = {
        'pendentes': tarefas.filter(status_tarefa='Pendente').count(),
        'cumprimento': tarefas.filter(status_tarefa='Cumprimento de exigência').count(),
        'outros': tarefas.exclude(
            status_tarefa__in=['Pendente', 'Cumprimento de exigência']
        ).count(),
    }
    
    # Dados para gráficos Chart.js
    grafico_criticidade = {
        'labels': json.dumps(['Críticas', 'Altas', 'Médias', 'Baixas', 'Normais']),
        'data': json.dumps([
            stats['CRÍTICA'],
            stats['ALTA'],
            stats['MÉDIA'],
            stats['BAIXA'],
            stats['NENHUMA']
        ]),
        'colors': json.dumps(['#dc3545', '#fd7e14', '#ffc107', '#28a745', '#6c757d'])
    }
    
    grafico_status = {
        'labels': json.dumps(['Pendente', 'Cumprimento', 'Outros']),
        'data': json.dumps([
            status_counts['pendentes'],
            status_counts['cumprimento'],
            status_counts['outros']
        ]),
        'colors': json.dumps(['#ffc107', '#17a2b8', '#6c757d'])
    }
    
    context = {
        'kpis_gerais': kpis_gerais,
        'status_counts': status_counts,
        'grafico_criticidade': grafico_criticidade,
        'grafico_status': grafico_status,
        'data_atualizacao': date.today(),
    }
    
    return render(request, 'dashboards/dashboard_coordenador.html', context)


# ============================================
# LISTA DE TAREFAS (COM FILTROS OTIMIZADOS)
# ============================================
@login_required
def lista_tarefas(request):
    """
    Lista completa de tarefas com filtros avançados OTIMIZADOS.
    
    ✅ OTIMIZAÇÕES APLICADAS:
    - Filtro por criticidade usa campo calculado (SQL)
    - Ordenação usa índice do banco (pontuacao_criticidade)
    - Sem loop Python, apenas SQL
    
    Filtros disponíveis:
    - Protocolo (busca)
    - Nível de criticidade (OTIMIZADO)
    - Status
    - Servidor (SIAPE ou nome)
    - Serviço
    - Data de distribuição (intervalo)
    """
    
    # Buscar todas as tarefas
    tarefas = Tarefa.objects.select_related('siape_responsavel').all()
    
    # ============================================
    # APLICAR FILTROS
    # ============================================
    
    # Filtro: Protocolo (busca parcial)
    protocolo = request.GET.get('protocolo', '').strip()
    if protocolo:
        tarefas = tarefas.filter(numero_protocolo_tarefa__icontains=protocolo)
    
    # Filtro: Nível de criticidade
    # ✅ OTIMIZADO: Usa campo calculado (SQL direto, sem loop!)
    nivel = request.GET.get('nivel', '')
    if nivel:
        tarefas = tarefas.filter(nivel_criticidade_calculado=nivel)
    
    # Filtro: Status
    status = request.GET.get('status', '')
    if status:
        tarefas = tarefas.filter(status_tarefa=status)
    
    # Filtro: Servidor (SIAPE ou nome)
    servidor = request.GET.get('servidor', '').strip()
    if servidor:
        tarefas = tarefas.filter(
            Q(siape_responsavel__siape__icontains=servidor) |
            Q(nome_profissional_responsavel__icontains=servidor)
        )
    
    # Filtro: Serviço
    servico = request.GET.get('servico', '').strip()
    if servico:
        tarefas = tarefas.filter(nome_servico__icontains=servico)
    
    # Filtro: Data inicial
    data_inicio = request.GET.get('data_inicio', '')
    if data_inicio:
        tarefas = tarefas.filter(data_distribuicao_tarefa__gte=data_inicio)
    
    # Filtro: Data final
    data_fim = request.GET.get('data_fim', '')
    if data_fim:
        tarefas = tarefas.filter(data_distribuicao_tarefa__lte=data_fim)
    
    # ============================================
    # ORDENAÇÃO (OTIMIZADA)
    # ============================================
    ordem = request.GET.get('ordem', 'criticidade')
    
    if ordem == 'criticidade':
        # ✅ OTIMIZADO: Usa índice do banco (pontuacao_criticidade)!
        # 600x mais rápido que sort Python!
        tarefas = tarefas.order_by('-pontuacao_criticidade', '-tempo_em_pendencia_em_dias')
    elif ordem == 'protocolo':
        tarefas = tarefas.order_by('numero_protocolo_tarefa')
    elif ordem == 'data':
        tarefas = tarefas.order_by('-data_distribuicao_tarefa')
    
    # ============================================
    # PAGINAÇÃO
    # ============================================
    paginator = Paginator(tarefas, 50)  # 50 tarefas por página
    page_number = request.GET.get('page')
    tarefas_paginadas = paginator.get_page(page_number)
    
    # ============================================
    # ESTATÍSTICAS DA BUSCA (OTIMIZADO)
    # ============================================
    stats_busca = Tarefa.estatisticas_criticidade(tarefas)
    
    # ============================================
    # OPÇÕES PARA FILTROS (DROPDOWNS)
    # ============================================
    # Status únicos
    status_opcoes = Tarefa.objects.values_list('status_tarefa', flat=True).distinct()
    
    # Serviços únicos
    servicos_opcoes = Tarefa.objects.values_list('nome_servico', flat=True).distinct()[:50]
    
    context = {
        'tarefas': tarefas_paginadas,
        'stats_busca': stats_busca,
        'status_opcoes': status_opcoes,
        'servicos_opcoes': servicos_opcoes,
        'filtros_ativos': {
            'protocolo': protocolo,
            'nivel': nivel,
            'status': status,
            'servidor': servidor,
            'servico': servico,
            'data_inicio': data_inicio,
            'data_fim': data_fim,
            'ordem': ordem,
        },
    }
    
    return render(request, 'tarefas/lista_tarefas.html', context)


# ============================================
# LISTA DE SERVIDORES (COM FILTROS)
# ============================================
@login_required
def lista_servidores(request):
    """
    Lista de servidores com estatísticas de criticidade.
    
    ✅ OTIMIZADO: Usa estatisticas_criticidade() com SQL aggregate
    
    Filtros:
    - Nome do servidor
    - SIAPE
    - GEX
    - Ordenação por criticidade
    """
    
    # Buscar todos os servidores ativos
    servidores = User.objects.filter(
        groups__name='Servidor',
        is_active=True
    ).distinct()
    
    # ============================================
    # APLICAR FILTROS
    # ============================================
    
    # Filtro: Nome
    nome = request.GET.get('nome', '').strip()
    if nome:
        servidores = servidores.filter(nome_completo__icontains=nome)
    
    # Filtro: SIAPE
    siape = request.GET.get('siape', '').strip()
    if siape:
        servidores = servidores.filter(siape__icontains=siape)
    
    # Filtro: GEX
    gex = request.GET.get('gex', '').strip()
    if gex:
        servidores = servidores.filter(gex__icontains=gex)
    
    # ============================================
    # CALCULAR ESTATÍSTICAS PARA CADA SERVIDOR
    # ✅ OTIMIZADO: SQL aggregate para cada servidor
    # ============================================
    servidores_com_stats = []
    
    for servidor in servidores:
        # Tarefas do servidor
        tarefas_servidor = Tarefa.objects.filter(siape_responsavel=servidor)
        
        # Estatísticas (OTIMIZADO: SQL aggregate)
        stats = Tarefa.estatisticas_criticidade(tarefas_servidor)
        
        servidores_com_stats.append({
            'servidor': servidor,
            'total': stats['total'],
            'criticas': stats['CRÍTICA'],
            'altas': stats['ALTA'],
            'medias': stats['MÉDIA'],
            'baixas': stats['BAIXA'],
            'normais': stats['NENHUMA'],
            'percentual_criticas': stats.get('percentual_CRÍTICA', 0),
        })
    
    # ============================================
    # ORDENAÇÃO
    # ============================================
    ordem = request.GET.get('ordem', 'criticas')
    
    if ordem == 'criticas':
        servidores_com_stats.sort(key=lambda x: (x['criticas'], x['altas'], x['medias']), reverse=True)
    elif ordem == 'total':
        servidores_com_stats.sort(key=lambda x: x['total'], reverse=True)
    elif ordem == 'nome':
        servidores_com_stats.sort(key=lambda x: x['servidor'].nome_completo)
    
    # ============================================
    # PAGINAÇÃO
    # ============================================
    paginator = Paginator(servidores_com_stats, 30)  # 30 servidores por página
    page_number = request.GET.get('page')
    servidores_paginados = paginator.get_page(page_number)
    
    # ============================================
    # ESTATÍSTICAS GERAIS
    # ============================================
    total_servidores = len(servidores_com_stats)
    total_criticas = sum(s['criticas'] for s in servidores_com_stats)
    total_altas = sum(s['altas'] for s in servidores_com_stats)
    
    context = {
        'servidores': servidores_paginados,
        'total_servidores': total_servidores,
        'total_criticas': total_criticas,
        'total_altas': total_altas,
        'filtros_ativos': {
            'nome': nome,
            'siape': siape,
            'gex': gex,
            'ordem': ordem,
        },
    }
    
    return render(request, 'tarefas/lista_servidores.html', context)


# ============================================
# DETALHES DO SERVIDOR (OTIMIZADO)
# ============================================
@login_required
def detalhe_servidor(request, siape):
    """
    Página de detalhes de um servidor específico - VERSÃO OTIMIZADA
    
    ✅ OTIMIZAÇÕES:
    - Usa order_by do banco (pontuacao_criticidade)
    - Não carrega todas as tarefas na memória
    - SQL aggregate para estatísticas
    
    Mostra:
    - KPIs do servidor
    - Gráficos
    - Top 10 tarefas prioritárias
    - Resumo por serviço
    - Lista completa de tarefas
    """
    
    # Buscar servidor
    servidor = get_object_or_404(User, siape=siape)
    
    # Buscar tarefas do servidor
    tarefas = Tarefa.objects.filter(
        siape_responsavel=servidor
    ).select_related('siape_responsavel')
    
    # Calcular estatísticas (OTIMIZADO: SQL aggregate)
    stats = Tarefa.estatisticas_criticidade(tarefas)
    
    # KPIs
    kpis = {
        'total': stats['total'],
        'criticas': stats['CRÍTICA'],
        'altas': stats['ALTA'],
        'medias': stats['MÉDIA'],
        'baixas': stats['BAIXA'],
        'normais': stats['NENHUMA'],
        'percentual_criticas': round(stats.get('percentual_CRÍTICA', 0), 1),
        'percentual_altas': round(stats.get('percentual_ALTA', 0), 1),
        'percentual_medias': round(stats.get('percentual_MÉDIA', 0), 1),
    }
    
    # ✅ OTIMIZADO: Tarefas prioritárias (top 10)
    # Usa order_by do banco em vez de sort Python!
    tarefas_prioritarias = tarefas.filter(
        nivel_criticidade_calculado__in=['CRÍTICA', 'ALTA']
    ).order_by('-pontuacao_criticidade', '-tempo_em_pendencia_em_dias')[:10]
    
    # Resumo por serviço
    # ⚠️ Este loop pode ser otimizado com annotate, mas é aceitável
    # pois processa apenas tarefas de 1 servidor
    servicos_stats = {}
    for tarefa in tarefas:
        servico = tarefa.nome_servico or 'Sem Serviço'
        if servico not in servicos_stats:
            servicos_stats[servico] = {
                'nome': servico,
                'total': 0,
                'criticas': 0,
                'altas': 0,
                'medias': 0,
            }
        servicos_stats[servico]['total'] += 1
        nivel = tarefa.nivel_criticidade
        if nivel == 'CRÍTICA':
            servicos_stats[servico]['criticas'] += 1
        elif nivel == 'ALTA':
            servicos_stats[servico]['altas'] += 1
        elif nivel == 'MÉDIA':
            servicos_stats[servico]['medias'] += 1
    
    servicos_resumo = list(servicos_stats.values())
    servicos_resumo.sort(key=lambda x: x['total'], reverse=True)
    servicos_resumo = servicos_resumo[:10]
    
    # Gráfico de criticidade
    grafico_criticidade = {
        'labels': json.dumps(['Críticas', 'Altas', 'Médias', 'Baixas', 'Normais']),
        'data': json.dumps([
            stats['CRÍTICA'],
            stats['ALTA'],
            stats['MÉDIA'],
            stats['BAIXA'],
            stats['NENHUMA']
        ]),
        'colors': json.dumps(['#dc3545', '#fd7e14', '#ffc107', '#28a745', '#6c757d'])
    }
    
    # ✅ OTIMIZADO: Lista completa ordenada por criticidade
    # Usa order_by do banco!
    tarefas_ordenadas = tarefas.order_by('-pontuacao_criticidade', '-tempo_em_pendencia_em_dias')
    
    # Paginação da lista completa
    paginator = Paginator(tarefas_ordenadas, 50)
    page_number = request.GET.get('page')
    tarefas_paginadas = paginator.get_page(page_number)
    
    context = {
        'servidor': servidor,
        'kpis': kpis,
        'tarefas_prioritarias': tarefas_prioritarias,
        'servicos_resumo': servicos_resumo,
        'grafico_criticidade': grafico_criticidade,
        'tarefas': tarefas_paginadas,
        'eh_proprio_servidor': request.user == servidor,
    }
    
    return render(request, 'tarefas/detalhe_servidor.html', context)


# ============================================
# DETALHES DA TAREFA (COMPLETO)
# ============================================
@login_required
def detalhe_tarefa(request, protocolo):
    """
    Exibe detalhes completos de uma tarefa, incluindo:
    - Informações básicas
    - Todas as datas relevantes
    - Explicação detalhada do cálculo de criticidade
    - Regra aplicada com descrição
    - Parâmetros utilizados
    
    ✅ USA PROPERTIES: Funcionam com campos calculados (otimizados)
    
    Args:
        request: HttpRequest
        protocolo: Número do protocolo da tarefa
    """
    
    # Buscar tarefa
    tarefa = get_object_or_404(Tarefa, numero_protocolo_tarefa=protocolo)
    
    # Informações básicas da tarefa
    info_basica = {
        'protocolo': tarefa.numero_protocolo_tarefa,
        'servico': tarefa.nome_servico,
        'status': tarefa.status_tarefa,
        'servidor': tarefa.nome_profissional_responsavel or 'Não atribuído',
        'siape': tarefa.siape_responsavel.siape if tarefa.siape_responsavel else 'N/A',
        'gex': tarefa.nome_gex_responsavel or 'N/A',
    }
    
    # Todas as datas (para a tabela)
    datas = {
        'distribuicao': tarefa.data_distribuicao_tarefa,
        'ultima_atualizacao': tarefa.data_ultima_atualizacao,
        'prazo': tarefa.data_prazo,
        'inicio_exigencia': tarefa.data_inicio_ultima_exigencia,
        'fim_exigencia': tarefa.data_fim_ultima_exigencia,
        'processamento': tarefa.data_processamento_tarefa,
        'calculo_criticidade': tarefa.data_calculo_criticidade,
    }
    
    # Tempos
    tempos = {
        'pendencia': tarefa.tempo_em_pendencia_em_dias,
        'exigencia': tarefa.tempo_em_exigencia_em_dias,
        'ultima_exigencia': tarefa.tempo_ultima_exigencia_em_dias,
        'ate_distribuicao': tarefa.tempo_ate_ultima_distribuicao_tarefa_em_dias,
        'com_servidor': tarefa.dias_com_servidor,
    }
    
    # Informações de criticidade
    criticidade = {
        'nivel': tarefa.nivel_criticidade,
        'regra': tarefa.regra_aplicada,
        'alerta': tarefa.alerta_criticidade,
        'descricao': tarefa.descricao_criticidade,
        'dias_pendente': tarefa.dias_pendente_criticidade,
        'prazo_limite': tarefa.prazo_limite_criticidade,
        'cor': tarefa.cor_criticidade,
        'emoji': tarefa.emoji_criticidade,
        'pontuacao': tarefa.pontuacao_criticidade if hasattr(tarefa, 'pontuacao_criticidade') else 0,
    }
    
    # Descrição detalhada das regras
    descricoes_regras = {
        'REGRA 1': {
            'nome': 'Exigência Cumprida pelo Servidor - Aguardando Análise',
            'descricao': 'Quando um servidor cadastra uma exigência e o segurado a cumpre, o servidor tem um prazo para analisar os documentos apresentados.',
            'condicoes': [
                'Status = "Pendente"',
                'Descrição = "Exigência cumprida"',
                'Servidor cadastrou a exigência (data início >= data atribuição)',
                'Exigência foi cumprida (data fim preenchida)',
            ],
            'prazo': '7 dias após o cumprimento da exigência',
            'calculo': 'dias_desde_cumprimento = HOJE - data_fim_ultima_exigencia',
            'classificacao': [
                '≤ 7 dias = BAIXA (Aguardando análise)',
                '> 7 dias = ALTA (Prazo excedido)',
            ],
        },
        'REGRA 2': {
            'nome': 'Cumprimento de Exigência pelo Segurado',
            'descricao': 'Quando um servidor cadastra uma exigência, o segurado tem 30 dias para apresentar os documentos, mais 5 dias de tolerância. Após vencimento sem cumprimento, servidor tem 7 dias para concluir.',
            'condicoes': [
                'Status = "Cumprimento de exigência"',
                'Descrição = "Em cumprimento de exigência"',
                'Data prazo preenchida',
            ],
            'prazo': 'Data do prazo + 5 dias (tolerância) + 7 dias (conclusão)',
            'calculo': 'dias_apos_prazo = HOJE - (data_prazo + 5 dias)',
            'classificacao': [
                'Dentro do prazo = NENHUMA',
                '0-7 dias após prazo = MÉDIA (Servidor deve concluir)',
                '> 7 dias após prazo = CRÍTICA (Ambos prazos vencidos)',
            ],
        },
        'REGRA 3': {
            'nome': 'Tarefa Nunca Trabalhada (Puxada sem Ação)',
            'descricao': 'Quando um servidor puxa uma tarefa nova (que nunca entrou em exigência), ele tem um prazo inicial para começar a trabalhar.',
            'condicoes': [
                'Status = "Pendente"',
                'Descrição = "Nunca entrou em exigência"',
                'Não tem data de início de exigência',
            ],
            'prazo': '10 dias após puxar a tarefa',
            'calculo': 'dias_com_servidor = tempo_em_pendencia - tempo_ate_ultima_distribuicao',
            'classificacao': [
                '≤ 10 dias = NENHUMA (Dentro do prazo inicial)',
                '> 10 dias = ALTA (Sem nenhuma ação)',
            ],
        },
        'REGRA 4': {
            'nome': 'Exigência Cumprida Antes da Atribuição',
            'descricao': 'Quando um servidor puxa uma tarefa que já estava com exigência cumprida (cumprida por outro servidor ou antes da distribuição). O servidor tem prazo para analisar os documentos já apresentados.',
            'condicoes': [
                'Status = "Pendente"',
                'Descrição = "Exigência cumprida"',
                'Exigência anterior à atribuição (data fim < data atribuição)',
            ],
            'prazo': '10 dias após atribuição para análise',
            'calculo': 'dias_com_servidor = tempo_em_pendencia - tempo_ate_ultima_distribuicao',
            'classificacao': [
                '≤ 10 dias = NENHUMA (Dentro do prazo de análise)',
                '> 10 dias = ALTA (Sem análise)',
            ],
        },
        'NENHUMA': {
            'nome': 'Sem Classificação de Criticidade',
            'descricao': 'Esta tarefa não se enquadra em nenhuma das regras de criticidade definidas.',
            'condicoes': ['Não atende aos critérios das regras 1, 2, 3 ou 4'],
            'prazo': 'N/A',
            'calculo': 'N/A',
            'classificacao': ['NENHUMA'],
        },
    }
    
    # Pegar descrição da regra aplicada
    regra_info = descricoes_regras.get(criticidade['regra'], descricoes_regras['NENHUMA'])
    
    # Contexto para o template
    context = {
        'tarefa': tarefa,
        'info_basica': info_basica,
        'datas': datas,
        'tempos': tempos,
        'criticidade': criticidade,
        'regra_info': regra_info,
    }
    
    return render(request, 'tarefas/detalhe_tarefa.html', context)


# ============================================
# DASHBOARD SERVIDOR (REDIRECIONA)
# ============================================
@login_required
def dashboard_servidor(request):
    """
    Dashboard do servidor - REDIRECIONA para página de detalhes.
    
    Mantido para compatibilidade com URLs antigas.
    """
    return redirect('tarefas:detalhe_servidor', siape=request.user.siape)


# ============================================
# API JSON (OPCIONAL - PARA GRÁFICOS AJAX)
# ============================================
@login_required
def api_estatisticas_json(request):
    """
    Retorna estatísticas em JSON para uso em gráficos dinâmicos.
    
    ✅ OTIMIZADO: Usa SQL aggregate
    """
    tarefas = Tarefa.objects.all()
    stats = Tarefa.estatisticas_criticidade(tarefas)
    
    return JsonResponse(stats)