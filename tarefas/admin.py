from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Q
from django import forms
from .models import (
    Tarefa, NotificacaoEmail, TipoJustificativa,
    Justificativa, SolicitacaoAjuda, ServicosCriticidade,
    Fila, ConfiguracaoFila,
    BloqueioServidor, SolicitacaoNotificacao,
    HistoricoBloqueio, HistoricoNotificacao,
    HistoricoEmail, TemplateEmail, HistoricoAcaoLote
)
from .parametros import ParametrosAnalise, HistoricoAlteracaoPrazos
from .parametros_admin import ParametrosAnaliseAdmin, HistoricoAlteracaoPrazosAdmin

# NOTA: Os 'admin.site.register' foram removidos daqui
# pois já estão sendo registrados dentro de 'parametros_admin.py'

# ============================================
# ADMINISTRAÇÃO DO MODEL TAREFA
# ============================================

@admin.register(Tarefa)
class TarefaAdmin(admin.ModelAdmin):
    """
    Administração completa para o modelo Tarefa.
    """
    
    # ============================================
    # CONFIGURAÇÃO DA LISTAGEM
    # ============================================
    
    list_display = (
        'numero_protocolo_tarefa',
        'nome_servico',
        'tipo_fila',          # ← NOVO: Mostra a fila de trabalho
        'status_badge',
        'criticidade_badge',  # ← USA A PROPRIEDADE DO MODEL
        'regra_badge',        # ← NOVO: Mostra a regra aplicada
        'justificativa_badge', # ← NOVO: Mostra status de justificativa
        'prazo_badge',
        'reaberta_badge',
        'ativa_badge',        # ← NOVO: Mostra se está ativa ou arquivada
        'nome_profissional_responsavel',
        'siape_responsavel',
        'gex_responsavel',
        'dias_com_servidor_display',
    )
    
    list_display_links = ('numero_protocolo_tarefa', 'nome_servico')
    
    # ============================================
    # FILTROS LATERAIS - INCLUINDO NOVOS CAMPOS
    # ============================================
    
    list_filter = (
        'ativa',                        # ← NOVO FILTRO: Tarefas ativas/arquivadas
        'tipo_fila',                    # ← NOVO FILTRO: Filtrar por fila
        'nivel_criticidade_calculado',
        'regra_aplicada_calculado',
        'status_tarefa',
        'tem_justificativa_ativa',  # ← NOVO FILTRO
        'tem_solicitacao_ajuda',    # ← NOVO FILTRO
        'servico_excluido_criticidade', # ← NOVO FILTRO
        'nome_gex_responsavel',
        'indicador_subtarefas_pendentes',
        'indicador_tarefa_reaberta',
        'data_distribuicao_tarefa',
        'data_prazo',
        'data_calculo_criticidade',
    )
    
    # ============================================
    # CAMPOS DE BUSCA
    # ============================================
    
    search_fields = (
        'numero_protocolo_tarefa',
        'nome_servico',
        'nome_profissional_responsavel',
        'siape_responsavel__siape',
        'siape_responsavel__nome_completo',
        'cpf_responsavel',
        'nome_gex_responsavel'
    )
    
    # ============================================
    # ORDENAÇÃO E PAGINAÇÃO
    # ============================================
    
    ordering = ('-pontuacao_criticidade', '-data_distribuicao_tarefa')
    list_per_page = 50
    
    # ============================================
    # CAMPOS SOMENTE LEITURA (AJUSTADOS)
    # ============================================
    
    readonly_fields = (
        'numero_protocolo_tarefa',
        'data_processamento_tarefa',
        'dias_com_servidor_display',
        'dias_ate_prazo_display',
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
        # ← NOVOS CAMPOS DE JUSTIFICATIVA
        'tem_justificativa_ativa',
        'tem_solicitacao_ajuda',
        'servico_excluido_criticidade',
        # ← NOVOS CAMPOS DE FILA E ARQUIVAMENTO
        'tipo_fila',
        'ativa',
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
        }),
        ('🛡️ Justificativas, Ajudas e Exceções', {
            'fields': (
                'tem_justificativa_ativa',
                'tem_solicitacao_ajuda',
                'servico_excluido_criticidade',
            ),
            'description': 'Flags que indicam se esta tarefa possui exceções de análise.'
        }),
        ('📂 Classificação e Arquivamento', {
            'fields': (
                'tipo_fila',
                'ativa',
            ),
            'description': 'Tipo de fila de trabalho e status de arquivamento da tarefa.'
        })
    )
    
    # ============================================
    # AÇÕES EM MASSA (AJUSTADAS)
    # ============================================
    
    actions = [
        'exportar_tarefas_com_prazo_vencido',
        'exportar_tarefas_criticas',
    ]
    
    # ============================================
    # MÉTODOS DE EXIBIÇÃO - BADGES E FORMATAÇÃO
    # ============================================
    
    def status_badge(self, obj):
        """Exibe o status com cores"""
        cores = {
            'Pendente': 'orange',
            'Cumprimento de exigência': 'blue',
            'Exigência cumprida': '#0d6efd', # Azul mais forte
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
        """← CORRIGIDO: Usa a propriedade 'badge_html_criticidade' do model"""
        return format_html(obj.badge_html_criticidade)
    criticidade_badge.short_description = 'Criticidade'
    criticidade_badge.admin_order_field = 'pontuacao_criticidade'
    
    def regra_badge(self, obj):
        """← NOVO: Exibe badge da regra aplicada"""
        if obj.regra_aplicada_calculado == 'NENHUMA':
            return format_html('<span style="color: gray;">-</span>')
        
        return format_html(
            '<span style="background-color: #0d6efd; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            obj.regra_aplicada_calculado
        )
    regra_badge.short_description = 'Regra'
    regra_badge.admin_order_field = 'regra_aplicada_calculado'
    
    def justificativa_badge(self, obj):
        """← NOVO: Exibe status de justificativa/ajuda"""
        if obj.tem_justificativa_ativa:
            return format_html(
                '<span style="background-color: #198754; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-weight: bold;">🛡️ JUSTIFICADA</span>'
            )
        if obj.tem_solicitacao_ajuda:
            return format_html(
                '<span style="background-color: #ffc107; color: black; padding: 3px 8px; '
                'border-radius: 3px; font-weight: bold;">🆘 AJUDA</span>'
            )
        return format_html('<span style="color: gray;">-</span>')
    justificativa_badge.short_description = 'Exceção'
    
    def prazo_badge(self, obj):
        """Exibe badge do prazo (Sem alteração, está correto)"""
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
        else:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ {} dias</span>',
                dias
            )
    prazo_badge.short_description = 'Prazo'
    
    def reaberta_badge(self, obj):
        """Indica se a tarefa foi reaberta (Sem alteração, está correto)"""
        if obj.foi_reaberta:
            return format_html(
                '<span style="background-color: #9c27b0; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-weight: bold;">🔄 REABERTA</span>'
            )
        return format_html('<span style="color: gray;">-</span>')
    reaberta_badge.short_description = 'Reaberta?'

    def ativa_badge(self, obj):
        """← NOVO: Indica se a tarefa está ativa ou arquivada"""
        if obj.ativa:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-weight: bold;">✓ ATIVA</span>'
            )
        return format_html(
            '<span style="background-color: #6c757d; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-weight: bold;">📦 ARQUIVADA</span>'
        )
    ativa_badge.short_description = 'Status'
    ativa_badge.admin_order_field = 'ativa'

    def gex_responsavel(self, obj):
        if obj.nome_gex_responsavel:
            nome_curto = ' '.join(obj.nome_gex_responsavel.split()[:3])
            return nome_curto
        return '-'
    gex_responsavel.short_description = 'GEX'
    
    def dias_com_servidor_display(self, obj):
        dias = obj.dias_com_servidor
        if dias > 30: cor = 'red'
        elif dias > 10: cor = 'orange'
        else: cor = 'green'
        return format_html('<span style="color: {}; font-weight: bold;">{} dias</span>', cor, dias)
    dias_com_servidor_display.short_description = 'Dias c/ Servidor'
    
    def dias_ate_prazo_display(self, obj):
        dias = obj.dias_ate_prazo
        if dias is None: return 'Sem prazo definido'
        if dias < 0: return format_html('<span style="color: red; font-weight: bold;">Vencido há {} dias</span>', abs(dias))
        elif dias == 0: return format_html('<span style="color: orange; font-weight: bold;">Vence HOJE</span>')
        else: return format_html('<span style="color: green;">Faltam {} dias</span>', dias)
    dias_ate_prazo_display.short_description = 'Dias até o Prazo'
    
    def resumo_criticidade_visual(self, obj):
        """← CORRIGIDO: Exibe resumo visual alinhado com o model (Crítica/Regular)"""
        if obj.nivel_criticidade_calculado == 'REGULAR':
            return format_html(
                '<div style="padding: 15px; background-color: #f0fff0; border-radius: 5px; '
                'border-left: 4px solid #28a745;">'
                '<h3 style="margin-top: 0; color: #28a745;">✅ TAREFA REGULAR</h3>'
                '<p>Esta tarefa não possui criticidade detectada.</p>'
                '</div>'
            )
        
        # Se for CRÍTICA
        cor = obj.cor_criticidade_calculado
        
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
    # AÇÕES EM MASSA (AJUSTADAS)
    # ============================================
    
    @admin.action(description='📊 Exportar tarefas com prazo vencido para CSV')
    def exportar_tarefas_com_prazo_vencido(self, request, queryset):
        import csv
        from django.http import HttpResponse
        
        tarefas_prazo_vencido = [t for t in queryset if t.prazo_vencido]
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="tarefas_prazo_vencido.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Protocolo', 'Serviço', 'Status', 'Responsável', 'SIAPE', 'Data do Prazo', 'Dias de Atraso', 'Reaberta', 'Criticidade'])
        
        for tarefa in tarefas_prazo_vencido:
            writer.writerow([
                tarefa.numero_protocolo_tarefa, tarefa.nome_servico, tarefa.status_tarefa,
                tarefa.nome_profissional_responsavel, tarefa.siape_responsavel.siape if tarefa.siape_responsavel else '',
                tarefa.data_prazo.strftime('%d/%m/%Y') if tarefa.data_prazo else '',
                abs(tarefa.dias_ate_prazo) if tarefa.dias_ate_prazo else 0,
                'Sim' if tarefa.foi_reaberta else 'Não', tarefa.nivel_criticidade_calculado
            ])
        
        self.message_user(request, f'{len(tarefas_prazo_vencido)} tarefas com prazo vencido exportadas.')
        return response
    
    @admin.action(description='🔴 Exportar tarefas CRÍTICAS para CSV')
    def exportar_tarefas_criticas(self, request, queryset):
        """← CORRIGIDO: Exporta apenas tarefas com criticidade CRÍTICA"""
        import csv
        from django.http import HttpResponse
        
        # Filtro simples para 'CRÍTICA'
        tarefas_criticas = queryset.filter(
            nivel_criticidade_calculado='CRÍTICA'
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
                tarefa.numero_protocolo_tarefa, tarefa.nome_servico, tarefa.status_tarefa,
                tarefa.nome_profissional_responsavel, tarefa.siape_responsavel.siape if tarefa.siape_responsavel else '',
                tarefa.nome_gex_responsavel, tarefa.nivel_criticidade_calculado,
                tarefa.regra_aplicada_calculado, tarefa.pontuacao_criticidade,
                tarefa.dias_pendente_criticidade_calculado, tarefa.prazo_limite_criticidade_calculado,
                tarefa.alerta_criticidade_calculado,
                tarefa.data_distribuicao_tarefa.strftime('%d/%m/%Y') if tarefa.data_distribuicao_tarefa else ''
            ])
        
        self.message_user(request, f'{tarefas_criticas.count()} tarefas críticas exportadas com sucesso.', level='success')
        return response


