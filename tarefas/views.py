"""
VIEWS COMPLETAS - SISTEMA DE 5 NÍVEIS DE CRITICIDADE
Arquitetura Limpa e Modular - VERSÃO OTIMIZADA E REFATORADA v3.0

✅ REFATORAÇÃO v3.0 - MELHORIAS DE UX PROFISSIONAL:
- Links clicáveis para protocolos (abre INSS em nova aba)
- Alertas clicáveis que redirecionam para detalhe da tarefa
- Descrição detalhada e alerta exibidos nas tabelas
- Gráficos com informações de criticidade expandidas
- Template detalhe_tarefa completamente redesenhado
- Cards de regras nos dashboards
- Contexto rico para todos os templates

ESTRUTURA:
1. Dashboard Coordenador (KPIs + Gráficos + Cards de Regras)
2. Dashboard Servidor (redireciona para detalhes)
3. Lista de Tarefas (com filtros + alertas clicáveis)
4. Lista de Servidores (com filtros)
5. Detalhes do Servidor (com cards de regras)
6. Detalhes da Tarefa (REDESENHADO - layout profissional)
7. Redirecionamento pós-login

Arquivo: tarefas/views.py
Data: 24/10/2025
"""

from datetime import date, timedelta
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.http import JsonResponse
from tarefas.models import Tarefa
from tarefas.parametros import ParametrosAnalise

User = get_user_model()


# ============================================
# HELPER: INFORMAÇÕES DE REGRAS
# ============================================
def get_regras_info():
    """
    Retorna informações detalhadas sobre todas as regras de criticidade.
    Usado para exibir cards informativos nos dashboards.
    """
    # Buscar parâmetros atuais
    try:
        params = ParametrosAnalise.get_configuracao_ativa()
    except:
        params = None
    
    return {
        'REGRA 1': {
            'numero': 'REGRA 1',
            'nome': 'Exigência Cumprida - Aguardando Análise',
            'descricao': 'Servidor cadastrou exigência que foi cumprida pelo segurado. Aguardando análise dos documentos.',
            'prazo': f"{params.prazo_analise_exigencia_cumprida if params else 7} dias após cumprimento",
            'badge_class': 'bg-info',
            'icon': 'fas fa-file-check',
            'exemplo': 'Status: Pendente + Exigência cumprida (após atribuição)'
        },
        'REGRA 2': {
            'numero': 'REGRA 2',
            'nome': 'Cumprimento de Exigência pelo Segurado',
            'descricao': 'Segurado tem prazo para cumprir exigência. Após vencimento, servidor tem prazo para conclusão.',
            'prazo': f"Prazo + {params.prazo_tolerancia_exigencia if params else 5} dias (tolerância) + {params.prazo_servidor_apos_vencimento if params else 7} dias (conclusão)",
            'badge_class': 'bg-warning',
            'icon': 'fas fa-hourglass-half',
            'exemplo': 'Status: Cumprimento de exigência + Prazo definido'
        },
        'REGRA 3': {
            'numero': 'REGRA 3',
            'nome': 'Tarefa Nunca Trabalhada',
            'descricao': 'Servidor puxou tarefa nova que nunca entrou em exigência. Tem prazo para primeira ação.',
            'prazo': f"{params.prazo_primeira_acao if params else 10} dias após puxar tarefa",
            'badge_class': 'bg-primary',
            'icon': 'fas fa-play-circle',
            'exemplo': 'Status: Pendente + Nunca entrou em exigência'
        },
        'REGRA 4': {
            'numero': 'REGRA 4',
            'nome': 'Exigência Cumprida Anterior',
            'descricao': 'Servidor puxou tarefa com exigência já cumprida (por outro servidor). Tem prazo para análise.',
            'prazo': f"{params.prazo_primeira_acao if params else 10} dias após atribuição",
            'badge_class': 'bg-success',
            'icon': 'fas fa-history',
            'exemplo': 'Status: Pendente + Exigência cumprida (antes da atribuição)'
        }
    }


