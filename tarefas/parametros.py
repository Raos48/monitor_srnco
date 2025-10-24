"""
Modelo de Parâmetros para Análise de Criticidade de Tarefas
Permite configuração dinâmica dos prazos via Django Admin
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone


class ParametrosAnalise(models.Model):
    """
    Parâmetros configuráveis para análise de criticidade das tarefas.
    
    Este modelo permite que a chefia ajuste os prazos de análise sem
    modificar o código do sistema.
    
    Deve existir APENAS UM registro ativo no banco de dados.
    """
    
    # ============================================
    # REGRA 1: Exigência Cumprida - Aguardando Análise
    # ============================================
    prazo_analise_exigencia_cumprida = models.IntegerField(
        default=7,
        verbose_name="Prazo para Análise de Exigência Cumprida (dias)",
        help_text="Prazo que o servidor tem para analisar uma exigência após ela ser cumprida. "
                  "Padrão: 7 dias. REGRA 1."
    )
    
    # ============================================
    # REGRA 2: Cumprimento de Exigência pelo Segurado
    # ============================================
    prazo_tolerancia_exigencia = models.IntegerField(
        default=5,
        verbose_name="Tolerância Adicional para Cumprimento de Exigência (dias)",
        help_text="Dias adicionais após a data do prazo para o segurado cumprir a exigência. "
                  "Padrão: 5 dias. REGRA 2."
    )
    
    prazo_servidor_apos_vencimento = models.IntegerField(
        default=7,
        verbose_name="Prazo do Servidor Após Vencimento da Exigência (dias)",
        help_text="Prazo que o servidor tem para concluir a tarefa após vencimento da exigência. "
                  "Padrão: 7 dias. REGRA 2."
    )
    
    # ============================================
    # REGRAS 3 e 4: Primeira Ação do Servidor
    # ============================================
    prazo_primeira_acao = models.IntegerField(
        default=10,
        verbose_name="Prazo para Primeira Ação (dias)",
        help_text="Prazo que o servidor tem para realizar a primeira ação em uma tarefa. "
                  "Padrão: 10 dias. REGRAS 3 e 4."
    )
    
    # ============================================
    # Metadados
    # ============================================
    ativo = models.BooleanField(
        default=True,
        verbose_name="Configuração Ativa",
        help_text="Indica se esta é a configuração ativa do sistema. "
                  "Deve haver apenas UMA configuração ativa."
    )
    
    data_criacao = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Criação"
    )
    
    data_atualizacao = models.DateTimeField(
        auto_now=True,
        verbose_name="Última Atualização"
    )
    
    usuario_atualizacao = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Usuário que Atualizou",
        help_text="Nome do usuário que fez a última atualização"
    )
    
    observacoes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observações",
        help_text="Motivo da alteração dos parâmetros ou observações gerais"
    )
    
    class Meta:
        verbose_name = "Configuração de Prazos"
        verbose_name_plural = "Configurações de Prazos"
        ordering = ['-ativo', '-data_atualizacao']
    
    def __str__(self):
        status = "ATIVA" if self.ativo else "Inativa"
        return f"Configuração de Prazos ({status}) - Atualizada em {self.data_atualizacao.strftime('%d/%m/%Y %H:%M')}"
    
    def clean(self):
        """
        Validações customizadas do modelo
        """
        # Validar que valores são positivos
        if self.prazo_analise_exigencia_cumprida < 1:
            raise ValidationError({
                'prazo_analise_exigencia_cumprida': 'O prazo deve ser maior que zero.'
            })
        
        if self.prazo_tolerancia_exigencia < 0:
            raise ValidationError({
                'prazo_tolerancia_exigencia': 'A tolerância não pode ser negativa.'
            })
        
        if self.prazo_servidor_apos_vencimento < 1:
            raise ValidationError({
                'prazo_servidor_apos_vencimento': 'O prazo deve ser maior que zero.'
            })
        
        if self.prazo_primeira_acao < 1:
            raise ValidationError({
                'prazo_primeira_acao': 'O prazo deve ser maior que zero.'
            })
        
        # Validar que existe apenas uma configuração ativa
        if self.ativo:
            qs = ParametrosAnalise.objects.filter(ativo=True)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            
            if qs.exists():
                raise ValidationError({
                    'ativo': 'Já existe uma configuração ativa. Desative a configuração anterior antes de ativar esta.'
                })
    
    def save(self, *args, **kwargs):
        """
        Sobrescreve o save para garantir validações
        """
        self.full_clean()
        super().save(*args, **kwargs)
    
    @classmethod
    def get_configuracao_ativa(cls):
        """
        Retorna a configuração ativa do sistema.
        Se não existir nenhuma, cria uma com valores padrão.
        
        Returns:
            ParametrosAnalise: Configuração ativa
        """
        try:
            return cls.objects.get(ativo=True)
        except cls.DoesNotExist:
            # Cria configuração padrão
            config = cls.objects.create(
                ativo=True,
                prazo_analise_exigencia_cumprida=7,
                prazo_tolerancia_exigencia=5,
                prazo_servidor_apos_vencimento=7,
                prazo_primeira_acao=10,
                observacoes="Configuração criada automaticamente com valores padrão"
            )
            return config
        except cls.MultipleObjectsReturned:
            # Se houver mais de uma ativa (não deveria acontecer), retorna a mais recente
            return cls.objects.filter(ativo=True).order_by('-data_atualizacao').first()
    
    @property
    def prazo_total_exigencia(self):
        """
        Calcula o prazo total que o segurado tem para cumprir uma exigência
        (prazo base + tolerância)
        """
        return self.prazo_tolerancia_exigencia
    
    @property
    def prazo_total_servidor_exigencia(self):
        """
        Calcula o prazo total incluindo o tempo do servidor após vencimento
        """
        return self.prazo_tolerancia_exigencia + self.prazo_servidor_apos_vencimento
    
    def desativar(self):
        """
        Desativa esta configuração
        """
        self.ativo = False
        self.save()
    
    def ativar(self):
        """
        Ativa esta configuração (e desativa todas as outras)
        """
        # Desativa todas as outras
        ParametrosAnalise.objects.filter(ativo=True).update(ativo=False)
        
        # Ativa esta
        self.ativo = True
        self.save()
    
    def duplicar(self):
        """
        Cria uma cópia desta configuração (inativa)
        Útil para criar novas configurações baseadas em anteriores
        """
        nova_config = ParametrosAnalise(
            prazo_analise_exigencia_cumprida=self.prazo_analise_exigencia_cumprida,
            prazo_tolerancia_exigencia=self.prazo_tolerancia_exigencia,
            prazo_servidor_apos_vencimento=self.prazo_servidor_apos_vencimento,
            prazo_primeira_acao=self.prazo_primeira_acao,
            ativo=False,
            observacoes=f"Duplicada da configuração de {self.data_atualizacao.strftime('%d/%m/%Y %H:%M')}"
        )
        nova_config.save()
        return nova_config
    
    def get_resumo_prazos(self):
        """
        Retorna um dicionário com resumo de todos os prazos
        Útil para exibição em dashboards
        """
        return {
            'regra_1': {
                'nome': 'Exigência Cumprida - Análise',
                'prazo': self.prazo_analise_exigencia_cumprida,
                'unidade': 'dias'
            },
            'regra_2_tolerancia': {
                'nome': 'Tolerância para Cumprimento',
                'prazo': self.prazo_tolerancia_exigencia,
                'unidade': 'dias'
            },
            'regra_2_servidor': {
                'nome': 'Servidor Após Vencimento',
                'prazo': self.prazo_servidor_apos_vencimento,
                'unidade': 'dias'
            },
            'regra_3_4': {
                'nome': 'Primeira Ação do Servidor',
                'prazo': self.prazo_primeira_acao,
                'unidade': 'dias'
            }
        }


class HistoricoAlteracaoPrazos(models.Model):
    """
    Modelo para registrar histórico de alterações nos prazos.
    Útil para auditoria e acompanhamento de mudanças.
    """
    
    configuracao = models.ForeignKey(
        ParametrosAnalise,
        on_delete=models.CASCADE,
        related_name='historico_alteracoes',
        verbose_name="Configuração"
    )
    
    data_alteracao = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data da Alteração"
    )
    
    usuario = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Usuário"
    )
    
    campo_alterado = models.CharField(
        max_length=100,
        verbose_name="Campo Alterado"
    )
    
    valor_anterior = models.IntegerField(
        verbose_name="Valor Anterior"
    )
    
    valor_novo = models.IntegerField(
        verbose_name="Valor Novo"
    )
    
    motivo = models.TextField(
        blank=True,
        null=True,
        verbose_name="Motivo da Alteração"
    )
    
    class Meta:
        verbose_name = "Histórico de Alteração de Prazo"
        verbose_name_plural = "Histórico de Alterações de Prazos"
        ordering = ['-data_alteracao']
    
    def __str__(self):
        return f"{self.campo_alterado}: {self.valor_anterior} → {self.valor_novo} em {self.data_alteracao.strftime('%d/%m/%Y %H:%M')}"