# ============================================
# ADMINISTRAÇÃO DOS NOVOS MODELS
# ============================================

@admin.register(TipoJustificativa)
class TipoJustificativaAdmin(admin.ModelAdmin):
    """Administração para Tipos de Justificativas"""
    list_display = ('nome', 'ativo', 'ordem_exibicao', 'descricao')
    list_editable = ('ativo', 'ordem_exibicao')
    search_fields = ('nome', 'descricao')
    list_filter = ('ativo',)
    ordering = ('ordem_exibicao', 'nome')

@admin.register(Justificativa)
class JustificativaAdmin(admin.ModelAdmin):
    """Administração para Justificativas de tarefas"""
    list_display = (
        'protocolo_tarefa', 
        'tipo_justificativa', 
        'status_badge', 
        'servidor', 
        'data_submissao', 
        'analisado_por', 
        'data_analise'
    )
    list_filter = ('status', 'tipo_justificativa', 'data_submissao', 'data_analise')
    search_fields = (
        'tarefa__numero_protocolo_tarefa', 
        'protocolo_original', 
        'servidor__nome_completo', 
        'servidor__siape',
        'analisado_por__nome_completo'
    )
    autocomplete_fields = ('tarefa', 'servidor', 'analisado_por')
    readonly_fields = ('data_submissao', 'protocolo_original', 'data_analise')
    ordering = ('-data_submissao',)
    
    fieldsets = (
        ('ℹ️ Dados da Submissão', {
            'fields': ('tarefa', 'servidor', 'tipo_justificativa', 'descricao', 'data_submissao', 'protocolo_original')
        }),
        ('⚖️ Dados da Análise (Equipe Volante)', {
            'fields': ('status', 'analisado_por', 'parecer', 'data_analise'),
            'classes': ('collapse-open',)
        }),
    )

    @admin.display(description='Protocolo', ordering='tarefa__numero_protocolo_tarefa')
    def protocolo_tarefa(self, obj):
        return obj.tarefa.numero_protocolo_tarefa
    
    @admin.display(description='Status', ordering='status')
    def status_badge(self, obj):
        cores = {
            'PENDENTE': 'orange',
            'APROVADA': 'green',
            'REPROVADA': 'red',
        }
        cor = cores.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            cor, obj.get_status_display()
        )