def get_regras_resumo_servidor(tarefas_servidor):
    """
    Calcula resumo de tarefas por regra para um servidor específico.
    Usado para exibir cards de regras nos detalhes do servidor.
    """
    regras_info = get_regras_info()
    resumo = {}
    
    for regra_key, info in regras_info.items():
        count = tarefas_servidor.filter(regra_aplicada_calculado=regra_key).count()
        resumo[regra_key] = {
            'nome': info['nome'],
            'descricao': info['descricao'],
            'prazo': info['prazo'],
            'count': count,
            'badge_class': info['badge_class'],
            'icon': info['icon']
        }
    
    return resumo


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
        return redirect('tarefas:detalhe_servidor', siape=user.siape)
    
    # Outros usuários
    else:
        return redirect('/')


# ============================================
# DASHBOARD COORDENADOR (EXPANDIDO)
# ============================================
@login_required
def dashboard_coordenador(request):
    """
    Dashboard do coordenador - VERSÃO EXPANDIDA v3.0
    
    Exibe:
    - 6 KPIs de criticidade
    - 3 Gráficos Chart.js (Criticidade, Status, Regras)
    - 4 Cards de regras com contadores
    - 2 Botões de ação
    
    ✅ OTIMIZAÇÃO: SQL aggregate
    """
    
    # Buscar todas as tarefas
    tarefas = Tarefa.objects.select_related('siape_responsavel').all()
    
    # Calcular estatísticas (OTIMIZADO)
    stats = Tarefa.estatisticas_criticidade(tarefas)
    
    # KPIs gerais
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
            (stats['com_criticidade'] / stats['total'] * 100) if stats['total'] > 0 else 0, 1
        ),
    }
    
    # Contadores por status
    status_counts = {
        'pendentes': tarefas.filter(status_tarefa='Pendente').count(),
        'cumprimento': tarefas.filter(status_tarefa='Cumprimento de exigência').count(),
        'outros': tarefas.exclude(status_tarefa__in=['Pendente', 'Cumprimento de exigência']).count(),
    }
    
    # ✅ NOVO: Resumo por regras
    regras_info = get_regras_info()
    regras_resumo = {}
    for regra_key, info in regras_info.items():
        count = tarefas.filter(regra_aplicada_calculado=regra_key).count()
        regras_resumo[regra_key] = {
            'nome': info['nome'],
            'descricao': info['descricao'],
            'prazo': info['prazo'],
            'count': count,
            'badge_class': info['badge_class'],
            'icon': info['icon']
        }
    
    # Gráficos
    grafico_criticidade = {
        'labels': json.dumps(['Críticas', 'Altas', 'Médias', 'Baixas', 'Normais']),
        'data': json.dumps([stats['CRÍTICA'], stats['ALTA'], stats['MÉDIA'], stats['BAIXA'], stats['NENHUMA']]),
        'colors': json.dumps(['#dc3545', '#fd7e14', '#ffc107', '#28a745', '#6c757d'])
    }
    
    grafico_status = {
        'labels': json.dumps(['Pendente', 'Cumprimento', 'Outros']),
        'data': json.dumps([status_counts['pendentes'], status_counts['cumprimento'], status_counts['outros']]),
        'colors': json.dumps(['#ffc107', '#17a2b8', '#6c757d'])
    }
    
    # ✅ NOVO: Gráfico de regras
    grafico_regras = {
        'labels': json.dumps(['Regra 1', 'Regra 2', 'Regra 3', 'Regra 4']),
        'data': json.dumps([
            regras_resumo['REGRA 1']['count'],
            regras_resumo['REGRA 2']['count'],
            regras_resumo['REGRA 3']['count'],
            regras_resumo['REGRA 4']['count'],
        ]),
        'colors': json.dumps(['#17a2b8', '#ffc107', '#007bff', '#28a745'])
    }
    
    context = {
        'kpis_gerais': kpis_gerais,
        'status_counts': status_counts,
        'regras_resumo': regras_resumo,
        'grafico_criticidade': grafico_criticidade,
        'grafico_status': grafico_status,
        'grafico_regras': grafico_regras,
        'data_atualizacao': date.today(),
    }
    
    return render(request, 'dashboards/dashboard_coordenador.html', context)


