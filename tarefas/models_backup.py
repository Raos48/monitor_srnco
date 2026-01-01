from django.db import models
from django.conf import settings
from datetime import date, timedelta
from .parametros import ParametrosAnalise, HistoricoAlteracaoPrazos
from .analisador import obter_analisador


class Tarefa(models.Model):
    # Campo protocolo como CharField
    numero_protocolo_tarefa = models.CharField(
        max_length=20,
        primary_key=True,
        verbose_name="Número do Protocolo"
    )
    
    indicador_subtarefas_pendentes = models.IntegerField()
    codigo_unidade_tarefa = models.IntegerField()
    nome_servico = models.CharField(max_length=255)
    status_tarefa = models.CharField(max_length=100)
    descricao_cumprimento_exigencia_tarefa = models.TextField(blank=True, null=True)
    
    # Relacionamento com usuário (FK)
    siape_responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tarefas_sob_responsabilidade',
        to_field='siape',
        db_column='siape_responsavel'
    )
    
    cpf_responsavel = models.CharField(max_length=14, blank=True, null=True, verbose_name="CPF do Responsável")
    nome_profissional_responsavel = models.CharField(max_length=255, blank=True, null=True)
    codigo_gex_responsavel = models.CharField(max_length=10, blank=True, null=True)
    nome_gex_responsavel = models.CharField(max_length=255, blank=True, null=True)
    
    # Datas
    data_distribuicao_tarefa = models.DateField(blank=True, null=True)
    data_ultima_atualizacao = models.DateField(blank=True, null=True)
    data_prazo = models.DateField(blank=True, null=True, verbose_name="Data do Prazo")
    data_inicio_ultima_exigencia = models.DateField(blank=True, null=True, verbose_name="Data de Início da Última Exigência")
    data_fim_ultima_exigencia = models.DateField(blank=True, null=True)
    data_processamento_tarefa = models.DateTimeField(blank=True, null=True)
    
    # Indicadores
    indicador_tarefa_reaberta = models.IntegerField(default=0, verbose_name="Indicador de Tarefa Reaberta")
    
    # Tempos
    tempo_ultima_exigencia_em_dias = models.IntegerField(blank=True, null=True)
    tempo_em_pendencia_em_dias = models.IntegerField(default=0)
    tempo_em_exigencia_em_dias = models.IntegerField(default=0)
    tempo_ate_ultima_distribuicao_tarefa_em_dias = models.IntegerField(default=0)

    # ============================================
    # NOVOS CAMPOS: CRITICIDADE CALCULADA (OTIMIZAÇÃO)
    # ============================================
    
    nivel_criticidade_calculado = models.CharField(
        max_length=10,
        choices=[
            ('CRÍTICA', 'Crítica'),
            ('REGULAR', 'Regular'),
        ],
        default='REGULAR',
        db_index=True,
        verbose_name='Nível de Criticidade (Calculado)'
    )
    
    regra_aplicada_calculado = models.CharField(
        max_length=20,
        default='NENHUMA',
        db_index=True,
        verbose_name='Regra Aplicada (Calculado)'
    )
    
    alerta_criticidade_calculado = models.TextField(
        blank=True,
        default='',
        verbose_name='Alerta de Criticidade (Calculado)'
    )
    
    descricao_criticidade_calculado = models.TextField(
        blank=True,
        default='',
        verbose_name='Descrição Detalhada (Calculado)'
    )
    
    dias_pendente_criticidade_calculado = models.IntegerField(
        default=0,
        verbose_name='Dias Pendente (Calculado)'
    )
    
    prazo_limite_criticidade_calculado = models.IntegerField(
        default=0,
        verbose_name='Prazo Limite (Calculado)'
    )
    
    pontuacao_criticidade = models.IntegerField(
        default=0,
        db_index=True,
        verbose_name='Pontuação para Ordenação'
    )
    
    cor_criticidade_calculado = models.CharField(
        max_length=7,
        default='#6c757d',
        verbose_name='Cor (Calculado)'
    )
    
    data_calculo_criticidade = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Data do Último Cálculo'
    )

    class Meta:
        ordering = ['-data_distribuicao_tarefa']
        verbose_name = 'Tarefa'
        verbose_name_plural = 'Tarefas'
        indexes = [
            models.Index(fields=['status_tarefa']),
            models.Index(fields=['siape_responsavel']),
            models.Index(fields=['data_distribuicao_tarefa']),
            models.Index(fields=['data_prazo']),
            models.Index(fields=['indicador_tarefa_reaberta']),
            # Novos índices para otimização
            models.Index(fields=['nivel_criticidade_calculado']),
            models.Index(fields=['pontuacao_criticidade']),
        ]

    def __str__(self):
        return f"{self.nome_servico} ({self.numero_protocolo_tarefa})"

    # ============================================
    # PROPRIEDADES PARA CÁLCULO DE ALERTAS
    # ============================================
    
    @property
    def dias_com_servidor(self):
        """
        Calcula há quantos dias a tarefa está com o servidor atual.
        Fórmula: tempo_ate_ultima_distribuicao - tempo_em_pendencia
        """
        if self.tempo_ate_ultima_distribuicao_tarefa_em_dias is None:
            return 0
        return self.tempo_ate_ultima_distribuicao_tarefa_em_dias - self.tempo_em_pendencia_em_dias

    @property
    def tem_subtarefa_pendente(self):
        """Verifica se possui subtarefa pendente (não deve gerar alerta)"""
        return self.indicador_subtarefas_pendentes > 0
    
    @property
    def foi_reaberta(self):
        """Verifica se a tarefa foi reaberta"""
        return self.indicador_tarefa_reaberta == 1
    
    @property
    def dias_ate_prazo(self):
        """
        Calcula quantos dias faltam até o prazo (ou quantos dias já passou).
        Retorna None se não houver prazo definido.
        Positivo = ainda há dias, Negativo = prazo vencido
        """
        if not self.data_prazo:
            return None
        return (self.data_prazo - date.today()).days
    
    @property
    def prazo_vencido(self):
        """Verifica se o prazo da tarefa já venceu"""
        if not self.data_prazo:
            return False
        return date.today() > self.data_prazo

    @property
    def alerta_tipo_1_pendente_sem_movimentacao(self):
        """
        REGRA 1: Tarefa pendente sem movimentação há mais de 10 dias
        
        Condições:
        - Status = 'Pendente'
        - Nunca entrou em exigência
        - Tempo com servidor > 10 dias
        - SEM subtarefa pendente
        """
        if self.tem_subtarefa_pendente:
            return False
            
        return (
            self.status_tarefa == 'Pendente' and
            self.descricao_cumprimento_exigencia_tarefa == 'Nunca entrou em exigência' and
            self.dias_com_servidor > 10
        )

    @property
    def alerta_tipo_2_exigencia_vencida(self):
        """
        REGRA 2: Exigência não cumprida após prazo legal + prazo para análise
        
        Condições:
        - Status contém 'Exigência' ou 'exigência'
        - Tempo em exigência > 42 dias (35 + 7)
        - SEM subtarefa pendente
        """
        if self.tem_subtarefa_pendente:
            return False
            
        status_lower = self.status_tarefa.lower() if self.status_tarefa else ''
        
        return (
            'exigência' in status_lower and
            self.tempo_em_exigencia_em_dias > 42
        )

    @property
    def alerta_tipo_3_exigencia_cumprida_pendente(self):
        """
        REGRA 3: Exigência cumprida aguardando análise há mais de 7 dias
        
        Condições:
        - Descrição = 'Exigência cumprida'
        - Possui data_fim_ultima_exigencia
        - Passou mais de 7 dias desde o cumprimento
        - SEM subtarefa pendente
        """
        if self.tem_subtarefa_pendente:
            return False
            
        if not self.data_fim_ultima_exigencia:
            return False
            
        if self.descricao_cumprimento_exigencia_tarefa != 'Exigência cumprida':
            return False
        
        # Calcula dias desde o cumprimento
        dias_desde_cumprimento = (date.today() - self.data_fim_ultima_exigencia).days
        
        return dias_desde_cumprimento > 7

    @property
    def tipo_alerta(self):
        """
        Retorna o tipo de alerta da tarefa ou None se não houver alerta.
        
        Retornos possíveis:
        - 'PENDENTE_SEM_MOVIMENTACAO' (Tipo 1)
        - 'EXIGENCIA_VENCIDA' (Tipo 2)
        - 'EXIGENCIA_CUMPRIDA_PENDENTE' (Tipo 3)
        - None (sem alerta)
        """
        if self.alerta_tipo_1_pendente_sem_movimentacao:
            return 'PENDENTE_SEM_MOVIMENTACAO'
        elif self.alerta_tipo_2_exigencia_vencida:
            return 'EXIGENCIA_VENCIDA'
        elif self.alerta_tipo_3_exigencia_cumprida_pendente:
            return 'EXIGENCIA_CUMPRIDA_PENDENTE'
        return None

    @property
    def tem_alerta(self):
        """Verifica se a tarefa possui qualquer tipo de alerta"""
        return self.tipo_alerta is not None

    @property
    def descricao_alerta(self):
        """Retorna descrição amigável do alerta"""
        tipo = self.tipo_alerta
        if tipo == 'PENDENTE_SEM_MOVIMENTACAO':
            return f'Tarefa pendente há {self.dias_com_servidor} dias sem movimentação'
        elif tipo == 'EXIGENCIA_VENCIDA':
            return f'Exigência há {self.tempo_em_exigencia_em_dias} dias sem conclusão'
        elif tipo == 'EXIGENCIA_CUMPRIDA_PENDENTE':
            dias = (date.today() - self.data_fim_ultima_exigencia).days
            return f'Exigência cumprida há {dias} dias aguardando análise'
        return ''
    
    # ============================================
    # SISTEMA DE CRITICIDADE (OTIMIZADO)
    # ============================================
    
    def _obter_analise_criticidade(self):
        """
        VERSÃO OTIMIZADA: Retorna dados JÁ CALCULADOS do banco.
        
        Se os campos calculados estiverem vazios, calcula em tempo real
        (fallback para compatibilidade).
        """
        # Se já foi calculado, usa o valor do banco (RÁPIDO!)
        if self.nivel_criticidade_calculado != 'NENHUMA' or self.data_calculo_criticidade:
            return {
                'regra': self.regra_aplicada_calculado,
                'alerta': self.alerta_criticidade_calculado,
                'severidade': self.nivel_criticidade_calculado,
                'dias_pendente': self.dias_pendente_criticidade_calculado,
                'prazo_limite': self.prazo_limite_criticidade_calculado,
                'detalhes': self.descricao_criticidade_calculado
            }
        
        # Fallback: calcula em tempo real (apenas para tarefas antigas)
        if not hasattr(self, '_cache_analise'):
            analisador = obter_analisador()
            self._cache_analise = analisador.analisar_tarefa(self)
        
        return self._cache_analise

    def calcular_e_salvar_criticidade(self):
        """
        Calcula a criticidade e salva nos campos do banco.
        
        Este método deve ser chamado:
        - Na importação de CSV
        - Em comandos de recálculo em lote
        
        Returns:
            dict: Resultado da análise
        """
        # ✅ CORREÇÃO: Importar timezone do Django
        from django.utils import timezone
        from .analisador import obter_analisador
        
        # Executar análise
        analisador = obter_analisador()
        resultado = analisador.analisar_tarefa(self)
        
        # Salvar nos campos calculados
        self.nivel_criticidade_calculado = resultado['severidade']
        self.regra_aplicada_calculado = resultado['regra']
        self.alerta_criticidade_calculado = resultado['alerta']
        self.descricao_criticidade_calculado = resultado['detalhes']
        self.dias_pendente_criticidade_calculado = resultado['dias_pendente']
        self.prazo_limite_criticidade_calculado = resultado['prazo_limite']
        
        # Calcular pontuação para ordenação
        ordem_severidade = {
            'CRÍTICA': 5,
            'ALTA': 4,
            'MÉDIA': 3,
            'BAIXA': 2,
            'NENHUMA': 1
        }
        self.pontuacao_criticidade = ordem_severidade.get(resultado['severidade'], 0)
        
        # Definir cor
        cores = {
            'CRÍTICA': '#dc3545',
            'ALTA': '#fd7e14',
            'MÉDIA': '#ffc107',
            'BAIXA': '#28a745',
            'NENHUMA': '#6c757d'
        }
        self.cor_criticidade_calculado = cores.get(resultado['severidade'], '#6c757d')
        
        # ✅ CORREÇÃO: Usar timezone.now() em vez de datetime.now()
        self.data_calculo_criticidade = timezone.now()
        
        # Salvar sem triggerar signals
        self.save(update_fields=[
            'nivel_criticidade_calculado',
            'regra_aplicada_calculado',
            'alerta_criticidade_calculado',
            'descricao_criticidade_calculado',
            'dias_pendente_criticidade_calculado',
            'prazo_limite_criticidade_calculado',
            'pontuacao_criticidade',
            'cor_criticidade_calculado',
            'data_calculo_criticidade'
        ])
        
        return resultado



    # ============================================
    # PROPERTIES DE CRITICIDADE (mantidas para compatibilidade)
    # ============================================
    
    @property
    def nivel_criticidade(self):
        """Retorna o nível de criticidade da tarefa"""
        return self._obter_analise_criticidade()['severidade']
    
    @property
    def regra_aplicada(self):
        """Retorna qual regra foi aplicada"""
        return self._obter_analise_criticidade()['regra']
    
    @property
    def alerta_criticidade(self):
        """Retorna o alerta de criticidade"""
        return self._obter_analise_criticidade()['alerta']
    
    @property
    def descricao_criticidade(self):
        """Retorna descrição detalhada da criticidade"""
        return self._obter_analise_criticidade()['detalhes']
    
    @property
    def dias_pendente_criticidade(self):
        """Retorna quantos dias a tarefa está em situação irregular"""
        return self._obter_analise_criticidade()['dias_pendente']
    
    @property
    def prazo_limite_criticidade(self):
        """Retorna o prazo limite estabelecido"""
        return self._obter_analise_criticidade()['prazo_limite']
    
    @property
    def tem_criticidade(self):
        """Verifica se a tarefa está crítica (prazo estourado)"""
        return self.nivel_criticidade_calculado == 'CRÍTICA'
    
    @property
    def cor_criticidade(self):
        """Retorna a cor hexadecimal do nível de criticidade"""
        cores = {
            'CRÍTICA': '#dc3545',  # Vermelho
            'REGULAR': '#28a745',   # Verde
        }
        return cores.get(self.nivel_criticidade_calculado, '#28a745')
    
    @property
    def emoji_criticidade(self):
        """Retorna emoji representando o nível de criticidade"""
        emojis = {
            'CRÍTICA': '⛔',
            'REGULAR': '✅',
        }
        return emojis.get(self.nivel_criticidade_calculado, '✅')
    
    @property
    def badge_html_criticidade(self):
        """Retorna HTML pronto de um badge Bootstrap"""
        badges = {
            'CRÍTICA': 'bg-danger',
            'REGULAR': 'bg-success',
        }
        css_class = badges.get(self.nivel_criticidade_calculado, 'bg-success')
        emoji = self.emoji_criticidade
        nivel = self.nivel_criticidade_calculado
        
        return f'<span class="badge {css_class}">{emoji} {nivel}</span>'
    
    @property
    def resumo_criticidade(self):
        """Retorna um dicionário com resumo completo da criticidade"""
        return {
            'nivel': self.nivel_criticidade,
            'regra': self.regra_aplicada,
            'alerta': self.alerta_criticidade,
            'descricao': self.descricao_criticidade,
            'dias_pendente': self.dias_pendente_criticidade,
            'prazo_limite': self.prazo_limite_criticidade,
            'tem_criticidade': self.tem_criticidade,
            'cor': self.cor_criticidade,
            'emoji': self.emoji_criticidade
        }
    
    # ============================================
    # MÉTODOS DE COMPARAÇÃO DE CRITICIDADE
    # ============================================
    
    def eh_mais_critica_que(self, outra_tarefa):
        """Compara o nível de criticidade com outra tarefa"""
        ordem_severidade = {
            'CRÍTICA': 5,
            'ALTA': 4,
            'MÉDIA': 3,
            'BAIXA': 2,
            'NENHUMA': 1
        }
        
        peso_esta = ordem_severidade.get(self.nivel_criticidade, 0)
        peso_outra = ordem_severidade.get(outra_tarefa.nivel_criticidade, 0)
        
        return peso_esta > peso_outra
    
    @classmethod
    def ordenar_por_criticidade(cls, tarefas):
        """
        VERSÃO OTIMIZADA: Ordena usando pontuacao_criticidade (índice no BD).
        """
        # Se for QuerySet, usar order_by do banco (SUPER RÁPIDO!)
        if hasattr(tarefas, 'order_by'):
            return tarefas.order_by('-pontuacao_criticidade', '-tempo_em_pendencia_em_dias')
        
        # Se for lista, ordenar em memória (compatibilidade)
        ordem_severidade = {
            'CRÍTICA': 5,
            'ALTA': 4,
            'MÉDIA': 3,
            'BAIXA': 2,
            'NENHUMA': 1
        }
        
        return sorted(
            tarefas,
            key=lambda t: (
                t.pontuacao_criticidade if hasattr(t, 'pontuacao_criticidade') and t.pontuacao_criticidade 
                else ordem_severidade.get(t.nivel_criticidade, 0)
            ),
            reverse=True
        )

    @classmethod
    def estatisticas_criticidade(cls, queryset=None):
        """
        VERSÃO OTIMIZADA: Usa aggregate do Django (consulta SQL única).
        """
        from django.db.models import Count, Q
        
        if queryset is None:
            queryset = cls.objects.all()
        
        # Consulta SQL única com aggregate (SUPER RÁPIDO!)
        stats = queryset.aggregate(
            total=Count('numero_protocolo_tarefa'),
            criticas=Count('numero_protocolo_tarefa', filter=Q(nivel_criticidade_calculado='CRÍTICA')),
            altas=Count('numero_protocolo_tarefa', filter=Q(nivel_criticidade_calculado='ALTA')),
            medias=Count('numero_protocolo_tarefa', filter=Q(nivel_criticidade_calculado='MÉDIA')),
            baixas=Count('numero_protocolo_tarefa', filter=Q(nivel_criticidade_calculado='BAIXA')),
            normais=Count('numero_protocolo_tarefa', filter=Q(nivel_criticidade_calculado='NENHUMA'))
        )
        
        # Formatar resultado
        estatisticas = {
            'total': stats['total'],
            'CRÍTICA': stats['criticas'],
            'ALTA': stats['altas'],
            'MÉDIA': stats['medias'],
            'BAIXA': stats['baixas'],
            'NENHUMA': stats['normais'],
            'com_criticidade': stats['criticas'] + stats['altas'] + stats['medias'] + stats['baixas'],
            'sem_criticidade': stats['normais']
        }
        
        # Adicionar percentuais
        if estatisticas['total'] > 0:
            for nivel in ['CRÍTICA', 'ALTA', 'MÉDIA', 'BAIXA', 'NENHUMA']:
                count = estatisticas[nivel]
                estatisticas[f'percentual_{nivel}'] = round(
                    (count / estatisticas['total']) * 100, 1
                )
        
                # Versão SIMPLIFICADA
        from django.db.models import Count, Q
        
        if queryset is None:
            queryset = cls.objects.all()
        
        # Consulta SQL simplificada
        stats = queryset.aggregate(
            total=Count('numero_protocolo_tarefa'),
            criticas=Count('numero_protocolo_tarefa', filter=Q(nivel_criticidade_calculado='CRÍTICA')),
            regulares=Count('numero_protocolo_tarefa', filter=Q(nivel_criticidade_calculado='REGULAR'))
        )
        
        estatisticas = {
            'total': stats['total'],
            'criticas': stats['criticas'],
            'regulares': stats['regulares'],
        }
        
        # Calcular percentuais
        if estatisticas['total'] > 0:
            estatisticas['percentual_criticas'] = round(
                (stats['criticas'] / stats['total']) * 100, 1
            )
            estatisticas['percentual_regulares'] = round(
                (stats['regulares'] / stats['total']) * 100, 1
            )
        
        return estatisticas
    
    @classmethod
    def tarefas_por_criticidade(cls, nivel, queryset=None):
        """
        VERSÃO OTIMIZADA: Usa filter do Django (consulta SQL).
        """
        if queryset is None:
            queryset = cls.objects.all()
        
        # Filter direto no banco (RÁPIDO!)
        return queryset.filter(nivel_criticidade_calculado=nivel)


class NotificacaoEmail(models.Model):
    tipo = models.CharField(max_length=20)
    assunto = models.CharField(max_length=255)
    mensagem = models.TextField()
    enviado_em = models.DateTimeField(auto_now_add=True)
    sucesso = models.BooleanField()
    erro = models.TextField(blank=True, null=True)
    
    destinatario = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        models.DO_NOTHING,
        related_name='notificacoes_recebidas'
    )
    remetente = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        models.DO_NOTHING, 
        related_name='notificacoes_enviadas',
        blank=True, 
        null=True
    )
    
    class Meta:
        verbose_name = 'Notificação de Email'
        verbose_name_plural = 'Notificações de Email'
        ordering = ['-enviado_em']