@admin.register(SolicitacaoAjuda)
class SolicitacaoAjudaAdmin(admin.ModelAdmin):
    """Administração para Solicitações de Ajuda"""
    list_display = (
        'protocolo_tarefa', 
        'servidor_solicitante', 
        'status_badge', 
        'data_solicitacao', 
        'atendido_por', 
        'data_conclusao'
    )
    list_filter = ('status', 'data_solicitacao', 'data_atendimento', 'data_conclusao')
    search_fields = (
        'tarefa__numero_protocolo_tarefa', 
        'protocolo_original', 
        'servidor_solicitante__nome_completo', 
        'servidor_solicitante__siape'
    )
    autocomplete_fields = ('tarefa', 'servidor_solicitante', 'atendido_por')
    readonly_fields = ('data_solicitacao', 'protocolo_original', 'data_atendimento', 'data_conclusao')
    ordering = ('-data_solicitacao',)

    fieldsets = (
        ('🆘 Dados da Solicitação', {
            'fields': ('tarefa', 'servidor_solicitante', 'descricao', 'data_solicitacao', 'protocolo_original')
        }),
        ('✅ Dados do Atendimento (Equipe Volante)', {
            'fields': ('status', 'atendido_por', 'observacoes_atendimento', 'data_atendimento', 'data_conclusao'),
            'classes': ('collapse-open',)
        }),
    )

    @admin.display(description='Protocolo', ordering='tarefa__numero_protocolo_tarefa')
    def protocolo_tarefa(self, obj):
        return obj.tarefa.numero_protocolo_tarefa
    
    @admin.display(description='Status', ordering='status')
    def status_badge(self, obj):
        cores = {
            'PENDENTE': 'orange',
            'EM_ATENDIMENTO': 'blue',
            'CONCLUIDA': 'green',
            'CANCELADA': 'gray',
        }
        cor = cores.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            cor, obj.get_status_display()
        )

