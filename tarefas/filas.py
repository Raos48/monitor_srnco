"""
Configurações e metadados das filas de trabalho do sistema.

Define informações como:
- Nome amigável
- Cor do card
- Ícone
- Descrição
- Ordem de exibição
"""

# Ordem de exibição das filas
ORDEM_FILAS = [
    'PGB',
    'CEABRD-23150521',
    'CEAB-BI-23150521',
    'CEAB-RECURSO-23150521',
    'CEAB-DEFESO-23150521',
    'CEAB-COMPREV-23150521',
    'CEAB-MOB-23150521',
    'OUTROS',
]

# Configurações detalhadas de cada fila
FILAS_CONFIG = {
    'PGB': {
        'nome': 'PGB',
        'nome_completo': 'Programa de Gerenciamento de Benefícios',
        'descricao': 'Tarefas da unidade 23150003',
        'cor': '#007bff',  # Azul
        'cor_bootstrap': 'primary',
        'icone': 'fas fa-building',
        'codigo_unidade': 23150003,
    },
    'CEABRD-23150521': {
        'nome': 'CEABRD',
        'nome_completo': 'Central de Análise de Benefícios e Reconhecimento de Direitos',
        'descricao': 'Aposentadorias, Pensões, BPC, Salário-Maternidade, etc.',
        'cor': '#28a745',  # Verde
        'cor_bootstrap': 'success',
        'icone': 'fas fa-user-check',
        'codigo_unidade': 23150521,
    },
    'CEAB-BI-23150521': {
        'nome': 'CEAB-BI',
        'nome_completo': 'Central de Análise de Benefícios por Incapacidade',
        'descricao': 'Auxílio-Doença, Perícias, Acertos Pós-Perícia',
        'cor': '#ffc107',  # Amarelo/Laranja
        'cor_bootstrap': 'warning',
        'icone': 'fas fa-user-injured',
        'codigo_unidade': 23150521,
    },
    'CEAB-RECURSO-23150521': {
        'nome': 'CEAB-RECURSO',
        'nome_completo': 'Central de Análise de Recursos',
        'descricao': 'Recursos, Acórdãos, Cumprimento de Decisões',
        'cor': '#dc3545',  # Vermelho
        'cor_bootstrap': 'danger',
        'icone': 'fas fa-gavel',
        'codigo_unidade': 23150521,
    },
    'CEAB-DEFESO-23150521': {
        'nome': 'CEAB-DEFESO',
        'nome_completo': 'Central de Análise de Seguro Defeso',
        'descricao': 'Seguro Defeso - Pescador Artesanal',
        'cor': '#17a2b8',  # Ciano
        'cor_bootstrap': 'info',
        'icone': 'fas fa-fish',
        'codigo_unidade': 23150521,
    },
    'CEAB-COMPREV-23150521': {
        'nome': 'CEAB-COMPREV',
        'nome_completo': 'Central de Análise de Compensação Previdenciária',
        'descricao': 'COMPREV-RI, COMPREV-RO, Certidão de Tempo de Contribuição',
        'cor': '#6f42c1',  # Roxo
        'cor_bootstrap': 'purple',
        'icone': 'fas fa-exchange-alt',
        'codigo_unidade': 23150521,
    },
    'CEAB-MOB-23150521': {
        'nome': 'CEAB-MOB',
        'nome_completo': 'Central de Análise de Apuração de Irregularidades (MOB)',
        'descricao': 'Apuração de Irregularidades, Força Tarefa',
        'cor': '#fd7e14',  # Laranja escuro
        'cor_bootstrap': 'orange',
        'icone': 'fas fa-search',
        'codigo_unidade': 23150521,
    },
    'OUTROS': {
        'nome': 'OUTROS',
        'nome_completo': 'Outras Tarefas',
        'descricao': 'Tarefas que não se encaixam nas categorias acima',
        'cor': '#6c757d',  # Cinza
        'cor_bootstrap': 'secondary',
        'icone': 'fas fa-ellipsis-h',
        'codigo_unidade': None,
    },
}


def obter_info_fila(codigo_fila):
    """
    Retorna as informações configuradas de uma fila.

    Args:
        codigo_fila (str): Código da fila (ex: 'PGB', 'CEABRD-23150521')

    Returns:
        dict: Dicionário com as informações da fila ou configuração padrão se não encontrada
    """
    return FILAS_CONFIG.get(codigo_fila, {
        'nome': codigo_fila,
        'nome_completo': codigo_fila,
        'descricao': 'Fila não configurada',
        'cor': '#6c757d',
        'cor_bootstrap': 'secondary',
        'icone': 'fas fa-question',
        'codigo_unidade': None,
    })


def obter_filas_ordenadas():
    """
    Retorna a lista de códigos de filas na ordem de exibição definida.

    Returns:
        list: Lista de códigos de filas ordenada
    """
    return ORDEM_FILAS


def obter_nome_amigavel(codigo_fila):
    """
    Retorna o nome amigável (curto) de uma fila.

    Args:
        codigo_fila (str): Código da fila

    Returns:
        str: Nome amigável da fila
    """
    info = obter_info_fila(codigo_fila)
    return info['nome']


def obter_cor_fila(codigo_fila):
    """
    Retorna a cor hexadecimal de uma fila.

    Args:
        codigo_fila (str): Código da fila

    Returns:
        str: Cor em formato hexadecimal
    """
    info = obter_info_fila(codigo_fila)
    return info['cor']


def obter_classe_bootstrap(codigo_fila):
    """
    Retorna a classe Bootstrap correspondente à cor da fila.

    Args:
        codigo_fila (str): Código da fila

    Returns:
        str: Nome da classe Bootstrap (ex: 'primary', 'success')
    """
    info = obter_info_fila(codigo_fila)
    return info['cor_bootstrap']
