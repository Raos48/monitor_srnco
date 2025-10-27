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
    ATUALIZADO: Incluindo campos de criticidade calculada.
    """
    
    # ============================================
    # CONFIGURAÇÃO DA LISTAGEM
    # ============================================
    
    list_display = (
        'numero_protocolo_tarefa',
        'nome_servico',
        'status_badge',
        'criticidade_badge',  # ← NOVO: Badge de criticidade calculada
        'alerta_badge',
        'prazo_badge',
        'reaberta_badge',
        'nome_profissional_responsavel',
        'siape_responsavel',
        'gex_responsavel',
        'dias_com_servidor_display',
        'data_distribuicao_tarefa',
        'tem_subtarefa'
    )
    
    list_display_links = ('numero_protocolo_tarefa', 'nome_servico')
    
    # ============================================
    # FILTROS LATERAIS - INCLUINDO CRITICIDADE
    # ============================================
    
    list_filter = (
        'status_tarefa',
        'descricao_cumprimento_exigencia_tarefa',
        'nivel_criticidade_calculado',  # ← NOVO FILTRO
        'regra_aplicada_calculado',     # ← NOVO FILTRO
        'nome_gex_responsavel',
        'indicador_subtarefas_pendentes',
        'indicador_tarefa_reaberta',
        'data_distribuicao_tarefa',
        'data_ultima_atualizacao',
        'data_prazo',
        'data_inicio_ultima_exigencia',
        'data_calculo_criticidade',  # ← NOVO FILTRO
    )
    
    # ============================================
    # CAMPOS DE BUSCA
    # ============================================
    
    search_fields = (
        'numero_protocolo_tarefa',
        'nome_servico',
        'nome_profissional_responsavel',
        'siape_responsavel__siape',
        'cpf_responsavel',
        'codigo_gex_responsavel',
        'nome_gex_responsavel'
    )
    
    # ============================================
    # ORDENAÇÃO E PAGINAÇÃO
    # ============================================
    
    ordering = ('-pontuacao_criticidade', '-data_distribuicao_tarefa')  # ← ATUALIZADO: Ordena por criticidade primeiro
    list_per_page = 50
    
    # ============================================
    # CAMPOS SOMENTE LEITURA
    # ============================================
    
    readonly_fields = (
        'numero_protocolo_tarefa',
        'data_processamento_tarefa',
        'dias_com_servidor_display',
        'dias_ate_prazo_display',
        'get_tipo_alerta',
        'get_descricao_alerta',
        # ← NOVOS CAMPOS DE CRITICIDADE
        'nivel_criticidade_calculado',
        'regra_aplicada_calculado',
        'alerta_criticidade_calculado',
        'descricao_criticidade_calculado',
        'dias_pendente_criticidade_calculado',
        'prazo_limite_criticidade_calculado',
        'pontuacao_criticidade',
        'cor_criticidade_calculado',
        'data_calculo_criticidade',
        'resumo_criticidade_visual',  # ← NOVO: Resumo visual da criticidade
    )
    
    # ============================================
    # ORGANIZAÇÃO DOS CAMPOS NO FORMULÁRIO
    # ============================================
    
    fieldsets = (
        ('🆔 Identificação da Tarefa', {
            'fields': (
                'numero_protocolo_tarefa',
                'codigo_unidade_tarefa',
                'nome_servico',
                'indicador_subtarefas_pendentes',
                'indicador_tarefa_reaberta'
            )
        }),
        ('📊 Status e Exigências', {
            'fields': (
                'status_tarefa',
                'descricao_cumprimento_exigencia_tarefa',
            )
        }),
        ('👤 Responsável', {
            'fields': (
                'siape_responsavel',
                'cpf_responsavel',
                'nome_profissional_responsavel',
                'codigo_gex_responsavel',
                'nome_gex_responsavel'
            )
        }),
        ('📅 Datas', {
            'fields': (
                'data_distribuicao_tarefa',
                'data_ultima_atualizacao',
                'data_prazo',
                'data_inicio_ultima_exigencia',
                'data_fim_ultima_exigencia',
                'data_processamento_tarefa'
            )
        }),
        ('⏱️ Tempos (em dias)', {
            'fields': (
                'tempo_ultima_exigencia_em_dias',
                'tempo_em_pendencia_em_dias',
                'tempo_em_exigencia_em_dias',
                'tempo_ate_ultima_distribuicao_tarefa_em_dias',
                'dias_com_servidor_display',
                'dias_ate_prazo_display'
            )
        }),
        ('⚠️ Alertas (Sistema Antigo)', {
            'fields': (
                'get_tipo_alerta',
                'get_descricao_alerta'
            ),
            'classes': ('collapse',)
        }),
        ('🎯 CRITICIDADE CALCULADA (Sistema Otimizado)', {
            'fields': (
                'resumo_criticidade_visual',
                'nivel_criticidade_calculado',
                'regra_aplicada_calculado',
                'pontuacao_criticidade',
                'alerta_criticidade_calculado',
                'descricao_criticidade_calculado',
                'dias_pendente_criticidade_calculado',
                'prazo_limite_criticidade_calculado',
                'cor_criticidade_calculado',
                'data_calculo_criticidade',
            ),
            'description': '✅ Valores pré-calculados para melhor performance. '
                          'Atualizados automaticamente durante importação de CSV.'
        })
    )
    
    # ============================================
    # AÇÕES EM MASSA
    # ============================================
    
    actions = [
        'exportar_tarefas_com_alerta',
        'exportar_tarefas_com_prazo_vencido',
        'exportar_tarefas_criticas',  # ← NOVA AÇÃO
        'recalcular_criticidade_selecionadas',  # ← NOVA AÇÃO
    ]
    
    # ============================================
    # MÉTODOS DE EXIBIÇÃO - BADGES E FORMATAÇÃO
    # ============================================
    
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
    
    def criticidade_badge(self, obj):
        """← NOVO: Exibe badge de criticidade calculada"""
        if obj.nivel_criticidade_calculado == 'NENHUMA':
            return format_html('<span style="color: gray;">⚪ Normal</span>')
        
        # Mapear cores e emojis
        config_badge = {
            'CRÍTICA': {'cor': '#dc3545', 'emoji': '🔴'},
            'ALTA': {'cor': '#fd7e14', 'emoji': '🟠'},
            'MÉDIA': {'cor': '#ffc107', 'emoji': '🟡'},
            'BAIXA': {'cor': '#28a745', 'emoji': '🟢'},
        }
        
        config = config_badge.get(obj.nivel_criticidade_calculado, {'cor': 'gray', 'emoji': '⚪'})
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 12px; '
            'border-radius: 3px; font-weight: bold; font-size: 12px;">{} {}</span>',
            config['cor'],
            config['emoji'],
            obj.nivel_criticidade_calculado
        )
    criticidade_badge.short_description = 'Criticidade'
    criticidade_badge.admin_order_field = 'pontuacao_criticidade'
    
    def alerta_badge(self, obj):
        """Exibe badge de alerta se houver"""
        if not obj.tem_alerta:
            return format_html('<span style="color: green;">✓ OK</span>')
        
        cores_alerta = {
            'PENDENTE_SEM_MOVIMENTACAO': '#ff9800',
            'EXIGENCIA_VENCIDA': '#f44336',
            'EXIGENCIA_CUMPRIDA_PENDENTE': '#2196f3'
        }
        
        tipo = obj.tipo_alerta
        cor = cores_alerta.get(tipo, 'gray')
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-weight: bold;">⚠ ALERTA</span>',
            cor
        )
    alerta_badge.short_description = 'Situação'
    
    def prazo_badge(self, obj):
        """Exibe badge do prazo com cores baseadas na proximidade"""
        if not obj.data_prazo:
            return format_html('<span style="color: gray;">-</span>')
        
        dias = obj.dias_ate_prazo
        
        if dias is None:
            return '-'
        
        if dias < 0:
            return format_html(
                '<span style="background-color: #f44336; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-weight: bold;">🔴 Vencido há {} dias</span>',
                abs(dias)
            )
        elif dias == 0:
            return format_html(
                '<span style="background-color: #ff9800; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-weight: bold;">⚠️ HOJE</span>'
            )
        elif dias <= 7:
            return format_html(
                '<span style="background-color: #ff9800; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-weight: bold;">⚠️ {} dias</span>',
                dias
            )
        elif dias <= 15:
            return format_html(
                '<span style="background-color: #ffc107; color: black; padding: 3px 8px; '
                'border-radius: 3px; font-weight: bold;">⏰ {} dias</span>',
                dias
            )
        else:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ {} dias</span>',
                dias
            )
    prazo_badge.short_description = 'Prazo'
    
    def reaberta_badge(self, obj):
        """Indica se a tarefa foi reaberta"""
        if obj.foi_reaberta:
            return format_html(
                '<span style="background-color: #9c27b0; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-weight: bold;">🔄 REABERTA</span>'
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
        """Exibe dias até o prazo de forma legível"""
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
    
    def resumo_criticidade_visual(self, obj):
        """← NOVO: Exibe resumo visual completo da criticidade calculada"""
        if obj.nivel_criticidade_calculado == 'NENHUMA':
            return format_html(
                '<div style="padding: 15px; background-color: #f8f9fa; border-radius: 5px; '
                'border-left: 4px solid #6c757d;">'
                '<h3 style="margin-top: 0;">⚪ Sem Criticidade</h3>'
                '<p>Esta tarefa não possui criticidade detectada.</p>'
                '</div>'
            )
        
        # Cores por nível
        cores = {
            'CRÍTICA': '#dc3545',
            'ALTA': '#fd7e14',
            'MÉDIA': '#ffc107',
            'BAIXA': '#28a745',
        }
        
        cor = cores.get(obj.nivel_criticidade_calculado, '#6c757d')
        
        html = f'''
        <div style="padding: 20px; background-color: {cor}22; border-radius: 8px; 
                    border-left: 6px solid {cor};">
            <h3 style="margin-top: 0; color: {cor};">
                {obj.emoji_criticidade} CRITICIDADE: {obj.nivel_criticidade_calculado}
            </h3>
            
            <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                <tr>
                    <td style="padding: 8px; font-weight: bold; width: 40%;">Regra Aplicada:</td>
                    <td style="padding: 8px;">
                        <span style="background-color: {cor}; color: white; padding: 4px 12px; 
                                     border-radius: 3px; font-weight: bold;">
                            {obj.regra_aplicada_calculado}
                        </span>
                    </td>
                </tr>
                <tr style="background-color: white;">
                    <td style="padding: 8px; font-weight: bold;">Pontuação:</td>
                    <td style="padding: 8px;">
                        <strong style="font-size: 18px; color: {cor};">
                            {obj.pontuacao_criticidade} pontos
                        </strong>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Dias Pendente:</td>
                    <td style="padding: 8px;">
                        <strong>{obj.dias_pendente_criticidade_calculado} dias</strong>
                    </td>
                </tr>
                <tr style="background-color: white;">
                    <td style="padding: 8px; font-weight: bold;">Prazo Limite:</td>
                    <td style="padding: 8px;">
                        <strong>{obj.prazo_limite_criticidade_calculado} dias</strong>
                    </td>
                </tr>
            </table>
            
            <div style="margin-top: 15px; padding: 12px; background-color: white; 
                        border-radius: 4px; border-left: 3px solid {cor};">
                <strong style="color: {cor};">📋 Alerta:</strong><br>
                <span style="margin-top: 5px; display: block;">
                    {obj.alerta_criticidade_calculado}
                </span>
            </div>
            
            <div style="margin-top: 10px; padding: 12px; background-color: white; 
                        border-radius: 4px; border-left: 3px solid {cor};">
                <strong style="color: {cor};">📝 Descrição Detalhada:</strong><br>
                <span style="margin-top: 5px; display: block;">
                    {obj.descricao_criticidade_calculado}
                </span>
            </div>
            
            <div style="margin-top: 15px; padding: 10px; background-color: #e7f3ff; 
                        border-radius: 4px; font-size: 12px;">
                <strong>🕐 Último cálculo:</strong> 
                {obj.data_calculo_criticidade.strftime('%d/%m/%Y às %H:%M:%S') if obj.data_calculo_criticidade else 'Não calculado'}
            </div>
        </div>
        '''
        
        return format_html(html)
    resumo_criticidade_visual.short_description = '🎯 Resumo Visual da Criticidade'
    
    # ============================================
    # AÇÕES EM MASSA
    # ============================================
    
    @admin.action(description='📊 Exportar tarefas com alerta para CSV')
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
            'Tipo de Alerta', 'Descrição', 'Dias com Servidor', 'Prazo', 'Reaberta',
            'Criticidade', 'Pontuação'
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
                'Sim' if tarefa.foi_reaberta else 'Não',
                tarefa.nivel_criticidade_calculado,
                tarefa.pontuacao_criticidade
            ])
        
        self.message_user(request, f'{len(tarefas_com_alerta)} tarefas com alerta exportadas.')
        return response
    
    @admin.action(description='📊 Exportar tarefas com prazo vencido para CSV')
    def exportar_tarefas_com_prazo_vencido(self, request, queryset):
        """Exporta apenas tarefas com prazo vencido"""
        import csv
        from django.http import HttpResponse
        
        tarefas_prazo_vencido = [t for t in queryset if t.prazo_vencido]
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="tarefas_prazo_vencido.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Protocolo', 'Serviço', 'Status', 'Responsável', 'SIAPE',
            'Data do Prazo', 'Dias de Atraso', 'Reaberta', 'Criticidade'
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
                'Sim' if tarefa.foi_reaberta else 'Não',
                tarefa.nivel_criticidade_calculado
            ])
        
        self.message_user(request, f'{len(tarefas_prazo_vencido)} tarefas com prazo vencido exportadas.')
        return response
    
    @admin.action(description='🔴 Exportar tarefas CRÍTICAS para CSV')
    def exportar_tarefas_criticas(self, request, queryset):
        """← NOVA: Exporta apenas tarefas com criticidade CRÍTICA ou ALTA"""
        import csv
        from django.http import HttpResponse
        
        tarefas_criticas = queryset.filter(
            nivel_criticidade_calculado__in=['CRÍTICA', 'ALTA']
        ).order_by('-pontuacao_criticidade')
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="tarefas_criticas.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Protocolo', 'Serviço', 'Status', 'Responsável', 'SIAPE', 'GEX',
            'Criticidade', 'Regra', 'Pontuação', 'Dias Pendente', 'Prazo Limite',
            'Alerta', 'Data Distribuição'
        ])
        
        for tarefa in tarefas_criticas:
            writer.writerow([
                tarefa.numero_protocolo_tarefa,
                tarefa.nome_servico,
                tarefa.status_tarefa,
                tarefa.nome_profissional_responsavel,
                tarefa.siape_responsavel.siape if tarefa.siape_responsavel else '',
                tarefa.nome_gex_responsavel,
                tarefa.nivel_criticidade_calculado,
                tarefa.regra_aplicada_calculado,
                tarefa.pontuacao_criticidade,
                tarefa.dias_pendente_criticidade_calculado,
                tarefa.prazo_limite_criticidade_calculado,
                tarefa.alerta_criticidade_calculado,
                tarefa.data_distribuicao_tarefa.strftime('%d/%m/%Y') if tarefa.data_distribuicao_tarefa else ''
            ])
        
        self.message_user(
            request, 
            f'{tarefas_criticas.count()} tarefas críticas exportadas com sucesso.',
            level='success'
        )
        return response
    
    @admin.action(description='🔄 Recalcular criticidade das tarefas selecionadas')
    def recalcular_criticidade_selecionadas(self, request, queryset):
        """← NOVA: Recalcula a criticidade das tarefas selecionadas"""
        from .analisador import obter_analisador
        
        contador = 0
        analisador = obter_analisador()
        
        for tarefa in queryset:
            tarefa.atualizar_criticidade(analisador)
            contador += 1
        
        self.message_user(
            request,
            f'Criticidade recalculada para {contador} tarefa(s).',
            level='success'
        )


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
        ('📧 Informações do E-mail', {
            'fields': ('tipo', 'assunto', 'mensagem')
        }),
        ('👥 Remetente e Destinatário', {
            'fields': ('remetente', 'destinatario')
        }),
        ('📊 Status', {
            'fields': ('sucesso', 'erro', 'enviado_em')
        })
    )
    
    def status_badge(self, obj):
        """Exibe badge de sucesso/erro"""
        if obj.sucesso:
            return format_html(
                '<span style="background-color: green; color: white; padding: 3px 10px; '
                'border-radius: 3px;">✓ Enviado</span>'
            )
        return format_html(
            '<span style="background-color: red; color: white; padding: 3px 10px; '
            'border-radius: 3px;">✗ Erro</span>'
        )
    status_badge.short_description = 'Status'