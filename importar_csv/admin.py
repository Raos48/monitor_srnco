from django.contrib import admin
from django.utils.html import format_html
from .models import RegistroImportacao, HistoricoTarefa


@admin.register(RegistroImportacao)
class RegistroImportacaoAdmin(admin.ModelAdmin):
    """
    Administração para RegistroImportacao.
    Gerencia o histórico de importações de CSV.
    """
    
    # Campos exibidos na listagem
    list_display = (
        'id',
        'nome_arquivo',
        'usuario',
        'data_importacao',
        'resumo_importacao',
        'total_processado'
    )
    
    # Campos clicáveis
    list_display_links = ('id', 'nome_arquivo')
    
    # Filtros laterais
    list_filter = (
        'data_importacao',
        'usuario'
    )
    
    # Campos de busca
    search_fields = (
        'nome_arquivo',
        'usuario__nome_completo',
        'usuario__email'
    )
    
    # Ordenação padrão
    ordering = ('-data_importacao',)
    
    # Paginação
    list_per_page = 25
    
    # Campos somente leitura
    readonly_fields = (
        'usuario',
        'data_importacao',
        'nome_arquivo',
        'registros_criados',
        'registros_atualizados',
        'usuarios_criados',
        'total_processado'
    )
    
    # Organização dos campos
    fieldsets = (
        ('Informações da Importação', {
            'fields': (
                'nome_arquivo',
                'usuario',
                'data_importacao'
            )
        }),
        ('Estatísticas', {
            'fields': (
                'registros_criados',
                'registros_atualizados',
                'usuarios_criados',
                'total_processado'
            )
        })
    )
    
    def resumo_importacao(self, obj):
        """Exibe resumo visual da importação"""
        return format_html(
            '<div style="line-height: 1.6;">'
            '<span style="color: green; font-weight: bold;">✓ {} criadas</span><br>'
            '<span style="color: blue; font-weight: bold;">↻ {} atualizadas</span><br>'
            '<span style="color: orange; font-weight: bold;">👤 {} usuários</span>'
            '</div>',
            obj.registros_criados,
            obj.registros_atualizados,
            obj.usuarios_criados
        )
    resumo_importacao.short_description = 'Resumo'
    
    def total_processado(self, obj):
        """Calcula total de registros processados"""
        total = obj.registros_criados + obj.registros_atualizados
        return format_html(
            '<span style="background-color: #2196f3; color: white; padding: 5px 15px; border-radius: 3px; font-weight: bold;">{} tarefas</span>',
            total
        )
    total_processado.short_description = 'Total Processado'
    
    def has_add_permission(self, request):
        """Remove o botão de adicionar (importações são feitas via upload)"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Não permite editar registros de importação"""
        return False


