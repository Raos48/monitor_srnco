"""
VIEWS PARA JUSTIFICATIVAS E SOLICITAÇÕES DE AJUDA
Arquivo: tarefas/views_justificativas.py (criar novo arquivo)
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Count, Case, When, IntegerField
from django.utils import timezone
from django.core.paginator import Paginator

from .models import Tarefa, Justificativa, SolicitacaoAjuda, TipoJustificativa
from .forms import (
    JustificativaForm, 
    AvaliacaoJustificativaForm,
    SolicitacaoAjudaForm,
    AtendimentoSolicitacaoForm,
    FiltroJustificativasForm,
    FiltroSolicitacoesForm
)


# ============================================================================
# FUNÇÕES AUXILIARES PARA VERIFICAÇÃO DE PERMISSÕES
# ============================================================================

def usuario_eh_equipe_volante(user):
    """Verifica se o usuário pertence ao grupo Equipe Volante"""
    return user.groups.filter(name='Equipe Volante').exists() or user.is_staff


def usuario_eh_coordenador(user):
    """Verifica se o usuário é coordenador"""
    return user.groups.filter(name='Coordenador').exists() or user.is_staff


# ============================================================================
# VIEWS PARA SERVIDOR - SUBMETER JUSTIFICATIVAS E SOLICITAR AJUDA
# ============================================================================

@login_required
def submeter_justificativa(request, protocolo):
    """
    Permite que o servidor submeta uma justificativa para uma tarefa crítica.
    
    Args:
        protocolo: Número do protocolo da tarefa
    """
    tarefa = get_object_or_404(Tarefa, numero_protocolo_tarefa=protocolo)
    
    # Verifica se o servidor é o responsável pela tarefa
    if tarefa.siape_responsavel != request.user:
        messages.error(request, 'Você não tem permissão para justificar esta tarefa.')
        return redirect('tarefas:detalhe_tarefa', protocolo=protocolo)
    
    # Verifica se pode submeter justificativa
    if not tarefa.pode_submeter_justificativa():
        messages.warning(
            request, 
            'Esta tarefa já possui uma justificativa pendente ou aprovada.'
        )
        return redirect('tarefas:detalhe_tarefa', protocolo=protocolo)
    
    if request.method == 'POST':
        form = JustificativaForm(request.POST)
        if form.is_valid():
            justificativa = form.save(commit=False)
            justificativa.tarefa = tarefa
            justificativa.servidor = request.user
            justificativa.protocolo_original = tarefa.numero_protocolo_tarefa
            justificativa.status = 'PENDENTE'
            justificativa.save()
            
            # Atualiza flags da tarefa
            tarefa.atualizar_flags_justificativa()
            
            # Recalcula criticidade
            from .analisador import aplicar_analise_criticidade
            aplicar_analise_criticidade(tarefa)
            tarefa.save()
            
            messages.success(
                request,
                'Justificativa submetida com sucesso! Aguardando análise da Equipe Volante.'
            )
            return redirect('tarefas:detalhe_tarefa', protocolo=protocolo)
    else:
        form = JustificativaForm()
    
    context = {
        'tarefa': tarefa,
        'form': form,
        'tipos_disponiveis': TipoJustificativa.objects.filter(ativo=True),
    }
    
    return render(request, 'tarefas/submeter_justificativa.html', context)


@login_required
def solicitar_ajuda(request, protocolo):
    """
    Permite que o servidor solicite ajuda da Equipe Volante para uma tarefa.
    
    Args:
        protocolo: Número do protocolo da tarefa
    """
    tarefa = get_object_or_404(Tarefa, numero_protocolo_tarefa=protocolo)
    
    # Verifica se o servidor é o responsável pela tarefa
    if tarefa.siape_responsavel != request.user:
        messages.error(request, 'Você não tem permissão para solicitar ajuda para esta tarefa.')
        return redirect('tarefas:detalhe_tarefa', protocolo=protocolo)
    
    # Verifica se já tem solicitação pendente
    tem_pendente = tarefa.solicitacoes_ajuda.filter(
        status__in=['PENDENTE', 'EM_ATENDIMENTO']
    ).exists()
    
    if tem_pendente:
        messages.warning(
            request,
            'Esta tarefa já possui uma solicitação de ajuda em andamento.'
        )
        return redirect('tarefas:detalhe_tarefa', protocolo=protocolo)
    
    if request.method == 'POST':
        form = SolicitacaoAjudaForm(request.POST)
        if form.is_valid():
            solicitacao = form.save(commit=False)
            solicitacao.tarefa = tarefa
            solicitacao.servidor_solicitante = request.user
            solicitacao.protocolo_original = tarefa.numero_protocolo_tarefa
            solicitacao.status = 'PENDENTE'
            solicitacao.save()
            
            # Atualiza flags da tarefa
            tarefa.atualizar_flags_justificativa()
            
            messages.success(
                request,
                'Solicitação de ajuda enviada com sucesso! A Equipe Volante foi notificada.'
            )
            return redirect('tarefas:detalhe_tarefa', protocolo=protocolo)
    else:
        form = SolicitacaoAjudaForm()
    
    context = {
        'tarefa': tarefa,
        'form': form,
    }
    
    return render(request, 'tarefas/solicitar_ajuda.html', context)


@login_required
def minhas_justificativas(request):
    """
    Lista todas as justificativas submetidas pelo servidor logado.
    """
    justificativas = Justificativa.objects.filter(
        servidor=request.user
    ).select_related(
        'tarefa',
        'tipo_justificativa',
        'analisado_por'
    ).order_by('-data_submissao')
    
    # Estatísticas
    stats = {
        'total': justificativas.count(),
        'pendentes': justificativas.filter(status='PENDENTE').count(),
        'aprovadas': justificativas.filter(status='APROVADA').count(),
        'reprovadas': justificativas.filter(status='REPROVADA').count(),
    }
    
    # Paginação
    paginator = Paginator(justificativas, 20)
    page = request.GET.get('page', 1)
    justificativas_page = paginator.get_page(page)
    
    context = {
        'justificativas': justificativas_page,
        'stats': stats,
    }
    
    return render(request, 'tarefas/minhas_justificativas.html', context)


@login_required
def minhas_solicitacoes(request):
    """
    Lista todas as solicitações de ajuda do servidor logado.
    """
    solicitacoes = SolicitacaoAjuda.objects.filter(
        servidor_solicitante=request.user
    ).select_related(
        'tarefa',
        'atendido_por'
    ).order_by('-data_solicitacao')
    
    # Estatísticas
    stats = {
        'total': solicitacoes.count(),
        'pendentes': solicitacoes.filter(status='PENDENTE').count(),
        'em_atendimento': solicitacoes.filter(status='EM_ATENDIMENTO').count(),
        'concluidas': solicitacoes.filter(status='CONCLUIDA').count(),
    }
    
    # Paginação
    paginator = Paginator(solicitacoes, 20)
    page = request.GET.get('page', 1)
    solicitacoes_page = paginator.get_page(page)
    
    context = {
        'solicitacoes': solicitacoes_page,
        'stats': stats,
    }
    
    return render(request, 'tarefas/minhas_solicitacoes.html', context)


# ============================================================================
# VIEWS PARA EQUIPE VOLANTE - ANÁLISE DE JUSTIFICATIVAS
# ============================================================================

@login_required
@user_passes_test(usuario_eh_equipe_volante)
def painel_equipe_volante(request):
    """
    Dashboard principal da Equipe Volante com visão geral de justificativas
    e solicitações pendentes.
    """
    # Justificativas pendentes
    justificativas_pendentes = Justificativa.objects.filter(
        status='PENDENTE'
    ).select_related(
        'tarefa',
        'servidor',
        'tipo_justificativa'
    ).order_by('data_submissao')
    
    # Solicitações pendentes
    solicitacoes_pendentes = SolicitacaoAjuda.objects.filter(
        status__in=['PENDENTE', 'EM_ATENDIMENTO']
    ).select_related(
        'tarefa',
        'servidor_solicitante',
        'atendido_por'
    ).order_by('data_solicitacao')
    
    # Estatísticas gerais
    stats = {
        'justificativas_pendentes': justificativas_pendentes.count(),
        'solicitacoes_pendentes': solicitacoes_pendentes.filter(status='PENDENTE').count(),
        'solicitacoes_em_atendimento': solicitacoes_pendentes.filter(status='EM_ATENDIMENTO').count(),
        'justificativas_aprovadas_hoje': Justificativa.objects.filter(
            status='APROVADA',
            data_analise__date=timezone.now().date()
        ).count(),
        'solicitacoes_concluidas_hoje': SolicitacaoAjuda.objects.filter(
            status='CONCLUIDA',
            data_conclusao__date=timezone.now().date()
        ).count(),
    }
    
    # Distribuição por tipo de justificativa (pendentes)
    tipos_distribuicao = justificativas_pendentes.values(
        'tipo_justificativa__nome'
    ).annotate(
        total=Count('id')
    ).order_by('-total')
    
    context = {
        'justificativas_pendentes': justificativas_pendentes[:10],  # Primeiras 10
        'solicitacoes_pendentes': solicitacoes_pendentes[:10],  # Primeiras 10
        'stats': stats,
        'tipos_distribuicao': tipos_distribuicao,
    }
    
    return render(request, 'tarefas/painel_equipe_volante.html', context)


@login_required
@user_passes_test(usuario_eh_equipe_volante)
def lista_justificativas_analise(request):
    """
    Lista completa de justificativas para análise pela Equipe Volante.
    Com filtros avançados.
    """
    # Query base
    justificativas = Justificativa.objects.select_related(
        'tarefa',
        'servidor',
        'tipo_justificativa',
        'analisado_por'
    )
    
    # Aplicar filtros
    form = FiltroJustificativasForm(request.GET)
    
    if form.is_valid():
        if form.cleaned_data.get('status'):
            justificativas = justificativas.filter(status=form.cleaned_data['status'])
        
        if form.cleaned_data.get('tipo'):
            justificativas = justificativas.filter(tipo_justificativa=form.cleaned_data['tipo'])
        
        if form.cleaned_data.get('servidor'):
            servidor_busca = form.cleaned_data['servidor']
            justificativas = justificativas.filter(
                Q(servidor__siape__icontains=servidor_busca) |
                Q(servidor__nome_completo__icontains=servidor_busca)
            )
        
        if form.cleaned_data.get('protocolo'):
            justificativas = justificativas.filter(
                protocolo_original__icontains=form.cleaned_data['protocolo']
            )
        
        if form.cleaned_data.get('data_inicial'):
            justificativas = justificativas.filter(
                data_submissao__date__gte=form.cleaned_data['data_inicial']
            )

        if form.cleaned_data.get('data_final'):
            justificativas = justificativas.filter(
                data_submissao__date__lte=form.cleaned_data['data_final']
            )
    
    # Ordenação
    justificativas = justificativas.order_by(
        Case(
            When(status='PENDENTE', then=0),
            When(status='APROVADA', then=1),
            When(status='REPROVADA', then=2),
            default=3,
            output_field=IntegerField()
        ),
        '-data_submissao'
    )
    
    # Estatísticas
    stats = {
        'total': justificativas.count(),
        'pendentes': justificativas.filter(status='PENDENTE').count(),
        'aprovadas': justificativas.filter(status='APROVADA').count(),
        'reprovadas': justificativas.filter(status='REPROVADA').count(),
    }
    
    # Paginação
    paginator = Paginator(justificativas, 25)
    page = request.GET.get('page', 1)
    justificativas_page = paginator.get_page(page)
    
    context = {
        'justificativas': justificativas_page,
        'form': form,
        'stats': stats,
    }
    
    return render(request, 'tarefas/lista_justificativas_analise.html', context)



"""
VIEWS PARA JUSTIFICATIVAS E SOLICITAÇÕES - PARTE 2
Continuação do arquivo: tarefas/views_justificativas.py
"""

@login_required
@user_passes_test(usuario_eh_equipe_volante)
def avaliar_justificativa(request, justificativa_id):
    """
    Permite que a Equipe Volante avalie (aprove ou reprove) uma justificativa.
    
    Args:
        justificativa_id: ID da justificativa
    """
    justificativa = get_object_or_404(
        Justificativa.objects.select_related('tarefa', 'servidor', 'tipo_justificativa'),
        id=justificativa_id
    )
    
    # Verifica se ainda está pendente
    if justificativa.status != 'PENDENTE':
        messages.warning(
            request,
            f'Esta justificativa já foi {justificativa.get_status_display().lower()}.'
        )
        return redirect('tarefas:detalhe_justificativa', justificativa_id=justificativa_id)
    
    if request.method == 'POST':
        form = AvaliacaoJustificativaForm(request.POST)
        if form.is_valid():
            decisao = form.cleaned_data['decisao']
            observacao = form.cleaned_data.get('observacao', '')
            
            if decisao == 'APROVAR':
                justificativa.aprovar(request.user, observacao)
                messages.success(
                    request,
                    f'Justificativa aprovada com sucesso! O protocolo {justificativa.protocolo_original} '
                    f'não será mais contabilizado como CRÍTICO.'
                )
            else:  # REPROVAR
                justificativa.reprovar(request.user, observacao)
                messages.info(
                    request,
                    f'Justificativa reprovada. O protocolo {justificativa.protocolo_original} '
                    f'permanecerá como CRÍTICO.'
                )
            
            # Atualiza flags e recalcula criticidade da tarefa
            tarefa = justificativa.tarefa
            tarefa.atualizar_flags_justificativa()
            
            from .analisador import aplicar_analise_criticidade
            aplicar_analise_criticidade(tarefa)
            tarefa.save()
            
            return redirect('tarefas:lista_justificativas_analise')
    else:
        form = AvaliacaoJustificativaForm()
    
    context = {
        'justificativa': justificativa,
        'form': form,
    }
    
    return render(request, 'tarefas/avaliar_justificativa.html', context)


@login_required
@user_passes_test(usuario_eh_equipe_volante)
def detalhe_justificativa(request, justificativa_id):
    """
    Exibe detalhes completos de uma justificativa.
    
    Args:
        justificativa_id: ID da justificativa
    """
    justificativa = get_object_or_404(
        Justificativa.objects.select_related(
            'tarefa',
            'servidor',
            'tipo_justificativa',
            'analisado_por'
        ),
        id=justificativa_id
    )
    
    context = {
        'justificativa': justificativa,
    }
    
    return render(request, 'tarefas/detalhe_justificativa.html', context)


# ============================================================================
# VIEWS PARA EQUIPE VOLANTE - SOLICITAÇÕES DE AJUDA
# ============================================================================

@login_required
@user_passes_test(usuario_eh_equipe_volante)
def lista_solicitacoes_ajuda(request):
    """
    Lista completa de solicitações de ajuda para a Equipe Volante.
    Com filtros.
    """
    # Query base
    solicitacoes = SolicitacaoAjuda.objects.select_related(
        'tarefa',
        'servidor_solicitante',
        'atendido_por'
    )
    
    # Aplicar filtros
    form = FiltroSolicitacoesForm(request.GET)
    
    if form.is_valid():
        if form.cleaned_data.get('status'):
            solicitacoes = solicitacoes.filter(status=form.cleaned_data['status'])
        
        if form.cleaned_data.get('servidor'):
            servidor_busca = form.cleaned_data['servidor']
            solicitacoes = solicitacoes.filter(
                Q(servidor_solicitante__siape__icontains=servidor_busca) |
                Q(servidor_solicitante__nome_completo__icontains=servidor_busca)
            )
        
        if form.cleaned_data.get('protocolo'):
            solicitacoes = solicitacoes.filter(
                protocolo_original__icontains=form.cleaned_data['protocolo']
            )
    
    # Ordenação: pendentes primeiro, depois em atendimento, depois concluídas
    solicitacoes = solicitacoes.order_by(
        Case(
            When(status='PENDENTE', then=0),
            When(status='EM_ATENDIMENTO', then=1),
            When(status='CONCLUIDA', then=2),
            default=3,
            output_field=IntegerField()
        ),
        '-data_solicitacao'
    )
    
    # Estatísticas
    stats = {
        'total': solicitacoes.count(),
        'pendentes': solicitacoes.filter(status='PENDENTE').count(),
        'em_atendimento': solicitacoes.filter(status='EM_ATENDIMENTO').count(),
        'concluidas': solicitacoes.filter(status='CONCLUIDA').count(),
    }
    
    # Paginação
    paginator = Paginator(solicitacoes, 25)
    page = request.GET.get('page', 1)
    solicitacoes_page = paginator.get_page(page)
    
    context = {
        'solicitacoes': solicitacoes_page,
        'form': form,
        'stats': stats,
    }
    
    return render(request, 'tarefas/lista_solicitacoes_ajuda.html', context)


@login_required
@user_passes_test(usuario_eh_equipe_volante)
def atender_solicitacao(request, solicitacao_id):
    """
    Permite que a Equipe Volante atenda uma solicitação de ajuda.
    
    Args:
        solicitacao_id: ID da solicitação
    """
    solicitacao = get_object_or_404(
        SolicitacaoAjuda.objects.select_related('tarefa', 'servidor_solicitante'),
        id=solicitacao_id
    )
    
    # Verifica se já foi concluída ou cancelada
    if solicitacao.status in ['CONCLUIDA', 'CANCELADA']:
        messages.warning(
            request,
            f'Esta solicitação já foi {solicitacao.get_status_display().lower()}.'
        )
        return redirect('tarefas:detalhe_solicitacao', solicitacao_id=solicitacao_id)
    
    if request.method == 'POST':
        form = AtendimentoSolicitacaoForm(request.POST)
        if form.is_valid():
            acao = form.cleaned_data['acao']
            observacao = form.cleaned_data.get('observacao', '')
            
            if acao == 'INICIAR':
                solicitacao.iniciar_atendimento(request.user)
                messages.success(
                    request,
                    f'Atendimento iniciado! A solicitação foi atribuída a você.'
                )
            elif acao == 'CONCLUIR':
                solicitacao.concluir(observacao)
                messages.success(
                    request,
                    f'Solicitação concluída com sucesso!'
                )
            else:  # CANCELAR
                solicitacao.cancelar(observacao)
                messages.info(
                    request,
                    f'Solicitação cancelada.'
                )
            
            # Atualiza flags da tarefa
            tarefa = solicitacao.tarefa
            tarefa.atualizar_flags_justificativa()
            
            return redirect('tarefas:lista_solicitacoes_ajuda')
    else:
        form = AtendimentoSolicitacaoForm()
    
    context = {
        'solicitacao': solicitacao,
        'form': form,
    }
    
    return render(request, 'tarefas/atender_solicitacao.html', context)


@login_required
@user_passes_test(usuario_eh_equipe_volante)
def detalhe_solicitacao(request, solicitacao_id):
    """
    Exibe detalhes completos de uma solicitação de ajuda.
    
    Args:
        solicitacao_id: ID da solicitação
    """
    solicitacao = get_object_or_404(
        SolicitacaoAjuda.objects.select_related(
            'tarefa',
            'servidor_solicitante',
            'atendido_por'
        ),
        id=solicitacao_id
    )
    
    context = {
        'solicitacao': solicitacao,
    }
    
    return render(request, 'tarefas/detalhe_solicitacao.html', context)


# ============================================================================
# VIEWS PARA COORDENADOR - RELATÓRIOS E ESTATÍSTICAS
# ============================================================================

@login_required
@user_passes_test(usuario_eh_coordenador)
def relatorio_justificativas_coordenador(request):
    """
    Relatório completo de justificativas para o coordenador.
    Mostra estatísticas por servidor, tipo, etc.
    """
    from django.db.models import Count, Q, F
    from usuarios.models import CustomUser
    
    # Estatísticas gerais
    stats_gerais = {
        'total_justificativas': Justificativa.objects.count(),
        'pendentes': Justificativa.objects.filter(status='PENDENTE').count(),
        'aprovadas': Justificativa.objects.filter(status='APROVADA').count(),
        'reprovadas': Justificativa.objects.filter(status='REPROVADAS').count(),
        'total_tarefas': Tarefa.objects.filter(ativa=True).count(),
        'tarefas_com_justificativa': Tarefa.objects.filter(ativa=True, tem_justificativa_ativa=True).count(),
    }
    
    # % de tarefas justificadas
    if stats_gerais['total_tarefas'] > 0:
        stats_gerais['percentual_justificadas'] = round(
            (stats_gerais['tarefas_com_justificativa'] / stats_gerais['total_tarefas']) * 100,
            2
        )
    else:
        stats_gerais['percentual_justificadas'] = 0
    
    # Servidores com mais justificativas
    servidores_ranking = CustomUser.objects.annotate(
        total_justificativas=Count('justificativas_submetidas'),
        justificativas_aprovadas=Count(
            'justificativas_submetidas',
            filter=Q(justificativas_submetidas__status='APROVADA')
        ),
        justificativas_pendentes=Count(
            'justificativas_submetidas',
            filter=Q(justificativas_submetidas__status='PENDENTE')
        ),
        total_tarefas=Count('tarefas_sob_responsabilidade')
    ).filter(
        total_justificativas__gt=0
    ).order_by('-total_justificativas')[:20]
    
    # Calcula % para cada servidor
    for servidor in servidores_ranking:
        if servidor.total_tarefas > 0:
            servidor.percentual = round(
                (servidor.total_justificativas / servidor.total_tarefas) * 100,
                2
            )
        else:
            servidor.percentual = 0
    
    # Distribuição por tipo
    tipos_distribuicao = Justificativa.objects.values(
        'tipo_justificativa__nome'
    ).annotate(
        total=Count('id'),
        aprovadas=Count('id', filter=Q(status='APROVADA')),
        reprovadas=Count('id', filter=Q(status='REPROVADA')),
        pendentes=Count('id', filter=Q(status='PENDENTE'))
    ).order_by('-total')
    
    # Tendência temporal (últimos 30 dias)
    from datetime import timedelta
    data_inicial = timezone.now() - timedelta(days=30)

    justificativas_recentes = Justificativa.objects.filter(
        data_submissao__gte=data_inicial
    ).extra(
        select={'dia': 'DATE(data_submissao)'}
    ).values('dia').annotate(
        total=Count('id')
    ).order_by('dia')
    
    context = {
        'stats_gerais': stats_gerais,
        'servidores_ranking': servidores_ranking,
        'tipos_distribuicao': tipos_distribuicao,
        'justificativas_recentes': justificativas_recentes,
    }
    
    return render(request, 'tarefas/relatorio_justificativas_coordenador.html', context)


@login_required
@user_passes_test(usuario_eh_coordenador)
def relatorio_solicitacoes_coordenador(request):
    """
    Relatório de solicitações de ajuda para o coordenador.
    """
    from django.db.models import Count, Avg, Q
    from datetime import timedelta
    
    # Estatísticas gerais
    stats_gerais = {
        'total': SolicitacaoAjuda.objects.count(),
        'pendentes': SolicitacaoAjuda.objects.filter(status='PENDENTE').count(),
        'em_atendimento': SolicitacaoAjuda.objects.filter(status='EM_ATENDIMENTO').count(),
        'concluidas': SolicitacaoAjuda.objects.filter(status='CONCLUIDA').count(),
    }
    
    # Tempo médio de atendimento (em horas)
    solicitacoes_concluidas = SolicitacaoAjuda.objects.filter(
        status='CONCLUIDA',
        data_atendimento__isnull=False
    )
    
    if solicitacoes_concluidas.exists():
        # Calcula diferença entre criação e conclusão
        tempos = []
        for sol in solicitacoes_concluidas:
            if sol.data_conclusao:
                diff = sol.data_conclusao - sol.data_solicitacao
                tempos.append(diff.total_seconds() / 3600)  # Converte para horas
        
        if tempos:
            stats_gerais['tempo_medio_horas'] = round(sum(tempos) / len(tempos), 1)
        else:
            stats_gerais['tempo_medio_horas'] = 0
    else:
        stats_gerais['tempo_medio_horas'] = 0
    
    # Membros da Equipe Volante e suas estatísticas
    from django.contrib.auth.models import Group
    
    grupo_volante = Group.objects.filter(name='Equipe Volante').first()
    if grupo_volante:
        membros_volante = grupo_volante.user_set.annotate(
            total_atendimentos=Count('solicitacoes_atendidas'),
            concluidos=Count(
                'solicitacoes_atendidas',
                filter=Q(solicitacoes_atendidas__status='CONCLUIDA')
            ),
            em_andamento=Count(
                'solicitacoes_atendidas',
                filter=Q(solicitacoes_atendidas__status='EM_ATENDIMENTO')
            )
        ).filter(total_atendimentos__gt=0).order_by('-total_atendimentos')
    else:
        membros_volante = []
    
    # Tendência temporal
    data_inicial = timezone.now() - timedelta(days=30)
    solicitacoes_recentes = SolicitacaoAjuda.objects.filter(
        data_solicitacao__gte=data_inicial
    ).extra(
        select={'dia': 'DATE(data_solicitacao)'}
    ).values('dia').annotate(
        total=Count('id')
    ).order_by('dia')
    
    context = {
        'stats_gerais': stats_gerais,
        'membros_volante': membros_volante,
        'solicitacoes_recentes': solicitacoes_recentes,
    }
    
    return render(request, 'tarefas/relatorio_solicitacoes_coordenador.html', context)