# ============================================
# LISTA DE TAREFAS
# ============================================
@login_required
def lista_tarefas(request):
    """
    Lista completa de tarefas com filtros OTIMIZADOS.
    
    ✅ v3.0:
    - Alertas clicáveis
    - Protocolos clicáveis (INSS)
    - Descrição na tabela
    """
    
    # Buscar tarefas
    tarefas = Tarefa.objects.select_related('siape_responsavel').all()
    
    # Filtros
    protocolo = request.GET.get('protocolo', '').strip()
    if protocolo:
        tarefas = tarefas.filter(numero_protocolo_tarefa__icontains=protocolo)
    
    nivel = request.GET.get('nivel', '')
    if nivel:
        tarefas = tarefas.filter(nivel_criticidade_calculado=nivel)
    
    status = request.GET.get('status', '')
    if status:
        tarefas = tarefas.filter(status_tarefa=status)
    
    servidor = request.GET.get('servidor', '').strip()
    if servidor:
        tarefas = tarefas.filter(
            Q(siape_responsavel__siape__icontains=servidor) |
            Q(nome_profissional_responsavel__icontains=servidor)
        )
    
    servico = request.GET.get('servico', '').strip()
    if servico:
        tarefas = tarefas.filter(nome_servico__icontains=servico)
    
    data_inicio = request.GET.get('data_inicio', '')
    if data_inicio:
        tarefas = tarefas.filter(data_distribuicao_tarefa__gte=data_inicio)
    
    data_fim = request.GET.get('data_fim', '')
    if data_fim:
        tarefas = tarefas.filter(data_distribuicao_tarefa__lte=data_fim)
    
    # Ordenação
    tarefas = tarefas.order_by('-pontuacao_criticidade', '-tempo_em_pendencia_em_dias')
    
    # Estatísticas
    stats = Tarefa.estatisticas_criticidade(tarefas)
    
    kpis = {
        'total': stats['total'],
        'criticas': stats['CRÍTICA'],
        'altas': stats['ALTA'],
        'medias': stats['MÉDIA'],
        'baixas': stats['BAIXA'],
        'normais': stats['NENHUMA'],
        'com_criticidade': stats['com_criticidade'],
    }
    
    # Paginação
    paginator = Paginator(tarefas, 50)
    page_number = request.GET.get('page')
    tarefas_paginadas = paginator.get_page(page_number)
    
    context = {
        'tarefas': tarefas_paginadas,
        'kpis': kpis,
        'filtros_ativos': {
            'protocolo': protocolo,
            'nivel': nivel,
            'status': status,
            'servidor': servidor,
            'servico': servico,
            'data_inicio': data_inicio,
            'data_fim': data_fim,
        },
        'niveis_disponiveis': ['CRÍTICA', 'ALTA', 'MÉDIA', 'BAIXA', 'NENHUMA'],
        'status_disponiveis': Tarefa.objects.values_list('status_tarefa', flat=True).distinct(),
    }
    
    return render(request, 'tarefas/lista_tarefas.html', context)


# ============================================
# LISTA DE SERVIDORES
# ============================================
@login_required
def lista_servidores(request):
    """Lista de servidores com resumo."""
    
    # Buscar servidores com tarefas
    servidores_com_tarefas = Tarefa.objects.values('siape_responsavel').distinct().exclude(siape_responsavel__isnull=True)
    siapes = [s['siape_responsavel'] for s in servidores_com_tarefas]
    servidores = User.objects.filter(siape__in=siapes)
    
    # Filtros
    nome = request.GET.get('nome', '').strip()
    if nome:
        servidores = servidores.filter(nome_completo__icontains=nome)
    
    siape_filtro = request.GET.get('siape', '').strip()
    if siape_filtro:
        servidores = servidores.filter(siape__icontains=siape_filtro)
    
    gex = request.GET.get('gex', '').strip()
    if gex:
        servidores = servidores.filter(gex__icontains=gex)
    
    # Montar lista com stats
    lista_servidores = []
    for servidor in servidores:
        tarefas_servidor = Tarefa.objects.filter(siape_responsavel=servidor)
        stats = Tarefa.estatisticas_criticidade(tarefas_servidor)
        
        lista_servidores.append({
            'servidor': servidor,
            'total': stats['total'],
            'criticas': stats['CRÍTICA'],
            'altas': stats['ALTA'],
            'medias': stats['MÉDIA'],
            'baixas': stats['BAIXA'],
            'normais': stats['NENHUMA'],
        })
    
    # Ordenação
    ordem = request.GET.get('ordem', 'criticas')
    if ordem == 'criticas':
        lista_servidores.sort(key=lambda x: x['criticas'], reverse=True)
    elif ordem == 'total':
        lista_servidores.sort(key=lambda x: x['total'], reverse=True)
    elif ordem == 'nome':
        lista_servidores.sort(key=lambda x: x['servidor'].nome_completo)
    
    # Paginação
    paginator = Paginator(lista_servidores, 20)
    page_number = request.GET.get('page')
    servidores_paginados = paginator.get_page(page_number)
    
    # Stats gerais
    total_servidores = len(lista_servidores)
    total_criticas = sum(s['criticas'] for s in lista_servidores)
    total_altas = sum(s['altas'] for s in lista_servidores)
    
    context = {
        'servidores': servidores_paginados,
        'filtros_ativos': {'nome': nome, 'siape': siape_filtro, 'gex': gex, 'ordem': ordem},
        'total_servidores': total_servidores,
        'total_criticas': total_criticas,
        'total_altas': total_altas,
    }
    
    return render(request, 'tarefas/lista_servidores.html', context)


