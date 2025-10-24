from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.utils.html import format_html
from .models import CustomUser, EmailServidor


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    """
    Administração customizada para o modelo CustomUser.
    Permite gerenciar usuários com SIAPE, CPF, GEX, etc.
    Exibe alertas para cadastros incompletos.
    """
    
    # Campos exibidos na listagem
    list_display = (
        'siape',
        'nome_completo',
        'email_display',
        'cpf',
        'gex',
        'status_cadastro_badge',
        'is_active',
        'is_staff',
        'get_groups',
        'date_joined'
    )
    
    # Campos clicáveis na listagem
    list_display_links = ('siape', 'nome_completo')
    
    # Filtros laterais
    list_filter = (
        'is_active',
        'is_staff',
        'is_superuser',
        'groups',
        'gex',
        'date_joined'
    )
    
    # Campos de busca
    search_fields = (
        'siape',
        'nome_completo',
        'email',
        'cpf',
        'gex',
        'lotacao'
    )
    
    # Ordenação padrão
    ordering = ('-date_joined',)
    
    # Campos editáveis diretamente na listagem
    list_editable = ('is_active',)
    
    # Paginação
    list_per_page = 50
    
    # Organização dos campos no formulário de edição
    fieldsets = (
        ('⚠️ Status do Cadastro', {
            'fields': ('get_status_cadastro_display',),
            'classes': ('wide',)
        }),
        ('Informações de Autenticação', {
            'fields': ('email', 'password')
        }),
        ('Informações Pessoais', {
            'fields': ('nome_completo', 'siape', 'cpf')
        }),
        ('Informações Profissionais', {
            'fields': ('gex', 'lotacao')
        }),
        ('Permissões', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Datas Importantes', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    
    # Campos ao adicionar novo usuário
    add_fieldsets = (
        ('Criar Novo Usuário', {
            'classes': ('wide',),
            'fields': (
                'siape',
                'nome_completo',
                'cpf',
                'email',
                'gex',
                'lotacao',
                'password1',
                'password2',
                'is_active',
                'is_staff',
                'groups'
            ),
            'description': 'E-mail é opcional. Se não informado, será criado um e-mail temporário.'
        }),
    )
    
    # Campos somente leitura
    readonly_fields = ('last_login', 'date_joined', 'get_status_cadastro_display')
    
    # Ações em massa customizadas
    actions = [
        'ativar_usuarios',
        'desativar_usuarios',
        'adicionar_ao_grupo_servidor',
        'listar_usuarios_sem_email'
    ]
    
    def email_display(self, obj):
        """Exibe o e-mail com alerta se for temporário"""
        if not obj.tem_email_real:
            return format_html(
                '<span style="color: red; font-weight: bold;">⚠️ SEM E-MAIL</span>'
            )
        return obj.email
    email_display.short_description = 'E-mail'
    
    def status_cadastro_badge(self, obj):
        """Exibe badge colorido com status do cadastro"""
        if obj.cadastro_completo:
            return format_html(
                '<span style="background-color: green; color: white; padding: 3px 10px; border-radius: 3px;">✓ Completo</span>'
            )
        else:
            return format_html(
                '<span style="background-color: orange; color: white; padding: 3px 10px; border-radius: 3px;">⚠ Incompleto</span>'
            )
    status_cadastro_badge.short_description = 'Status'
    
    def get_status_cadastro_display(self, obj):
        """Exibe alerta detalhado sobre o status do cadastro"""
        if obj.cadastro_completo:
            return format_html(
                '<div style="padding: 10px; background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 5px;">'
                '<strong style="color: #155724;">✓ Cadastro Completo</strong>'
                '</div>'
            )
        
        mensagens = []
        if not obj.tem_email_real:
            mensagens.append('❌ E-mail não cadastrado - usuário não pode fazer login')
        if not obj.cpf:
            mensagens.append('⚠️ CPF não cadastrado')
        
        return format_html(
            '<div style="padding: 10px; background-color: #fff3cd; border: 1px solid #ffc107; border-radius: 5px;">'
            '<strong style="color: #856404;">⚠️ CADASTRO INCOMPLETO</strong><br>'
            '<ul style="margin: 10px 0 0 0; padding-left: 20px;">{}</ul>'
            '</div>',
            format_html(''.join(f'<li>{msg}</li>' for msg in mensagens))
        )
    get_status_cadastro_display.short_description = 'Status do Cadastro'
    
    def get_groups(self, obj):
        """Exibe os grupos do usuário na listagem"""
        return ", ".join([group.name for group in obj.groups.all()])
    get_groups.short_description = 'Grupos'
    
    @admin.action(description='Ativar usuários selecionados')
    def ativar_usuarios(self, request, queryset):
        """Ativa múltiplos usuários de uma vez"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} usuário(s) ativado(s) com sucesso.')
    
    @admin.action(description='Desativar usuários selecionados')
    def desativar_usuarios(self, request, queryset):
        """Desativa múltiplos usuários de uma vez"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} usuário(s) desativado(s) com sucesso.')
    
    @admin.action(description='Adicionar ao grupo "Servidor"')
    def adicionar_ao_grupo_servidor(self, request, queryset):
        """Adiciona usuários ao grupo Servidor"""
        grupo_servidor, _ = Group.objects.get_or_create(name='Servidor')
        count = 0
        for user in queryset:
            if grupo_servidor not in user.groups.all():
                user.groups.add(grupo_servidor)
                count += 1
        self.message_user(request, f'{count} usuário(s) adicionado(s) ao grupo Servidor.')
    
    @admin.action(description='📋 Listar usuários SEM e-mail')
    def listar_usuarios_sem_email(self, request, queryset):
        """Lista usuários sem e-mail real"""
        usuarios_sem_email = [u for u in queryset if not u.tem_email_real]
        
        if not usuarios_sem_email:
            self.message_user(request, 'Todos os usuários selecionados possuem e-mail cadastrado.')
            return
        
        mensagem = f'📋 {len(usuarios_sem_email)} usuário(s) sem e-mail encontrado(s):<br><ul>'
        for user in usuarios_sem_email[:20]:  # Limita a 20 para não sobrecarregar
            mensagem += f'<li><strong>{user.siape}</strong> - {user.nome_completo}</li>'
        
        if len(usuarios_sem_email) > 20:
            mensagem += f'<li><em>... e mais {len(usuarios_sem_email) - 20} usuário(s)</em></li>'
        
        mensagem += '</ul>'
        
        from django.contrib import messages
        messages.warning(request, format_html(mensagem))


@admin.register(EmailServidor)
class EmailServidorAdmin(admin.ModelAdmin):
    """
    Administração para a tabela EmailServidor.
    Gerencia e-mails e SIAPEs dos servidores.
    """
    
    # Campos exibidos na listagem
    list_display = ('siape', 'email')
    
    # Campos de busca
    search_fields = ('siape', 'email')
    
    # Ordenação padrão
    ordering = ('siape',)
    
    # Paginação
    list_per_page = 100
    
    # Campos editáveis diretamente na listagem
    list_editable = ('email',)