@admin.register(ServicosCriticidade)
class ServicosCriticidadeAdmin(admin.ModelAdmin):
    """Administração para Configuração de Serviços Excluídos"""
    
    # CORREÇÃO: 'excluido_badge' removido de list_display
    list_display = (
        'nome_servico', 
        'excluido_criticidade',  # <-- CAMPO CORRIGIDO (para ser editável)
        'configurado_por', 
        'data_ultima_alteracao'
    )
    search_fields = ('nome_servico', 'motivo_exclusao')
    list_filter = ('excluido_criticidade',)
    list_editable = ('excluido_criticidade',) # <-- CORREÇÃO: Deve bater com list_display
    readonly_fields = ('data_configuracao', 'data_ultima_alteracao', 'configurado_por')
    ordering = ('nome_servico',)

    def save_model(self, request, obj, form, change):
        """Atribui o usuário logado ao salvar"""
        if not obj.pk or 'configurado_por' not in form.changed_data:
            obj.configurado_por = request.user
        super().save_model(request, obj, form, change)
    
    # CORREÇÃO: Método 'excluido_badge' removido pois não é mais usado no list_display


# ============================================
# ADMINISTRAÇÃO DO MODEL NOTIFICACAOEMAIL
# ============================================

@admin.register(NotificacaoEmail)
class NotificacaoEmailAdmin(admin.ModelAdmin):
    """
    Administração para NotificacaoEmail.
    (Mantido como fornecido, está correto)
    """
    
    list_display = ('id', 'tipo', 'assunto', 'destinatario', 'enviado_em', 'status_badge')
    list_display_links = ('id', 'assunto')
    list_filter = ('tipo', 'sucesso', 'enviado_em')
    search_fields = ('assunto', 'destinatario__nome_completo', 'destinatario__email', 'mensagem')
    ordering = ('-enviado_em',)
    list_per_page = 50
    readonly_fields = ('enviado_em',)
    
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