# ============================================
# DETALHES DO SERVIDOR
# ============================================
@login_required
def detalhe_servidor(request, siape):
    """
    Detalhes do servidor COM CARDS DE REGRAS.
    
    ✅ v3.0: Cards de regras, links clicáveis
    """
    
    # Buscar servidor
    servidor = get_object_or_404(User, siape=siape)
    
    # Tarefas do servidor
    tarefas = Tarefa.objects.filter(siape_responsavel=servidor)
    
    # ✅ NOVO: Resumo por regras
    regras_resumo = get_regras_resumo_servidor(tarefas)
    
    # Stats
    stats = Tarefa.estatisticas_criticidade(tarefas)
    
    kpis = {
        'total': stats['total'],
        'criticas': stats['CRÍTICA'],
        'altas': stats['ALTA'],
        'medias': stats['MÉDIA'],
        'baixas': stats['BAIXA'],
        'normais': stats['NENHUMA'],
    }
    
    # Top 10 prioritárias
    tarefas_prioritarias = tarefas.filter(
        nivel_criticidade_calculado__in=['CRÍTICA', 'ALTA', 'MÉDIA']
    ).order_by('-pontuacao_criticidade')[:10]
    
    # Resumo por serviço
    servicos = tarefas.values('nome_servico').annotate(total=Count('numero_protocolo_tarefa')).order_by('-total')[:10]
    
    servicos_resumo = []
    for servico in servicos:
        tarefas_servico = tarefas.filter(nome_servico=servico['nome_servico'])
        stats_servico = Tarefa.estatisticas_criticidade(tarefas_servico)
        servicos_resumo.append({
            'nome': servico['nome_servico'],
            'total': stats_servico['total'],
            'criticas': stats_servico['CRÍTICA'],
            'altas': stats_servico['ALTA'],
            'medias': stats_servico['MÉDIA'],
        })
    
    # Gráfico
    grafico_criticidade = {
        'labels': json.dumps(['Críticas', 'Altas', 'Médias', 'Baixas', 'Normais']),
        'data': json.dumps([stats['CRÍTICA'], stats['ALTA'], stats['MÉDIA'], stats['BAIXA'], stats['NENHUMA']]),
        'colors': json.dumps(['#dc3545', '#fd7e14', '#ffc107', '#28a745', '#6c757d'])
    }
    
    # Lista completa
    tarefas_ordenadas = tarefas.order_by('-pontuacao_criticidade', '-tempo_em_pendencia_em_dias')
    
    # Paginação
    paginator = Paginator(tarefas_ordenadas, 50)
    page_number = request.GET.get('page')
    tarefas_paginadas = paginator.get_page(page_number)
    
    context = {
        'servidor': servidor,
        'kpis': kpis,
        'regras_resumo': regras_resumo,
        'tarefas_prioritarias': tarefas_prioritarias,
        'servicos_resumo': servicos_resumo,
        'grafico_criticidade': grafico_criticidade,
        'tarefas': tarefas_paginadas,
        'eh_proprio_servidor': request.user == servidor,
    }
    
    return render(request, 'tarefas/detalhe_servidor.html', context)