@admin.register(HistoricoTarefa)
class HistoricoTarefaAdmin(admin.ModelAdmin):
    """
    Administração para HistoricoTarefa.
    Gerencia o histórico de mudanças nas tarefas.
    ATUALIZADO: Inclui os 3 novos campos.
    """
    
    # Campos exibidos na listagem (INCLUINDO NOVOS CAMPOS)
    list_display = (
        'id',
        'protocolo',
        'data_importacao_display',
        'status_tarefa',
        'prazo_historico',  # ← NOVO
        'reaberta_historico',  # ← NOVO
        'responsavel',
        'gex_abreviada'
    )
    
    # Campos clicáveis
    list_display_links = ('id', 'protocolo')
    
    # Filtros laterais (INCLUINDO NOVOS CAMPOS)
    list_filter = (
        'status_tarefa',
        'registro_importacao__data_importacao',
        'nome_gex_responsavel',
        'indicador_tarefa_reaberta',  # ← NOVO FILTRO
        'data_prazo',  # ← NOVO FILTRO
    )
    
    # Campos de busca
    search_fields = (
        'tarefa_original__numero_protocolo_tarefa',
        'nome_profissional_responsavel',
        'siape_responsavel',
        'cpf_responsavel'
    )
    
    # Ordenação padrão
    ordering = ('-registro_importacao__data_importacao',)
    
    # Paginação
    list_per_page = 50
    
    # Campos somente leitura (histórico não deve ser editado) - INCLUINDO NOVOS CAMPOS
    readonly_fields = (
        'tarefa_original',
        'registro_importacao',
        'status_tarefa',
        'descricao_cumprimento_exigencia_tarefa',
        'siape_responsavel',
        'cpf_responsavel',
        'nome_profissional_responsavel',
        'codigo_gex_responsavel',
        'nome_gex_responsavel',
        'data_distribuicao_tarefa',
        'data_ultima_atualizacao',
        'data_prazo',  # ← NOVO CAMPO
        'data_inicio_ultima_exigencia',  # ← NOVO CAMPO
        'data_fim_ultima_exigencia',
        'indicador_tarefa_reaberta',  # ← NOVO CAMPO
        'data_processamento_tarefa',
        'tempo_ultima_exigencia_em_dias',
        'tempo_em_pendencia_em_dias',
        'tempo_em_exigencia_em_dias',
        'tempo_ate_ultima_distribuicao_tarefa_em_dias'
    )
    
    # Organização dos campos (INCLUINDO NOVOS CAMPOS)
    fieldsets = (
        ('Rastreamento', {
            'fields': (
                'tarefa_original',
                'registro_importacao'
            )
        }),
        ('Status da Tarefa', {
            'fields': (
                'status_tarefa',
                'descricao_cumprimento_exigencia_tarefa',
                'indicador_tarefa_reaberta'  # ← NOVO CAMPO
            )
        }),
        ('Responsável', {
            'fields': (
                'siape_responsavel',
                'cpf_responsavel',
                'nome_profissional_responsavel',
                'codigo_gex_responsavel',
                'nome_gex_responsavel'
            )
        }),
        ('Datas', {
            'fields': (
                'data_distribuicao_tarefa',
                'data_ultima_atualizacao',
                'data_prazo',  # ← NOVO CAMPO
                'data_inicio_ultima_exigencia',  # ← NOVO CAMPO
                'data_fim_ultima_exigencia',
                'data_processamento_tarefa'
            ),
            'classes': ('collapse',)
        }),
        ('Tempos', {
            'fields': (
                'tempo_ultima_exigencia_em_dias',
                'tempo_em_pendencia_em_dias',
                'tempo_em_exigencia_em_dias',
                'tempo_ate_ultima_distribuicao_tarefa_em_dias'
            ),
            'classes': ('collapse',)
        })
    )
    
    def protocolo(self, obj):
        """Exibe o número do protocolo da tarefa"""
        return obj.tarefa_original.numero_protocolo_tarefa
    protocolo.short_description = 'Protocolo'
    protocolo.admin_order_field = 'tarefa_original__numero_protocolo_tarefa'
    
    def data_importacao_display(self, obj):
        """Exibe a data da importação formatada"""
        return obj.registro_importacao.data_importacao.strftime('%d/%m/%Y %H:%M')
    data_importacao_display.short_description = 'Data da Importação'
    data_importacao_display.admin_order_field = 'registro_importacao__data_importacao'
    
    def prazo_historico(self, obj):
        """← NOVO: Exibe o prazo no histórico"""
        if obj.data_prazo:
            return format_html(
                '<span style="color: #2196f3; font-weight: bold;">{}</span>',
                obj.data_prazo.strftime('%d/%m/%Y')
            )
        return format_html('<span style="color: gray;">-</span>')
    prazo_historico.short_description = 'Prazo'
    prazo_historico.admin_order_field = 'data_prazo'
    
    def reaberta_historico(self, obj):
        """← NOVO: Indica se a tarefa estava reaberta neste histórico"""
        if obj.indicador_tarefa_reaberta == 1:
            return format_html(
                '<span style="background-color: #9c27b0; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">🔄 SIM</span>'
            )
        return format_html('<span style="color: gray; font-size: 11px;">Não</span>')
    reaberta_historico.short_description = 'Reaberta'
    reaberta_historico.admin_order_field = 'indicador_tarefa_reaberta'
    
    def responsavel(self, obj):
        """Exibe o nome do responsável de forma resumida"""
        if obj.nome_profissional_responsavel:
            # Pega apenas o primeiro e último nome
            partes = obj.nome_profissional_responsavel.split()
            if len(partes) > 1:
                return f"{partes[0]} {partes[-1]}"
            return partes[0]
        return '-'
    responsavel.short_description = 'Responsável'
    
    def gex_abreviada(self, obj):
        """Exibe a GEX de forma abreviada"""
        if obj.nome_gex_responsavel:
            return ' '.join(obj.nome_gex_responsavel.split()[:3])
        return '-'
    gex_abreviada.short_description = 'GEX'
    
    def has_add_permission(self, request):
        """Remove o botão de adicionar (históricos são criados automaticamente)"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Não permite editar históricos"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Permite deletar apenas para superusuários"""
        return request.user.is_superuser