# ============================================
# ADMINISTRAÇÃO DE FILAS DE TRABALHO
# ============================================

@admin.register(Fila)
class FilaAdmin(admin.ModelAdmin):
    """
    📋 GERENCIAMENTO DE FILAS DE TRABALHO

    Use esta interface para adicionar, editar ou remover filas do sistema.
    """

    list_display = (
        'id',
        'codigo',
        'nome',
        'cor_badge',
        'icone_display',
        'ordem',
        'ativa_badge',
        'total_configuracoes',
    )

    list_display_links = ('id', 'codigo', 'nome')

    list_filter = (
        'ativa',
        'data_criacao',
    )

    search_fields = (
        'codigo',
        'nome',
        'nome_completo',
        'descricao',
    )

    ordering = ('ordem', 'nome')

    list_per_page = 20

    readonly_fields = (
        'data_criacao',
        'criado_por',
        'data_ultima_alteracao',
        'alterado_por',
    )

    fieldsets = (
        ('Identificação', {
            'fields': (
                'codigo',
                'nome',
                'nome_completo',
                'descricao',
            )
        }),
        ('Aparência', {
            'fields': (
                'cor',
                'icone',
            ),
            'description': 'Configurações visuais da fila'
        }),
        ('Configurações', {
            'fields': (
                'ordem',
                'ativa',
            )
        }),
        ('Auditoria', {
            'fields': (
                'data_criacao',
                'criado_por',
                'data_ultima_alteracao',
                'alterado_por',
            ),
            'classes': ('collapse',),
        }),
    )

    actions = ['ativar_filas', 'desativar_filas']

    def cor_badge(self, obj):
        """Exibe preview da cor"""
        return format_html(
            '<div style="width: 30px; height: 20px; background-color: {}; '
            'border: 1px solid #ddd; border-radius: 3px;"></div>',
            obj.cor
        )
    cor_badge.short_description = 'Cor'

    def icone_display(self, obj):
        """Exibe preview do ícone"""
        return format_html(
            '<i class="{}" style="font-size: 18px;"></i>',
            obj.icone
        )
    icone_display.short_description = 'Ícone'

    def ativa_badge(self, obj):
        """Badge de status ativo/inativo"""
        if obj.ativa:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-weight: bold;">ATIVA</span>'
            )
        return format_html(
            '<span style="background-color: #6c757d; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-weight: bold;">INATIVA</span>'
        )
    ativa_badge.short_description = 'Status'
    ativa_badge.admin_order_field = 'ativa'

    def total_configuracoes(self, obj):
        """Mostra quantas configurações de serviços apontam para esta fila"""
        total = ConfiguracaoFila.objects.filter(tipo_fila=obj.codigo, ativa=True).count()
        if total > 0:
            return format_html(
                '<a href="/admin/tarefas/configuracaofila/?tipo_fila={}" '
                'style="text-decoration: none;">{} serviços</a>',
                obj.codigo, total
            )
        return format_html('<span style="color: #999;">0 serviços</span>')
    total_configuracoes.short_description = 'Configurações'

    @admin.action(description='Ativar filas selecionadas')
    def ativar_filas(self, request, queryset):
        updated = queryset.update(ativa=True, alterado_por=request.user)
        self.message_user(request, f'{updated} fila(s) ativada(s).', level='success')

    @admin.action(description='Desativar filas selecionadas')
    def desativar_filas(self, request, queryset):
        updated = queryset.update(ativa=False, alterado_por=request.user)
        self.message_user(request, f'{updated} fila(s) desativada(s).', level='warning')

    def save_model(self, request, obj, form, change):
        """Salva o modelo com auditoria"""
        if not change:
            obj.criado_por = request.user
        obj.alterado_por = request.user
        super().save_model(request, obj, form, change)