# ============================================
# DETALHES DA TAREFA (REDESENHADO)
# ============================================
@login_required
def detalhe_tarefa(request, protocolo):
    """
    Detalhes completos da tarefa - REDESENHADO v3.0
    
    ✅ Layout profissional com todas informações
    """
    
    # Buscar tarefa
    tarefa = get_object_or_404(Tarefa, numero_protocolo_tarefa=protocolo)
    
    # Info básica
    info_basica = {
        'protocolo': tarefa.numero_protocolo_tarefa,
        'servico': tarefa.nome_servico,
        'status': tarefa.status_tarefa,
        'servidor': tarefa.nome_profissional_responsavel or 'Não atribuído',
        'siape': tarefa.siape_responsavel.siape if tarefa.siape_responsavel else 'N/A',
        'gex': tarefa.nome_gex_responsavel or 'N/A',
    }
    
    # Datas
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
    
    # Criticidade (COMPLETA)
    criticidade = {
        'nivel': tarefa.nivel_criticidade_calculado,
        'regra': tarefa.regra_aplicada_calculado,
        'alerta': tarefa.alerta_criticidade_calculado,
        'descricao': tarefa.descricao_criticidade_calculado,
        'dias_pendente': tarefa.dias_pendente_criticidade_calculado,
        'prazo_limite': tarefa.prazo_limite_criticidade_calculado,
        'cor': tarefa.cor_criticidade_calculado,
        'emoji': tarefa.emoji_criticidade,
        'pontuacao': tarefa.pontuacao_criticidade,
    }
    
    # Info da regra
    regras_info = get_regras_info()
    regra_info = regras_info.get(criticidade['regra'], {
        'nome': 'Sem classificação',
        'descricao': 'Não se enquadra em nenhuma regra.',
        'prazo': 'N/A',
        'condicoes': [],
        'calculo': 'N/A',
        'classificacao': [],
    })
    
    # Adicionar detalhes específicos da regra
    if criticidade['regra'] == 'REGRA 1':
        regra_info['condicoes'] = [
            'Status = "Pendente"',
            'Descrição = "Exigência cumprida"',
            'Servidor cadastrou a exigência',
            'Exigência foi cumprida',
        ]
        regra_info['calculo'] = f'dias_desde_cumprimento = HOJE - {tarefa.data_fim_ultima_exigencia.strftime("%d/%m/%Y") if tarefa.data_fim_ultima_exigencia else "N/A"}'
        regra_info['classificacao'] = ['≤ 7 dias = BAIXA', '> 7 dias = ALTA']
        
    elif criticidade['regra'] == 'REGRA 2':
        regra_info['condicoes'] = [
            'Status = "Cumprimento de exigência"',
            'Descrição = "Em cumprimento"',
            f'Data prazo: {tarefa.data_prazo.strftime("%d/%m/%Y") if tarefa.data_prazo else "N/A"}',
        ]
        regra_info['calculo'] = f'dias_apos_prazo = HOJE - ({tarefa.data_prazo.strftime("%d/%m/%Y") if tarefa.data_prazo else "N/A"} + 5 dias)'
        regra_info['classificacao'] = ['Dentro = NENHUMA', '0-7 dias = MÉDIA', '> 7 dias = CRÍTICA']
        
    elif criticidade['regra'] == 'REGRA 3':
        regra_info['condicoes'] = [
            'Status = "Pendente"',
            'Nunca entrou em exigência',
            'Sem data de início',
        ]
        regra_info['calculo'] = f'dias_com_servidor = {tarefa.tempo_em_pendencia_em_dias} - {tarefa.tempo_ate_ultima_distribuicao_tarefa_em_dias}'
        regra_info['classificacao'] = ['≤ 10 dias = NENHUMA', '> 10 dias = ALTA']
        
    elif criticidade['regra'] == 'REGRA 4':
        regra_info['condicoes'] = [
            'Status = "Pendente"',
            'Exigência cumprida anterior',
            'Data fim < data atribuição',
        ]
        regra_info['calculo'] = f'dias_com_servidor = {tarefa.tempo_em_pendencia_em_dias} - {tarefa.tempo_ate_ultima_distribuicao_tarefa_em_dias}'
        regra_info['classificacao'] = ['≤ 10 dias = NENHUMA', '> 10 dias = ALTA']
    
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
    """Redireciona para detalhes do servidor."""
    return redirect('tarefas:detalhe_servidor', siape=request.user.siape)


# ============================================
# API JSON
# ============================================
@login_required
def api_estatisticas_json(request):
    """Retorna estatísticas em JSON."""
    tarefas = Tarefa.objects.all()
    stats = Tarefa.estatisticas_criticidade(tarefas)
    return JsonResponse(stats)