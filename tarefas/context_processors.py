from datetime import datetime, timedelta
from django.utils import timezone


def group_permissions(request):
    """
    Adiciona variáveis de permissão ao contexto do template
    baseadas nos grupos do usuário.

    OTIMIZAÇÃO: Cache dos grupos do usuário para evitar queries repetidas
    """
    user = request.user

    if not user.is_authenticated:
        return {}

    # OTIMIZAÇÃO: Buscar todos os grupos de uma vez e cachear
    # Usar hasattr para verificar se já foi cacheado nesta requisição
    if not hasattr(user, '_cached_groups'):
        user._cached_groups = set(user.groups.values_list('name', flat=True))

    groups = user._cached_groups

    # Determinar perfil do usuário usando o cache
    perfil = None
    if user.is_staff or user.is_superuser:
        perfil = 'COORDENADOR'
    elif 'Coordenador' in groups:
        perfil = 'COORDENADOR'
    elif 'Equipe Volante' in groups:
        perfil = 'EQUIPE_VOLANTE'
    elif 'Servidor' in groups:
        perfil = 'SERVIDOR'

    # Adicionar perfil como propriedade do usuário para acesso nos templates
    user.perfil = perfil

    return {
        'is_coordenador': 'Coordenador' in groups or user.is_staff,
        'is_servidor': 'Servidor' in groups,
        'is_equipe_volante': 'Equipe Volante' in groups,
    }


def data_processamento_context(request):
    """
    Adiciona informações sobre a data de processamento dos dados
    ao contexto do template.

    OTIMIZAÇÃO: Cache de 5 minutos para evitar query pesada em toda requisição
    """
    from django.core.cache import cache
    from tarefas.models import Tarefa

    # OTIMIZAÇÃO: Tentar obter do cache primeiro (5 minutos)
    cache_key = 'data_processamento_info'
    cached_data = cache.get(cache_key)

    if cached_data is not None:
        return cached_data

    # Buscar a data de processamento mais recente (query apenas se não houver cache)
    # OTIMIZAÇÃO: Usar values_list para buscar apenas o campo necessário
    data_processamento = Tarefa.objects.filter(
        data_processamento_tarefa__isnull=False
    ).values_list('data_processamento_tarefa', flat=True).order_by('-data_processamento_tarefa').first()

    if not data_processamento:
        result = {
            'data_processamento': None,
            'cor_status_processamento': 'secondary',
            'dados_atualizados': False
        }
        # Cachear por 5 minutos
        cache.set(cache_key, result, 300)
        return result

    # Calcular se está dentro do prazo (3 dias)
    hoje = timezone.now()
    diferenca_dias = (hoje.date() - data_processamento.date()).days

    # Definir cor: verde se <= 3 dias, amarelo se > 3 dias
    cor_status = 'success' if diferenca_dias <= 3 else 'warning'

    result = {
        'data_processamento': data_processamento,
        'cor_status_processamento': cor_status,
        'dados_atualizados': True
    }

    # OTIMIZAÇÃO: Cachear resultado por 5 minutos (300 segundos)
    cache.set(cache_key, result, 300)

    return result