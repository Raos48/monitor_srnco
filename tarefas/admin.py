from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Q
from .models import Tarefa, NotificacaoEmail
from .parametros_admin import ParametrosAnaliseAdmin, HistoricoAlteracaoPrazosAdmin


@admin.register(Tarefa)
class TarefaAdmin(admin.ModelAdmin):
    """
    Administração completa para o modelo Tarefa.
    Permite visualizar, filtrar e gerenciar todas as tarefas.
    """
    
    # Campos exibidos na listagem (INCLUINDO NOVOS CAMPOS)
    list_display = (
        'numero_protocolo_tarefa',
        'nome_servico',
        'status_badge',
        'alerta_badge',
        'prazo_badge',  # ← NOVO: Exibe o prazo
        'reaberta_badge',  # ← NOVO: Indica se foi reaberta
        'nome_profissional_responsavel',
        'siape_responsavel',
        'gex_responsavel',
        'dias_com_servidor_display',
        'data_distribuicao_tarefa',
        'tem_subtarefa'
    )
    
    # Campos clicáveis
    list_display_links = ('numero_protocolo_tarefa', 'nome_servico')
    
    # Filtros laterais (INCLUINDO NOVOS CAMPOS)
    list_filter = (
        'status_tarefa',
        'descricao_cumprimento_exigencia_tarefa',
        'nome_gex_responsavel',
        'indicador_subtarefas_pendentes',
        'indicador_tarefa_reaberta',  # ← NOVO FILTRO
        'data_distribuicao_tarefa',
        'data_ultima_atualizacao',
        'data_prazo',  # ← NOVO FILTRO
        'data_inicio_ultima_exigencia',  # ← NOVO FILTRO
    )
    
    # Campos de busca
    search_fields = (
        'numero_protocolo_tarefa',
        'nome_servico',
        'nome_profissional_responsavel',
        'siape_responsavel__siape',
        'cpf_responsavel',
        'codigo_gex_responsavel',
        'nome_gex_responsavel'
    )
    
    # Ordenação padrão
    ordering = ('-data_distribuicao_tarefa',)
    
    # Paginação
    list_per_page = 50
    
    # Campos somente leitura
    readonly_fields = (
        'numero_protocolo_tarefa',
        'data_processamento_tarefa',
        'dias_com_servidor_display',
        'dias_ate_prazo_display',  # ← NOVO
        'get_tipo_alerta',
        'get_descricao_alerta'
    )
    
    # Organização dos campos no formulário (INCLUINDO NOVOS CAMPOS)
    fieldsets = (
        ('Identificação da Tarefa', {
            'fields': (
                'numero_protocolo_tarefa',
                'codigo_unidade_tarefa',
                'nome_servico',
                'indicador_subtarefas_pendentes',
                'indicador_tarefa_reaberta'  # ← NOVO CAMPO
            )
        }),
        ('Status e Exigências', {
            'fields': (
                'status_tarefa',
                'descricao_cumprimento_exigencia_tarefa',
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
            )
        }),
        ('Tempos (em dias)', {
            'fields': (
                'tempo_ultima_exigencia_em_dias',
                'tempo_em_pendencia_em_dias',
                'tempo_em_exigencia_em_dias',
                'tempo_ate_ultima_distribuicao_tarefa_em_dias',
                'dias_com_servidor_display',
                'dias_ate_prazo_display'  # ← NOVO CAMPO
            )
        }),
        ('Alertas', {
            'fields': (
                'get_tipo_alerta',
                'get_descricao_alerta'
            ),
            'classes': ('collapse',)
        })
    )
    
    # Ações em massa
    actions = ['exportar_tarefas_com_alerta', 'exportar_tarefas_com_prazo_vencido']
    
    def status_badge(self, obj):
        """Exibe o status com cores"""
        cores = {
            'Pendente': 'orange',
            'Cumprimento de exigência': 'blue',
            'Concluído': 'green',
            'Cancelado': 'red'
        }
        cor = cores.get(obj.status_tarefa, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            cor,
            obj.status_tarefa
        )
    status_badge.short_description = 'Status'
    
    def alerta_badge(self, obj):
        """Exibe badge de alerta se houver"""
        if not obj.tem_alerta:
            return format_html('<span style="color: green;">✓ OK</span>')
        
        cores_alerta = {
            'PENDENTE_SEM_MOVIMENTACAO': '#ff9800',  # Laranja
            'EXIGENCIA_VENCIDA': '#f44336',  # Vermelho
            'EXIGENCIA_CUMPRIDA_PENDENTE': '#2196f3'  # Azul
        }
        
        tipo = obj.tipo_alerta
        cor = cores_alerta.get(tipo, 'gray')
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">⚠ ALERTA</span>',
            cor
        )
    alerta_badge.short_description = 'Situação'
    
    def prazo_badge(self, obj):
        """← NOVO: Exibe badge do prazo com cores baseadas na proximidade"""
        if not obj.data_prazo:
            return format_html('<span style="color: gray;">-</span>')
        
        dias = obj.dias_ate_prazo
        
        if dias is None:
            return '-'
        
        if dias < 0:
            # Prazo vencido
            return format_html(
                '<span style="background-color: #f44336; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">🔴 Vencido há {} dias</span>',
                abs(dias)
            )
        elif dias == 0:
            return format_html(
                '<span style="background-color: #ff9800; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">⚠️ HOJE</span>'
            )
        elif dias <= 7:
            # Prazo próximo (urgente)
            return format_html(
                '<span style="background-color: #ff9800; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">⚠️ {} dias</span>',
                dias
            )
        elif dias <= 15:
            # Prazo próximo (atenção)
            return format_html(
                '<span style="background-color: #ffc107; color: black; padding: 3px 8px; border-radius: 3px; font-weight: bold;">⏰ {} dias</span>',
                dias
            )
        else:
            # Prazo OK
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ {} dias</span>',
                dias
            )
    prazo_badge.short_description = 'Prazo'
    
    def reaberta_badge(self, obj):
        """← NOVO: Indica se a tarefa foi reaberta"""
        if obj.foi_reaberta:
            return format_html(
                '<span style="background-color: #9c27b0; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">🔄 REABERTA</span>'
            )
        return format_html('<span style="color: gray;">-</span>')
    reaberta_badge.short_description = 'Reaberta?'
    
    def tem_subtarefa(self, obj):
        """Indica se tem subtarefa pendente"""
        if obj.indicador_subtarefas_pendentes > 0:
            return format_html('<span style="color: orange;">⚠ Sim</span>')
        return format_html('<span style="color: green;">✓ Não</span>')
    tem_subtarefa.short_description = 'Subtarefa?'
    
    def gex_responsavel(self, obj):
        """Exibe a GEX de forma resumida"""
        if obj.nome_gex_responsavel:
            # Pega apenas as primeiras palavras
            nome_curto = ' '.join(obj.nome_gex_responsavel.split()[:3])
            return nome_curto
        return '-'
    gex_responsavel.short_description = 'GEX'
    
    def dias_com_servidor_display(self, obj):
        """Exibe os dias com o servidor com formatação"""
        dias = obj.dias_com_servidor
        if dias > 30:
            cor = 'red'
        elif dias > 10:
            cor = 'orange'
        else:
            cor = 'green'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} dias</span>',
            cor,
            dias
        )
    dias_com_servidor_display.short_description = 'Dias c/ Servidor'
    
    def dias_ate_prazo_display(self, obj):
        """← NOVO: Exibe dias até o prazo de forma legível"""
        dias = obj.dias_ate_prazo
        if dias is None:
            return 'Sem prazo definido'
        
        if dias < 0:
            return format_html(
                '<span style="color: red; font-weight: bold;">Vencido há {} dias</span>',
                abs(dias)
            )
        elif dias == 0:
            return format_html(
                '<span style="color: orange; font-weight: bold;">Vence HOJE</span>'
            )
        else:
            return format_html(
                '<span style="color: green;">Faltam {} dias</span>',
                dias
            )
    dias_ate_prazo_display.short_description = 'Dias até o Prazo'
    
    def get_tipo_alerta(self, obj):
        """Retorna o tipo de alerta para exibição"""
        return obj.tipo_alerta or 'Sem alerta'
    get_tipo_alerta.short_description = 'Tipo de Alerta'
    
    def get_descricao_alerta(self, obj):
        """Retorna a descrição do alerta"""
        return obj.descricao_alerta or 'Nenhum alerta ativo'
    get_descricao_alerta.short_description = 'Descrição do Alerta'
    
    @admin.action(description='Exportar tarefas com alerta para CSV')
    def exportar_tarefas_com_alerta(self, request, queryset):
        """Exporta apenas tarefas com alerta"""
        import csv
        from django.http import HttpResponse
        
        tarefas_com_alerta = [t for t in queryset if t.tem_alerta]
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="tarefas_com_alerta.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Protocolo', 'Serviço', 'Status', 'Responsável', 'SIAPE',
            'Tipo de Alerta', 'Descrição', 'Dias com Servidor', 'Prazo', 'Reaberta'
        ])
        
        for tarefa in tarefas_com_alerta:
            writer.writerow([
                tarefa.numero_protocolo_tarefa,
                tarefa.nome_servico,
                tarefa.status_tarefa,
                tarefa.nome_profissional_responsavel,
                tarefa.siape_responsavel.siape if tarefa.siape_responsavel else '',
                tarefa.tipo_alerta,
                tarefa.descricao_alerta,
                tarefa.dias_com_servidor,
                tarefa.data_prazo.strftime('%d/%m/%Y') if tarefa.data_prazo else 'Sem prazo',
                'Sim' if tarefa.foi_reaberta else 'Não'
            ])
        
        self.message_user(request, f'{len(tarefas_com_alerta)} tarefas com alerta exportadas.')
        return response
    
    @admin.action(description='Exportar tarefas com prazo vencido para CSV')
    def exportar_tarefas_com_prazo_vencido(self, request, queryset):
        """← NOVA AÇÃO: Exporta apenas tarefas com prazo vencido"""
        import csv
        from django.http import HttpResponse
        
        tarefas_prazo_vencido = [t for t in queryset if t.prazo_vencido]
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="tarefas_prazo_vencido.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Protocolo', 'Serviço', 'Status', 'Responsável', 'SIAPE',
            'Data do Prazo', 'Dias de Atraso', 'Reaberta'
        ])
        
        for tarefa in tarefas_prazo_vencido:
            writer.writerow([
                tarefa.numero_protocolo_tarefa,
                tarefa.nome_servico,
                tarefa.status_tarefa,
                tarefa.nome_profissional_responsavel,
                tarefa.siape_responsavel.siape if tarefa.siape_responsavel else '',
                tarefa.data_prazo.strftime('%d/%m/%Y') if tarefa.data_prazo else '',
                abs(tarefa.dias_ate_prazo) if tarefa.dias_ate_prazo else 0,
                'Sim' if tarefa.foi_reaberta else 'Não'
            ])
        
        self.message_user(request, f'{len(tarefas_prazo_vencido)} tarefas com prazo vencido exportadas.')
        return response