# ============================================
# FORMULÁRIO PERSONALIZADO PARA CONFIGURAÇÃO DE FILAS
# ============================================

class ConfiguracaoFilaForm(forms.ModelForm):
    """Formulário personalizado com dropdown dinâmico de filas"""

    tipo_fila = forms.ChoiceField(
        label='Fila de Destino',
        help_text='Escolha a fila para onde este serviço será direcionado'
    )

    class Meta:
        model = ConfiguracaoFila
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Popula choices dinamicamente do modelo Fila
        self.fields['tipo_fila'].choices = [
            (fila.codigo, f"{fila.nome} - {fila.nome_completo}")
            for fila in Fila.objects.filter(ativa=True).order_by('ordem')
        ]


# ============================================
# ADMINISTRAÇÃO DE CONFIGURAÇÃO DE FILAS
# ============================================

@admin.register(ConfiguracaoFila)
class ConfiguracaoFilaAdmin(admin.ModelAdmin):
    """
    ⚙️ CONFIGURAÇÃO DE FILAS DE TRABALHO

    Use esta interface para gerenciar quais serviços pertencem a cada fila.
    Estas configurações determinam automaticamente como as tarefas são classificadas.
    """

    # Formulário customizado com dropdown dinâmico de filas
    form = ConfiguracaoFilaForm

    # Campos exibidos na listagem
    list_display = (
        'id',
        'nome_servico_resumido',
        'codigo_unidade',
        'fila_badge',
        'prioridade',
        'ativa_badge',
        'data_criacao_display',
        'criado_por',
    )

    list_display_links = ('id', 'nome_servico_resumido')

    # Filtros laterais
    list_filter = (
        'tipo_fila',
        'ativa',
        'codigo_unidade',
        'prioridade',
        'data_criacao',
    )

    # Campos de busca
    search_fields = (
        'nome_servico',
        'observacoes',
    )

    # Ordenação padrão
    ordering = ('prioridade', 'tipo_fila', 'nome_servico')

    # Paginação
    list_per_page = 50

    # Campos somente leitura
    readonly_fields = (
        'data_criacao',
        'criado_por',
        'data_ultima_alteracao',
        'alterado_por',
    )

    # Organização dos campos no formulário
    fieldsets = (
        ('Identificação do Serviço', {
            'fields': (
                'nome_servico',
                'codigo_unidade',
            ),
            'description': 'Defina o serviço e opcionalmente a unidade do INSS.'
        }),
        ('Classificação', {
            'fields': (
                'tipo_fila',
                'prioridade',
            ),
            'description': 'Escolha a fila de destino e a prioridade desta regra.'
        }),
        ('Controle', {
            'fields': (
                'ativa',
                'observacoes',
            )
        }),
        ('Auditoria', {
            'fields': (
                'data_criacao',
                'criado_por',
                'data_ultima_alteracao',
                'alterado_por',
            ),
            'classes': ('collapse',),
            'description': 'Informações de auditoria (geradas automaticamente)'
        }),
    )

    # Ações em massa
    actions = ['ativar_configuracoes', 'desativar_configuracoes', 'duplicar_configuracoes']

    def nome_servico_resumido(self, obj):
        """Exibe nome do serviço truncado"""
        if len(obj.nome_servico) > 60:
            return obj.nome_servico[:60] + '...'
        return obj.nome_servico
    nome_servico_resumido.short_description = 'Serviço'
    nome_servico_resumido.admin_order_field = 'nome_servico'

    def fila_badge(self, obj):
        """Exibe badge colorido da fila"""
        cores = {
            'PGB': '#007bff',
            'CEABRD-23150521': '#28a745',
            'CEAB-BI-23150521': '#ffc107',
            'CEAB-RECURSO-23150521': '#dc3545',
            'CEAB-DEFESO-23150521': '#17a2b8',
            'CEAB-COMPREV-23150521': '#6f42c1',
            'CEAB-MOB-23150521': '#fd7e14',
            'OUTROS': '#6c757d',
        }
        cor = cores.get(obj.tipo_fila, '#6c757d')

        # Nomes amigáveis para exibição
        nomes_filas = {
            'PGB': 'PGB',
            'CEABRD-23150521': 'CEABRD',
            'CEAB-BI-23150521': 'CEAB-BI',
            'CEAB-RECURSO-23150521': 'CEAB-RECURSO',
            'CEAB-DEFESO-23150521': 'CEAB-DEFESO',
            'CEAB-COMPREV-23150521': 'CEAB-COMPREV',
            'CEAB-MOB-23150521': 'CEAB-MOB',
            'OUTROS': 'OUTROS',
        }
        nome_exibicao = nomes_filas.get(obj.tipo_fila, obj.tipo_fila)

        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 10px; '
            'border-radius: 3px; font-weight: bold; font-size: 11px;">{}</span>',
            cor, nome_exibicao
        )
    fila_badge.short_description = 'Fila'
    fila_badge.admin_order_field = 'tipo_fila'

    def ativa_badge(self, obj):
        """Indica se a configuração está ativa"""
        if obj.ativa:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-weight: bold;">ATIVA</span>'
            )
        return format_html(
            '<span style="background-color: #6c757d; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-weight: bold;">INATIVA</span>'
        )
    ativa_badge.short_description = 'Status'
    ativa_badge.admin_order_field = 'ativa'

    def data_criacao_display(self, obj):
        """Exibe data de criação formatada"""
        return obj.data_criacao.strftime('%d/%m/%Y %H:%M')
    data_criacao_display.short_description = 'Criada em'
    data_criacao_display.admin_order_field = 'data_criacao'

    @admin.action(description='Ativar configurações selecionadas')
    def ativar_configuracoes(self, request, queryset):
        """Ativa as configurações selecionadas"""
        updated = queryset.update(ativa=True, alterado_por=request.user)
        self.message_user(
            request,
            f'{updated} configuração(ões) ativada(s) com sucesso.',
            level='success'
        )

    @admin.action(description='Desativar configurações selecionadas')
    def desativar_configuracoes(self, request, queryset):
        """Desativa as configurações selecionadas"""
        updated = queryset.update(ativa=False, alterado_por=request.user)
        self.message_user(
            request,
            f'{updated} configuração(ões) desativada(s) com sucesso.',
            level='success'
        )

    @admin.action(description='Duplicar configurações selecionadas')
    def duplicar_configuracoes(self, request, queryset):
        """Duplica as configurações selecionadas"""
        duplicadas = 0
        for config in queryset:
            config.pk = None  # Remove o ID para criar novo registro
            config.criado_por = request.user
            config.alterado_por = request.user
            config.observacoes = f"[DUPLICADA] {config.observacoes}"
            config.save()
            duplicadas += 1

        self.message_user(
            request,
            f'{duplicadas} configuração(ões) duplicada(s) com sucesso.',
            level='success'
        )

    def save_model(self, request, obj, form, change):
        """Salva o modelo com informações de auditoria"""
        if not change:  # Novo registro
            obj.criado_por = request.user
        obj.alterado_por = request.user
        super().save_model(request, obj, form, change)


