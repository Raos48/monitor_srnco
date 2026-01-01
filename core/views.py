from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import View, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models
from django.db.models import Avg, Count
from datetime import date

from tarefas.models import Tarefa
from usuarios.models import CustomUser


def teste_visual(request):
    return render(request, 'teste_visual.html')


class DashboardView(LoginRequiredMixin, View):
    """
    View que redireciona usuários para seus dashboards apropriados.
    Esta view centraliza o roteamento inicial após login.
    """
    def get(self, request, *args, **kwargs):
        user = request.user

        # 1. COORDENADOR → Dashboard do Coordenador em tarefas
        if user.groups.filter(name='Coordenador').exists():
            return redirect('tarefas:dashboard_coordenador')

        # 2. EQUIPE VOLANTE → Painel da Equipe Volante
        elif user.groups.filter(name='Equipe Volante').exists():
            return redirect('tarefas:painel_equipe_volante')

        # 3. SERVIDOR → Dashboard do Servidor em tarefas
        elif user.groups.filter(name='Servidor').exists():
            return redirect('tarefas:dashboard_servidor')

        # 4. OUTROS (Admin, etc) → Página inicial do app tarefas
        else:
            return redirect('tarefas:redirect_after_login')


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


@login_required
def logout_view(request):
    """
    Desloga o usuário e o redireciona para a página de login.
    Adiciona mensagem de sucesso para feedback visual.
    """
    usuario_nome = request.user.nome_completo if hasattr(request.user, 'nome_completo') else request.user.username
    logout(request)
    messages.success(request, f'Você saiu do sistema com sucesso. Até logo, {usuario_nome}!')
    return redirect('login')