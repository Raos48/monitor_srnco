"""
Admin customizado para Parâmetros de Análise
Interface amigável para configuração de prazos
"""

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Q
from .parametros import ParametrosAnalise, HistoricoAlteracaoPrazos


@admin.register(ParametrosAnalise)
class ParametrosAnaliseAdmin(admin.ModelAdmin):
    """
    Interface administrativa para configuração de prazos.
    """
    
    # Campos exibidos na listagem
    list_display = (
        'id',
        'status_badge',
        'prazo_analise_exigencia_cumprida',
        'prazo_tolerancia_exigencia',
        'prazo_servidor_apos_vencimento',
        'prazo_primeira_acao',
        'data_atualizacao',
        'usuario_atualizacao',
        'acoes_rapidas'
    )
    
    # Campos clicáveis
    list_display_links = ('id',)
    
    # Filtros laterais
    list_filter = (
        'ativo',
        'data_criacao',
        'data_atualizacao'
    )
    
    # Campos de busca
    search_fields = (
        'observacoes',
        'usuario_atualizacao'
    )
    
    # Ordenação padrão
    ordering = ('-ativo', '-data_atualizacao')
    
    # Campos somente leitura
    readonly_fields = (
        'data_criacao',
        'data_atualizacao',
        'prazo_total_exigencia',
        'prazo_total_servidor_exigencia',
        'resumo_visual_prazos'
    )
    
    # Organização dos campos no formulário
    fieldsets = (
        ('⚙️ Status da Configuração', {
            'fields': ('ativo',),
            'description': '⚠️ ATENÇÃO: Apenas UMA configuração pode estar ativa por vez.'
        }),
        ('📋 REGRA 1: Exigência Cumprida - Aguardando Análise', {
            'fields': ('prazo_analise_exigencia_cumprida',),
            'description': 'Prazo para o servidor analisar uma exigência após ela ser cumprida pelo segurado.'
        }),
        ('📋 REGRA 2: Cumprimento de Exigência pelo Segurado', {
            'fields': (
                'prazo_tolerancia_exigencia',
                'prazo_servidor_apos_vencimento',
                'prazo_total_exigencia',
                'prazo_total_servidor_exigencia'
            ),
            'description': 'Prazos relacionados ao cumprimento de exigências e ação do servidor após vencimento.'
        }),
        ('📋 REGRAS 3 e 4: Primeira Ação do Servidor', {
            'fields': ('prazo_primeira_acao',),
            'description': 'Prazo para o servidor realizar a primeira ação em uma tarefa nova ou com exigência já cumprida.'
        }),
        ('📝 Informações de Controle', {
            'fields': (
                'usuario_atualizacao',
                'observacoes',
                'data_criacao',
                'data_atualizacao',
                'resumo_visual_prazos'
            ),
            'classes': ('collapse',)
        })
    )
    
    # Ações em massa
    actions = ['ativar_configuracao', 'desativar_configuracao', 'duplicar_configuracao']
    
    def status_badge(self, obj):
        """Exibe badge de status (ativo/inativo)"""
        if obj.ativo:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 5px 12px; '
                'border-radius: 3px; font-weight: bold; font-size: 11px;">✓ ATIVA</span>'
            )
        return format_html(
            '<span style="background-color: #6c757d; color: white; padding: 5px 12px; '
            'border-radius: 3px; font-size: 11px;">○ Inativa</span>'
        )
    status_badge.short_description = 'Status'
    
    def acoes_rapidas(self, obj):
        """Exibe botões de ação rápida"""
        if obj.ativo:
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">● EM USO</span>'
            )
        return format_html(
            '<a class="button" href="/admin/tarefas/parametrosanalise/{}/change/" '
            'style="background-color: #007bff; color: white; padding: 3px 10px; '
            'text-decoration: none; border-radius: 3px; font-size: 11px;">'
            'Editar</a>',
            obj.pk
        )
    acoes_rapidas.short_description = 'Ações'
    
    def resumo_visual_prazos(self, obj):
        """Exibe resumo visual dos prazos configurados"""
        html = '''
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; border-left: 4px solid #007bff;">
            <h3 style="margin-top: 0; color: #007bff;">📊 Resumo dos Prazos Configurados</h3>
            
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="background-color: #e9ecef;">
                    <th style="padding: 10px; text-align: left; border-bottom: 2px solid #dee2e6;">Regra</th>
                    <th style="padding: 10px; text-align: left; border-bottom: 2px solid #dee2e6;">Descrição</th>
                    <th style="padding: 10px; text-align: center; border-bottom: 2px solid #dee2e6;">Prazo</th>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #dee2e6;"><strong>REGRA 1</strong></td>
                    <td style="padding: 10px; border-bottom: 1px solid #dee2e6;">Análise de Exigência Cumprida</td>
                    <td style="padding: 10px; text-align: center; border-bottom: 1px solid #dee2e6;">
                        <span style="background-color: #007bff; color: white; padding: 5px 15px; border-radius: 3px; font-weight: bold;">
                            {} dias
                        </span>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #dee2e6;"><strong>REGRA 2</strong></td>
                    <td style="padding: 10px; border-bottom: 1px solid #dee2e6;">Tolerância para Cumprimento</td>
                    <td style="padding: 10px; text-align: center; border-bottom: 1px solid #dee2e6;">
                        <span style="background-color: #17a2b8; color: white; padding: 5px 15px; border-radius: 3px; font-weight: bold;">
                            {} dias
                        </span>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #dee2e6;"><strong>REGRA 2</strong></td>
                    <td style="padding: 10px; border-bottom: 1px solid #dee2e6;">Servidor Após Vencimento</td>
                    <td style="padding: 10px; text-align: center; border-bottom: 1px solid #dee2e6;">
                        <span style="background-color: #ffc107; color: black; padding: 5px 15px; border-radius: 3px; font-weight: bold;">
                            {} dias
                        </span>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 10px;"><strong>REGRAS 3 e 4</strong></td>
                    <td style="padding: 10px;">Primeira Ação do Servidor</td>
                    <td style="padding: 10px; text-align: center;">
                        <span style="background-color: #28a745; color: white; padding: 5px 15px; border-radius: 3px; font-weight: bold;">
                            {} dias
                        </span>
                    </td>
                </tr>
            </table>
            
            <div style="margin-top: 15px; padding: 10px; background-color: #fff3cd; border-left: 4px solid #ffc107; border-radius: 3px;">
                <strong>⚠️ Observação:</strong> Alterações nestes prazos afetarão imediatamente a classificação de criticidade de todas as tarefas.
            </div>
        </div>
        '''.format(
            obj.prazo_analise_exigencia_cumprida,
            obj.prazo_tolerancia_exigencia,
            obj.prazo_servidor_apos_vencimento,
            obj.prazo_primeira_acao
        )
        return format_html(html)
    resumo_visual_prazos.short_description = 'Visualização dos Prazos'
    
    @admin.action(description='✓ Ativar configuração selecionada')
    def ativar_configuracao(self, request, queryset):
        """Ativa a configuração selecionada"""
        if queryset.count() > 1:
            self.message_user(
                request,
                'Selecione apenas UMA configuração para ativar.',
                level='error'
            )
            return
        
        config = queryset.first()
        config.ativar()
        
        self.message_user(
            request,
            f'Configuração ativada com sucesso! Esta é agora a configuração ativa do sistema.',
            level='success'
        )
    
    @admin.action(description='○ Desativar configurações selecionadas')
    def desativar_configuracao(self, request, queryset):
        """Desativa as configurações selecionadas"""
        count = queryset.filter(ativo=True).count()
        
        if count == 0:
            self.message_user(
                request,
                'Nenhuma configuração ativa foi selecionada.',
                level='warning'
            )
            return
        
        queryset.filter(ativo=True).update(ativo=False)
        
        self.message_user(
            request,
            f'{count} configuração(ões) desativada(s) com sucesso.',
            level='success'
        )
    
    @admin.action(description='📋 Duplicar configurações selecionadas')
    def duplicar_configuracao(self, request, queryset):
        """Duplica as configurações selecionadas"""
        count = 0
        for config in queryset:
            config.duplicar()
            count += 1
        
        self.message_user(
            request,
            f'{count} configuração(ões) duplicada(s) com sucesso. As novas configurações estão INATIVAS.',
            level='success'
        )
    
    def save_model(self, request, obj, form, change):
        """Captura o usuário que está salvando"""
        if request.user.is_authenticated:
            obj.usuario_atualizacao = request.user.get_full_name() or request.user.username
        super().save_model(request, obj, form, change)


