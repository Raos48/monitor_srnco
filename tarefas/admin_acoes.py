"""
Administração Django para modelos de ações automatizadas.

Gerencia bloqueios, notificações, históricos e templates de email.
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    BloqueioServidor, SolicitacaoNotificacao,
    HistoricoBloqueio, HistoricoNotificacao,
    HistoricoEmail, TemplateEmail
)


# ============================================
# BLOQUEIO DE SERVIDOR
# ============================================

@admin.register(BloqueioServidor)
class BloqueioServidorAdmin(admin.ModelAdmin):
    """Administração de bloqueios de servidor"""

    list_display = (
        'id',
        'siape_servidor',
        'codigo_fila',
        'tipo_acao_badge',
        'status_badge',
        'data_solicitacao_display',
        'solicitado_por',
    )

    list_display_links = ('id', 'siape_servidor')

    list_filter = (
        'tipo_acao',
        'status',
        'codigo_fila',
        'data_solicitacao',
    )

    search_fields = (
        'servidor__siape',
        'servidor__nome_completo',
        'codigo_fila',
        'observacoes',
    )

    readonly_fields = (
        'data_solicitacao',
        'data_processamento',
        'data_conclusao',
    )

    ordering = ('-data_solicitacao',)

    list_per_page = 50

    fieldsets = (
        ('Informações do Bloqueio', {
            'fields': (
                'servidor',
                'codigo_fila',
                'tipo_acao',
                'status',
            )
        }),
        ('Datas', {
            'fields': (
                'data_solicitacao',
                'data_processamento',
                'data_conclusao',
            )
        }),
        ('Auditoria e Resposta', {
            'fields': (
                'solicitado_por',
                'observacoes',
                'resposta_robo',
                'mensagem_erro',
            )
        }),
    )

    def siape_servidor(self, obj):
        return obj.servidor.siape
    siape_servidor.short_description = 'SIAPE'
    siape_servidor.admin_order_field = 'servidor__siape'

    def tipo_acao_badge(self, obj):
        cores = {
            'BLOQUEIO': '#dc3545',
            'DESBLOQUEIO': '#28a745',
        }
        cor = cores.get(obj.tipo_acao, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            cor, obj.get_tipo_acao_display()
        )
    tipo_acao_badge.short_description = 'Ação'

    def status_badge(self, obj):
        cores = {
            'PENDENTE': '#ffc107',
            'PROCESSANDO': '#17a2b8',
            'CONCLUIDO': '#28a745',
            'ERRO': '#dc3545',
            'CANCELADO': '#6c757d',
        }
        cor = cores.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px;">{}</span>',
            cor, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def data_solicitacao_display(self, obj):
        return obj.data_solicitacao.strftime('%d/%m/%Y %H:%M')
    data_solicitacao_display.short_description = 'Solicitado em'
    data_solicitacao_display.admin_order_field = 'data_solicitacao'


# ============================================
# SOLICITAÇÃO DE NOTIFICAÇÃO PGB
# ============================================

@admin.register(SolicitacaoNotificacao)
class SolicitacaoNotificacaoAdmin(admin.ModelAdmin):
    """Administração de solicitações de notificação PGB"""

    list_display = (
        'id',
        'siape_servidor',
        'tipo_notificacao_badge',
        'status_badge',
        'numero_protocolo_criado',
        'data_solicitacao_display',
        'solicitado_por',
    )

    list_display_links = ('id', 'siape_servidor')

    list_filter = (
        'tipo_notificacao',
        'status',
        'data_solicitacao',
    )

    search_fields = (
        'servidor__siape',
        'servidor__nome_completo',
        'numero_protocolo_criado',
        'observacoes',
    )

    readonly_fields = (
        'data_solicitacao',
        'data_processamento',
        'data_conclusao',
    )

    ordering = ('-data_solicitacao',)

    list_per_page = 50

    fieldsets = (
        ('Informações da Notificação', {
            'fields': (
                'servidor',
                'tipo_notificacao',
                'status',
            )
        }),
        ('Resultado', {
            'fields': (
                'numero_protocolo_criado',
            )
        }),
        ('Datas', {
            'fields': (
                'data_solicitacao',
                'data_processamento',
                'data_conclusao',
            )
        }),
        ('Auditoria e Resposta', {
            'fields': (
                'solicitado_por',
                'observacoes',
                'resposta_robo',
                'mensagem_erro',
            )
        }),
    )

    def siape_servidor(self, obj):
        return obj.servidor.siape
    siape_servidor.short_description = 'SIAPE'
    siape_servidor.admin_order_field = 'servidor__siape'

    def tipo_notificacao_badge(self, obj):
        cores = {
            'PRIMEIRA_NOTIFICACAO': '#ffc107',
            'SEGUNDA_NOTIFICACAO': '#dc3545',
        }
        cor = cores.get(obj.tipo_notificacao, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            cor, obj.get_tipo_notificacao_display()
        )
    tipo_notificacao_badge.short_description = 'Tipo'

    def status_badge(self, obj):
        cores = {
            'PENDENTE': '#ffc107',
            'PROCESSANDO': '#17a2b8',
            'CONCLUIDO': '#28a745',
            'ERRO': '#dc3545',
            'CANCELADO': '#6c757d',
        }
        cor = cores.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px;">{}</span>',
            cor, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def data_solicitacao_display(self, obj):
        return obj.data_solicitacao.strftime('%d/%m/%Y %H:%M')
    data_solicitacao_display.short_description = 'Solicitado em'
    data_solicitacao_display.admin_order_field = 'data_solicitacao'


# ============================================
# HISTÓRICO DE BLOQUEIOS
# ============================================

@admin.register(HistoricoBloqueio)
class HistoricoBloqueioAdmin(admin.ModelAdmin):
    """Administração do histórico de bloqueios"""

    list_display = (
        'id',
        'siape_servidor',
        'codigo_fila',
        'tipo_acao',
        'status',
        'data_hora_display',
        'executado_por',
    )

    list_filter = (
        'tipo_acao',
        'status',
        'data_hora',
    )

    search_fields = (
        'servidor__siape',
        'servidor__nome_completo',
        'codigo_fila',
        'detalhes',
    )

    readonly_fields = ('data_hora',)

    ordering = ('-data_hora',)

    list_per_page = 100

    def siape_servidor(self, obj):
        return obj.servidor.siape
    siape_servidor.short_description = 'SIAPE'

    def data_hora_display(self, obj):
        return obj.data_hora.strftime('%d/%m/%Y %H:%M:%S')
    data_hora_display.short_description = 'Data/Hora'
    data_hora_display.admin_order_field = 'data_hora'


# ============================================
# HISTÓRICO DE NOTIFICAÇÕES
# ============================================

@admin.register(HistoricoNotificacao)
class HistoricoNotificacaoAdmin(admin.ModelAdmin):
    """Administração do histórico de notificações"""

    list_display = (
        'id',
        'siape_servidor',
        'tipo_notificacao',
        'status',
        'numero_protocolo',
        'data_hora_display',
        'executado_por',
    )

    list_filter = (
        'tipo_notificacao',
        'status',
        'data_hora',
    )

    search_fields = (
        'servidor__siape',
        'servidor__nome_completo',
        'numero_protocolo',
        'detalhes',
    )

    readonly_fields = ('data_hora',)

    ordering = ('-data_hora',)

    list_per_page = 100

    def siape_servidor(self, obj):
        return obj.servidor.siape
    siape_servidor.short_description = 'SIAPE'

    def data_hora_display(self, obj):
        return obj.data_hora.strftime('%d/%m/%Y %H:%M:%S')
    data_hora_display.short_description = 'Data/Hora'
    data_hora_display.admin_order_field = 'data_hora'


# ============================================
# HISTÓRICO DE EMAILS
# ============================================

@admin.register(HistoricoEmail)
class HistoricoEmailAdmin(admin.ModelAdmin):
    """Administração do histórico de emails"""

    list_display = (
        'id',
        'siape_servidor',
        'email_destinatario',
        'assunto_resumido',
        'status_badge',
        'data_solicitacao_display',
        'enviado_por',
    )

    list_filter = (
        'status',
        'data_solicitacao',
    )

    search_fields = (
        'servidor__siape',
        'servidor__nome_completo',
        'email_destinatario',
        'assunto',
    )

    readonly_fields = (
        'data_solicitacao',
        'data_envio',
    )

    ordering = ('-data_solicitacao',)

    list_per_page = 50

    fieldsets = (
        ('Destinatário', {
            'fields': (
                'servidor',
                'email_destinatario',
            )
        }),
        ('Conteúdo', {
            'fields': (
                'assunto',
                'corpo_email',
            )
        }),
        ('Status', {
            'fields': (
                'status',
                'data_solicitacao',
                'data_envio',
                'enviado_por',
            )
        }),
        ('Resposta', {
            'fields': (
                'resposta_api',
                'mensagem_erro',
            )
        }),
    )

    def siape_servidor(self, obj):
        return obj.servidor.siape
    siape_servidor.short_description = 'SIAPE'

    def assunto_resumido(self, obj):
        if len(obj.assunto) > 50:
            return obj.assunto[:50] + '...'
        return obj.assunto
    assunto_resumido.short_description = 'Assunto'

    def status_badge(self, obj):
        cores = {
            'PENDENTE': '#ffc107',
            'ENVIADO': '#28a745',
            'ERRO': '#dc3545',
        }
        cor = cores.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px;">{}</span>',
            cor, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def data_solicitacao_display(self, obj):
        return obj.data_solicitacao.strftime('%d/%m/%Y %H:%M')
    data_solicitacao_display.short_description = 'Solicitado em'
    data_solicitacao_display.admin_order_field = 'data_solicitacao'


# ============================================
# TEMPLATE DE EMAIL
# ============================================

@admin.register(TemplateEmail)
class TemplateEmailAdmin(admin.ModelAdmin):
    """Administração de templates de email"""

    list_display = (
        'id',
        'nome',
        'assunto',
        'ativo_badge',
        'data_criacao_display',
        'criado_por',
    )

    list_display_links = ('id', 'nome')

    list_filter = (
        'ativo',
        'data_criacao',
    )

    search_fields = (
        'nome',
        'descricao',
        'assunto',
    )

    readonly_fields = (
        'data_criacao',
        'data_alteracao',
    )

    ordering = ('nome',)

    list_per_page = 20

    fieldsets = (
        ('Identificação', {
            'fields': (
                'nome',
                'descricao',
                'ativo',
            )
        }),
        ('Conteúdo do Email', {
            'fields': (
                'assunto',
                'corpo_html',
            ),
            'description': '''
            <div style="background-color: #e7f3ff; padding: 15px; border-radius: 5px; margin: 10px 0;">
                <strong>Variáveis Disponíveis:</strong><br>
                <code>{{nome_servidor}}</code> - Nome completo do servidor<br>
                <code>{{siape}}</code> - SIAPE do servidor<br>
                <code>{{email}}</code> - Email do servidor<br>
                <code>{{total_tarefas}}</code> - Total de tarefas<br>
                <code>{{tarefas_criticas}}</code> - Total de tarefas críticas<br>
                <code>{{lista_tarefas}}</code> - Lista HTML com as tarefas<br>
                <code>{{data_hoje}}</code> - Data de hoje formatada
            </div>
            '''
        }),
        ('Auditoria', {
            'fields': (
                'data_criacao',
                'data_alteracao',
                'criado_por',
            ),
            'classes': ('collapse',)
        }),
    )

    def ativo_badge(self, obj):
        if obj.ativo:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; '
                'border-radius: 3px; font-weight: bold;">ATIVO</span>'
            )
        return format_html(
            '<span style="background-color: #6c757d; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">INATIVO</span>'
        )
    ativo_badge.short_description = 'Status'

    def data_criacao_display(self, obj):
        return obj.data_criacao.strftime('%d/%m/%Y %H:%M')
    data_criacao_display.short_description = 'Criado em'
    data_criacao_display.admin_order_field = 'data_criacao'

    def save_model(self, request, obj, form, change):
        """Salva o template com informações de auditoria"""
        if not change:
            obj.criado_por = request.user
        super().save_model(request, obj, form, change)