# ============================================
# ADMINISTRAÇÃO DO HISTÓRICO DE AÇÕES EM LOTE
# ============================================

@admin.register(HistoricoAcaoLote)
class HistoricoAcaoLoteAdmin(admin.ModelAdmin):
    """Administração para histórico de geração de arquivos em lote."""

    list_display = (
        'id',
        'data_geracao',
        'servidor_info',
        'codigo_fila',
        'tipo_acao_badge',
        'criterio_selecao',
        'quantidade_tarefas',
        'gerado_por',
        'nome_arquivo',
    )

    list_filter = (
        'tipo_acao',
        'criterio_selecao',
        'codigo_fila',
        'data_geracao',
    )

    search_fields = (
        'servidor__siape',
        'servidor__nome_completo',
        'codigo_fila',
        'nome_arquivo',
        'protocolos_incluidos',
    )

    readonly_fields = (
        'servidor',
        'codigo_fila',
        'tipo_acao',
        'criterio_selecao',
        'servico_selecionado',
        'quantidade_tarefas',
        'uo_destino',
        'despacho',
        'data_geracao',
        'gerado_por',
        'nome_arquivo',
        'protocolos_detalhados',
    )

    fieldsets = (
        ('Informações Principais', {
            'fields': (
                'servidor',
                'codigo_fila',
                'tipo_acao',
                'data_geracao',
                'gerado_por',
            )
        }),
        ('Critérios de Seleção', {
            'fields': (
                'criterio_selecao',
                'servico_selecionado',
                'quantidade_tarefas',
            )
        }),
        ('Dados da Transferência', {
            'fields': (
                'uo_destino',
                'despacho',
            ),
            'classes': ('collapse',),
        }),
        ('Arquivo Gerado', {
            'fields': (
                'nome_arquivo',
                'protocolos_detalhados',
            )
        }),
    )

    def servidor_info(self, obj):
        """Exibe informações do servidor"""
        if obj.servidor:
            return format_html(
                '<strong>{}</strong><br><small>{}</small>',
                obj.servidor.nome_completo,
                obj.servidor.siape
            )
        return '-'
    servidor_info.short_description = 'Servidor'

    def tipo_acao_badge(self, obj):
        """Exibe badge do tipo de ação"""
        cores = {
            'REMOVER_RESPONSAVEL': 'warning',
            'TRANSFERIR_TAREFA': 'info',
        }
        cor = cores.get(obj.tipo_acao, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            cor,
            obj.get_tipo_acao_display()
        )
    tipo_acao_badge.short_description = 'Tipo de Ação'

    def protocolos_detalhados(self, obj):
        """Exibe protocolos em formato mais legível"""
        if obj.protocolos_incluidos:
            protocolos = obj.protocolos_incluidos.split(',')
            if len(protocolos) <= 10:
                return format_html('<br>'.join(protocolos))
            else:
                primeiros = protocolos[:10]
                total = len(protocolos)
                return format_html(
                    '{}<br><strong>... e mais {} protocolo(s)</strong>',
                    '<br>'.join(primeiros),
                    total - 10
                )
        return '-'
    protocolos_detalhados.short_description = 'Protocolos Incluídos'

    def has_add_permission(self, request):
        """Não permite adicionar manualmente (somente via sistema)"""
        return False

    def has_change_permission(self, request, obj=None):
        """Não permite editar (somente leitura)"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Permite deletar apenas para superusuários"""
        return request.user.is_superuser