@admin.register(NotificacaoEmail)
class NotificacaoEmailAdmin(admin.ModelAdmin):
    """
    Administração para NotificacaoEmail.
    Gerencia o histórico de e-mails enviados.
    """
    
    # Campos exibidos na listagem
    list_display = (
        'id',
        'tipo',
        'assunto',
        'destinatario',
        'enviado_em',
        'status_badge'
    )
    
    # Campos clicáveis
    list_display_links = ('id', 'assunto')
    
    # Filtros laterais
    list_filter = (
        'tipo',
        'sucesso',
        'enviado_em'
    )
    
    # Campos de busca
    search_fields = (
        'assunto',
        'destinatario__nome_completo',
        'destinatario__email',
        'mensagem'
    )
    
    # Ordenação padrão
    ordering = ('-enviado_em',)
    
    # Paginação
    list_per_page = 50
    
    # Campos somente leitura
    readonly_fields = ('enviado_em',)
    
    # Organização dos campos
    fieldsets = (
        ('Informações do E-mail', {
            'fields': ('tipo', 'assunto', 'mensagem')
        }),
        ('Remetente e Destinatário', {
            'fields': ('remetente', 'destinatario')
        }),
        ('Status', {
            'fields': ('sucesso', 'erro', 'enviado_em')
        })
    )
    
    def status_badge(self, obj):
        """Exibe badge de sucesso/erro"""
        if obj.sucesso:
            return format_html(
                '<span style="background-color: green; color: white; padding: 3px 10px; border-radius: 3px;">✓ Enviado</span>'
            )
        return format_html(
            '<span style="background-color: red; color: white; padding: 3px 10px; border-radius: 3px;">✗ Erro</span>'
        )
    status_badge.short_description = 'Status'
    