@admin.register(HistoricoAlteracaoPrazos)
class HistoricoAlteracaoPrazosAdmin(admin.ModelAdmin):
    """
    Interface administrativa para histórico de alterações.
    Apenas visualização (não permite edição).
    """
    
    # Campos exibidos na listagem
    list_display = (
        'data_alteracao',
        'campo_alterado',
        'valores_badge',
        'usuario',
        'configuracao'
    )
    
    # Filtros laterais
    list_filter = (
        'campo_alterado',
        'data_alteracao',
        'usuario'
    )
    
    # Campos de busca
    search_fields = (
        'campo_alterado',
        'motivo',
        'usuario'
    )
    
    # Ordenação padrão
    ordering = ('-data_alteracao',)
    
    # Campos somente leitura (tudo)
    readonly_fields = (
        'configuracao',
        'data_alteracao',
        'usuario',
        'campo_alterado',
        'valor_anterior',
        'valor_novo',
        'motivo'
    )
    
    # Desabilitar adição/edição/exclusão
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def valores_badge(self, obj):
        """Exibe a mudança de valores de forma visual"""
        return format_html(
            '<span style="background-color: #dc3545; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-weight: bold;">{}</span> '
            '<span style="margin: 0 5px;">→</span> '
            '<span style="background-color: #28a745; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            obj.valor_anterior,
            obj.valor_novo
        )
    valores_badge.short_description = 'Alteração'