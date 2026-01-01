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
        'status_badge',          # ← NOVO: Badge de status
        'progresso_display',     # ← NOVO: Progresso visual
        'resumo_importacao',
        'duracao_display',       # ← NOVO: Duração do processamento
        'arquivo_status_display', # ← NOVO: Status do arquivo no disco
        'total_processado'
    )
    
    # Campos clicáveis
    list_display_links = ('id', 'nome_arquivo')
    
    # Filtros laterais
    list_filter = (
        'status',               # ← NOVO: Filtrar por status
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
        'caminho_arquivo',                  # ← NOVO: Caminho completo
        'status',
        'total_linhas',
        'linhas_processadas',
        'progresso_percentual',
        'data_inicio_processamento',
        'data_fim_processamento',
        'mensagem_erro',
        'registros_criados',
        'registros_atualizados',
        'usuarios_criados',
        'total_processado',
        'duracao_display',
        'arquivo_info_display'              # ← NOVO: Informações do arquivo
    )
    
    # Organização dos campos
    fieldsets = (
        ('📁 Informações da Importação', {
            'fields': (
                'nome_arquivo',
                'usuario',
                'data_importacao'
            )
        }),
        ('⚙️ Status e Progresso', {
            'fields': (
                'status',
                'total_linhas',
                'linhas_processadas',
                'progresso_percentual'
            )
        }),
        ('📊 Estatísticas', {
            'fields': (
                'registros_criados',
                'registros_atualizados',
                'usuarios_criados',
                'total_processado'
            )
        }),
        ('⏱️ Tempos', {
            'fields': (
                'data_inicio_processamento',
                'data_fim_processamento',
                'duracao_display'
            )
        }),
        ('❌ Erros', {
            'fields': (
                'mensagem_erro',
            ),
            'classes': ('collapse',)
        }),
        ('📂 Arquivo no Disco', {
            'fields': (
                'caminho_arquivo',
                'arquivo_info_display'
            ),
            'description': 'Informações sobre o arquivo CSV no disco. Use a ação "Deletar arquivo do disco" para remover arquivos desnecessários.'
        })
    )

    # Ações personalizadas
    actions = ['deletar_arquivos_do_disco']
    
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

    def status_badge(self, obj):
        """← NOVO: Exibe badge colorido do status"""
        cores = {
            'PENDING': '#ffc107',
            'PROCESSING': '#2196f3',
            'COMPLETED': '#28a745',
            'FAILED': '#dc3545',
        }
        cor = cores.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            cor,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'

    def progresso_display(self, obj):
        """← NOVO: Exibe barra de progresso visual"""
        progresso = float(obj.progresso_percentual)

        if obj.status == 'COMPLETED':
            cor = '#28a745'
        elif obj.status == 'FAILED':
            cor = '#dc3545'
        elif obj.status == 'PROCESSING':
            cor = '#2196f3'
        else:
            cor = '#ffc107'

        return format_html(
            '<div style="width: 100px;">'
            '<div style="background-color: #e9ecef; border-radius: 3px; overflow: hidden;">'
            '<div style="background-color: {}; width: {}%; height: 20px; text-align: center; '
            'color: white; font-size: 11px; line-height: 20px; font-weight: bold;">'
            '{}%'
            '</div>'
            '</div>'
            '</div>',
            cor, progresso, int(progresso)
        )
    progresso_display.short_description = 'Progresso'
    progresso_display.admin_order_field = 'progresso_percentual'

    def duracao_display(self, obj):
        """← NOVO: Exibe a duração do processamento formatada"""
        duracao = obj.duracao_processamento()

        if duracao is None:
            if obj.status == 'PROCESSING':
                return format_html('<span style="color: #2196f3;">⏳ Em andamento...</span>')
            return format_html('<span style="color: gray;">-</span>')

        # Converter para minutos e segundos
        minutos = int(duracao // 60)
        segundos = int(duracao % 60)

        if minutos > 0:
            texto = f"{minutos}m {segundos}s"
        else:
            texto = f"{segundos}s"

        return format_html(
            '<span style="color: #28a745; font-weight: bold;">⏱️ {}</span>',
            texto
        )
    duracao_display.short_description = 'Duração'

    def arquivo_status_display(self, obj):
        """← NOVO: Mostra status do arquivo no disco"""
        if obj.arquivo_existe():
            tamanho = obj.tamanho_arquivo_mb()
            tamanho_formatado = f"{tamanho:.2f}"
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">✓ Disponível</span><br>'
                '<span style="font-size: 11px; color: #6c757d;">{} MB</span>',
                tamanho_formatado
            )
        return format_html('<span style="color: #dc3545;">✗ Não encontrado</span>')
    arquivo_status_display.short_description = 'Arquivo'

    def arquivo_info_display(self, obj):
        """← NOVO: Mostra informações detalhadas do arquivo"""
        if obj.arquivo_existe():
            tamanho = obj.tamanho_arquivo_mb()
            tamanho_formatado = f"{tamanho:.2f}"
            return format_html(
                '<div style="padding: 15px; background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 5px;">'
                '<h4 style="color: #155724; margin-top: 0;">✓ Arquivo Disponível no Disco</h4>'
                '<table style="width: 100%; margin-top: 10px;">'
                '<tr><td style="font-weight: bold; width: 120px;">Tamanho:</td><td>{} MB</td></tr>'
                '<tr><td style="font-weight: bold;">Caminho:</td><td style="font-family: monospace; font-size: 11px;">{}</td></tr>'
                '</table>'
                '<p style="margin-top: 15px; color: #856404; background-color: #fff3cd; padding: 10px; border-radius: 3px;">'
                '💡 <strong>Dica:</strong> Para liberar espaço em disco, selecione um ou mais registros na lista e '
                'use a ação "Deletar arquivo do disco".'
                '</p>'
                '</div>',
                tamanho_formatado, obj.caminho_arquivo
            )
        return format_html(
            '<div style="padding: 15px; background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 5px;">'
            '<h4 style="color: #721c24; margin-top: 0;">✗ Arquivo Não Encontrado</h4>'
            '<p style="margin-bottom: 0;">O arquivo foi removido ou movido do caminho original.</p>'
            '</div>'
        )
    arquivo_info_display.short_description = 'Informações do Arquivo'

    @admin.action(description='🗑️ Deletar arquivo do disco (mantém registro no banco)')
    def deletar_arquivos_do_disco(self, request, queryset):
        """Deleta os arquivos CSV do disco mantendo os registros no banco"""
        deletados = 0
        erros = []
        nao_encontrados = 0

        for registro in queryset:
            if not registro.arquivo_existe():
                nao_encontrados += 1
                continue

            sucesso, mensagem = registro.deletar_arquivo()
            if sucesso:
                deletados += 1
            else:
                erros.append(f"ID {registro.id}: {mensagem}")

        # Mensagens de feedback
        if deletados > 0:
            self.message_user(
                request,
                f'✓ {deletados} arquivo(s) deletado(s) com sucesso do disco.',
                level='success'
            )

        if nao_encontrados > 0:
            self.message_user(
                request,
                f'ℹ️ {nao_encontrados} arquivo(s) já não existiam no disco.',
                level='warning'
            )

        if erros:
            self.message_user(
                request,
                f'✗ Erros ao deletar {len(erros)} arquivo(s): {"; ".join(erros)}',
                level='error'
            )

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