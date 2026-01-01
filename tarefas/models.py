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
        max_length=15,  # Aumentado para suportar 'JUSTIFICADA' (12 caracteres)
        choices=[
            ('CRÍTICA', 'Crítica'),
            ('REGULAR', 'Regular'),
            ('JUSTIFICADA', 'Justificada'),
            ('EXCLUÍDA', 'Excluída'),
        ],
        default='REGULAR',
        db_index=True,
        verbose_name='Nível de Criticidade (Calculado)'
    )
    
    regra_aplicada_calculado = models.CharField(
        max_length=50,
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

    # ============================================
    # CAMPO: CONTROLE DE ARQUIVAMENTO
    # ============================================

    ativa = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name='Tarefa Ativa',
        help_text='False = tarefa arquivada (não aparece mais nos CSVs importados)'
    )

    # ============================================
    # NOVOS CAMPOS: SISTEMA DE JUSTIFICATIVAS
    # ============================================
    
    tem_justificativa_ativa = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name='Possui Justificativa Aprovada'
    )
    
    tem_solicitacao_ajuda = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name='Possui Solicitação de Ajuda'
    )
    
    servico_excluido_criticidade = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name='Serviço Excluído da Criticidade'
    )

    # ============================================
    # NOVO CAMPO: TIPO DE FILA
    # ============================================

    tipo_fila = models.CharField(
        max_length=50,
        default='OUTROS',
        db_index=True,
        verbose_name='Tipo de Fila',
        help_text='Classificação automática da tarefa em filas de trabalho'
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
            # OTIMIZAÇÃO: Índices compostos para queries frequentes do dashboard
            models.Index(fields=['ativa', 'siape_responsavel', 'tipo_fila']),  # Dashboard e listagens
            models.Index(fields=['ativa', 'tipo_fila', 'nivel_criticidade_calculado']),  # Estatísticas
            models.Index(fields=['data_processamento_tarefa']),  # Context processor
            models.Index(fields=['ativa', 'siape_responsavel']),  # Filtragem geral
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
        - Status = 'Exigência cumprida'
        - Tempo em pendência > 7 dias
        - SEM subtarefa pendente
        """
        if self.tem_subtarefa_pendente:
            return False
            
        return (
            self.status_tarefa == 'Exigência cumprida' and
            self.tempo_em_pendencia_em_dias > 7
        )

    @property
    def alerta_tipo_4_prazo_sistema_vencido(self):
        """
        REGRA 4: Prazo do sistema vencido

        Condições:
        - Status = 'Pendente'
        - Prazo do sistema vencido (dias_ate_prazo < 0)
        - SEM subtarefa pendente
        """
        if self.tem_subtarefa_pendente:
            return False

        return (
            self.status_tarefa == 'Pendente' and
            self.dias_ate_prazo is not None and
            self.dias_ate_prazo < 0
        )

    @property
    def tem_alerta(self):
        """
        Verifica se a tarefa possui algum tipo de alerta ativo.
        Retorna True se qualquer uma das 4 regras de alerta for verdadeira.
        """
        return (
            self.alerta_tipo_1_pendente_sem_movimentacao or
            self.alerta_tipo_2_exigencia_vencida or
            self.alerta_tipo_3_exigencia_cumprida_pendente or
            self.alerta_tipo_4_prazo_sistema_vencido
        )

    @property
    def tipo_alerta(self):
        """
        Retorna o tipo de alerta da tarefa (prioridade em ordem de criticidade).
        Se houver múltiplos alertas, retorna o mais crítico.
        Retorna None se não houver alertas.
        """
        # Prioridade: Exigência Vencida > Prazo Sistema Vencido > Sem Movimentação > Exigência Cumprida
        if self.alerta_tipo_2_exigencia_vencida:
            return 'EXIGENCIA_VENCIDA'
        if self.alerta_tipo_4_prazo_sistema_vencido:
            return 'PRAZO_SISTEMA_VENCIDO'
        if self.alerta_tipo_1_pendente_sem_movimentacao:
            return 'PENDENTE_SEM_MOVIMENTACAO'
        if self.alerta_tipo_3_exigencia_cumprida_pendente:
            return 'EXIGENCIA_CUMPRIDA_PENDENTE'

        return None
    
    # ============================================
    # PROPRIEDADES DE CRITICIDADE (CALCULADAS)
    # ============================================
    
    def _obter_analise_criticidade(self):
        """
        Método interno que busca análise do analisador de criticidade.
        Reutiliza resultado em cache para evitar múltiplas chamadas.
        """
        if not hasattr(self, '_cache_analise'):
            analisador = obter_analisador()
            self._cache_analise = analisador.analisar_tarefa(self)
        return self._cache_analise
    
    @property
    def nivel_criticidade(self):
        """Retorna o nível de criticidade da tarefa"""
        # Retorna valor calculado (já está no BD)
        return self.nivel_criticidade_calculado
    
    @property
    def regra_aplicada(self):
        """Retorna qual regra foi aplicada na análise"""
        return self.regra_aplicada_calculado

    @property
    def regra_aplicada_nome(self):
        """Retorna o nome amigável da regra aplicada"""
        from tarefas.analisador import obter_nome_regra_amigavel
        return obter_nome_regra_amigavel(self.regra_aplicada_calculado or 'SEM_REGRA')

    @property
    def alerta_criticidade(self):
        """Retorna mensagem de alerta principal"""
        return self.alerta_criticidade_calculado
    
    @property
    def descricao_criticidade(self):
        """Retorna descrição detalhada da criticidade"""
        return self.descricao_criticidade_calculado or ''
    
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
    # MÉTODO PARA CALCULAR E SALVAR CRITICIDADE
    # ============================================

    def calcular_criticidade(self):
        """
        Calcula a criticidade SEM salvar no banco.
        Otimizado para uso com bulk_update.

        Returns:
            dict: Dicionário com todos os campos calculados prontos para atribuição
        """
        from django.utils import timezone

        # Executar análise
        analisador = obter_analisador()
        resultado = analisador.analisar_tarefa(self)

        # Calcular pontuação para ordenação
        ordem_severidade = {
            'CRÍTICA': 5,
            'JUSTIFICADA': 4,
            'EXCLUÍDA': 3,
            'REGULAR': 2,
        }
        pontuacao = ordem_severidade.get(resultado['nivel'], 0)

        # Retorna dicionário com todos os campos calculados
        return {
            'nivel_criticidade_calculado': resultado['nivel'],
            'regra_aplicada_calculado': resultado['regra'],
            'alerta_criticidade_calculado': resultado['alerta'],
            'descricao_criticidade_calculado': resultado['descricao'],
            'dias_pendente_criticidade_calculado': resultado['dias_pendente'],
            'prazo_limite_criticidade_calculado': resultado['prazo_limite'],
            'pontuacao_criticidade': pontuacao,
            'cor_criticidade_calculado': resultado['cor'],
            'data_calculo_criticidade': timezone.now()
        }

    def calcular_e_salvar_criticidade(self):
        """
        MÉTODO LEGADO: Calcula a criticidade e salva nos campos do banco.

        Para operações em lote, prefira usar calcular_criticidade() + bulk_update.
        Este método é mantido para compatibilidade com código existente.

        Returns:
            dict: Resultado da análise
        """
        # Usa o novo método otimizado
        campos_calculados = self.calcular_criticidade()

        # Atribui os valores aos campos da instância
        for campo, valor in campos_calculados.items():
            setattr(self, campo, valor)

        # Salvar sem triggerar signals
        self.save(update_fields=list(campos_calculados.keys()))

        # Retorna resultado no formato antigo para compatibilidade
        analisador = obter_analisador()
        return analisador.analisar_tarefa(self)

    # ============================================
    # MÉTODO PARA CLASSIFICAR TIPO DE FILA
    # ============================================

    def classificar_fila(self):
        """
        Classifica a tarefa em uma fila de trabalho baseado em configurações do banco de dados.

        NOVO SISTEMA CONFIGURÁVEL:
        - Consulta o modelo ConfiguracaoFila para determinar a fila
        - Totalmente gerenciável via Django Admin
        - Regra especial: PGB é baseada apenas em codigo_unidade = 23150003
        - Fallback: Se não encontrar configuração, retorna 'OUTROS'

        Returns:
            str: Código da fila identificada
        """

        # Regra especial: PGB (baseada apenas no código da unidade)
        if self.codigo_unidade_tarefa == 23150003:
            return 'PGB'

        # Obter nome do serviço normalizado
        servico = self.nome_servico.strip() if self.nome_servico else ''

        # Consultar configuração do banco de dados
        try:
            fila_configurada = ConfiguracaoFila.obter_fila_para_servico(
                nome_servico=servico,
                codigo_unidade=self.codigo_unidade_tarefa
            )

            if fila_configurada:
                return fila_configurada

        except Exception:
            # Se houver erro (ex: tabela ainda não existe durante migrations), ignora
            pass

        # Fallback: Se não encontrar configuração, retorna OUTROS
        return 'OUTROS'

    def calcular_e_salvar_tipo_fila(self):
        """
        Calcula e salva o tipo de fila da tarefa.

        Returns:
            str: Tipo de fila identificado
        """
        self.tipo_fila = self.classificar_fila()
        self.save(update_fields=['tipo_fila'])
        return self.tipo_fila

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



    def atualizar_flags_justificativa(self):
        """Atualiza flags de justificativas e serviços"""
        self.tem_justificativa_ativa = self.justificativas.filter(
            status='APROVADA'
        ).exists()

        self.tem_solicitacao_ajuda = self.solicitacoes_ajuda.filter(
            status__in=['PENDENTE', 'EM_ATENDIMENTO']
        ).exists()

        # Verificar se o serviço está excluído da análise de criticidade
        # Importação dinâmica para evitar problemas de ordem de definição
        try:
            from tarefas.models import ServicosCriticidade
            servico_config = ServicosCriticidade.objects.get(
                nome_servico=self.nome_servico
            )
            self.servico_excluido_criticidade = servico_config.excluido_criticidade
        except Exception:
            # Captura qualquer exceção (DoesNotExist ou erro de importação)
            self.servico_excluido_criticidade = False

    def pode_submeter_justificativa(self):
        """Verifica se pode submeter justificativa"""
        return not self.justificativas.filter(
            status__in=['PENDENTE', 'APROVADA']
        ).exists()

    @property
    def justificativa_ativa(self):
        """Retorna justificativa aprovada"""
        return self.justificativas.filter(status='APROVADA').first()


# ============================================
# NOVOS MODELS: SISTEMA DE JUSTIFICATIVAS
# ============================================

class TipoJustificativa(models.Model):
    """
    Tipos predefinidos de justificativas que um servidor pode usar.
    Exemplos: Problema Sistêmico, Aguardando Adequação, etc.
    """
    nome = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Nome do Tipo'
    )
    descricao = models.TextField(
        verbose_name='Descrição',
        help_text='Explicação detalhada sobre quando usar este tipo'
    )
    ativo = models.BooleanField(
        default=True,
        verbose_name='Ativo',
        help_text='Se desmarcado, não aparecerá como opção'
    )
    ordem_exibicao = models.IntegerField(
        default=0,
        verbose_name='Ordem de Exibição',
        help_text='Ordem em que aparece na lista (menor = primeiro)'
    )
    
    class Meta:
        verbose_name = 'Tipo de Justificativa'
        verbose_name_plural = 'Tipos de Justificativas'
        ordering = ['ordem_exibicao', 'nome']
    
    def __str__(self):
        return self.nome


class Justificativa(models.Model):
    """
    Justificativas submetidas por servidores para tarefas críticas.
    Aprovadas pela Equipe Volante, fazem a tarefa não contar como crítica.
    """
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente de Análise'),
        ('APROVADA', 'Aprovada'),
        ('REPROVADA', 'Reprovada'),
    ]
    
    tarefa = models.ForeignKey(
        'Tarefa',
        on_delete=models.CASCADE,
        related_name='justificativas',
        verbose_name='Tarefa'
    )
    servidor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='justificativas_submetidas',
        verbose_name='Servidor'
    )
    tipo_justificativa = models.ForeignKey(
        'TipoJustificativa',
        on_delete=models.PROTECT,
        related_name='justificativas',
        verbose_name='Tipo'
    )
    
    # Dados da justificativa
    descricao = models.TextField(
        verbose_name='Descrição',
        help_text='Explique detalhadamente a situação'
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='PENDENTE',
        db_index=True,
        verbose_name='Status'
    )
    
    # Datas de controle
    data_submissao = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data de Submissão'
    )
    data_analise = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Data da Análise'
    )
    
    # Análise da Equipe Volante
    analisado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='justificativas_analisadas',
        verbose_name='Analisado Por'
    )
    parecer = models.TextField(
        blank=True,
        verbose_name='Parecer',
        help_text='Comentário da Equipe Volante sobre a decisão'
    )
    
    # Metadados
    protocolo_original = models.CharField(
        max_length=20,
        db_index=True,
        verbose_name='Protocolo Original',
        help_text='Número do protocolo no momento da submissão'
    )
    
    class Meta:
        verbose_name = 'Justificativa'
        verbose_name_plural = 'Justificativas'
        ordering = ['-data_submissao']
        indexes = [
            models.Index(fields=['status', 'data_submissao']),
            models.Index(fields=['servidor', 'status']),
        ]
    
    def __str__(self):
        return f"Justificativa {self.tipo_justificativa.nome} - {self.tarefa.numero_protocolo_tarefa}"
    
    @property
    def esta_ativa(self):
        """Verifica se a justificativa está ativa (aprovada)"""
        return self.status == 'APROVADA'

    def aprovar(self, analisador, parecer=''):
        """Aprova a justificativa"""
        from django.utils import timezone
        self.status = 'APROVADA'
        self.analisado_por = analisador
        self.parecer = parecer
        self.data_analise = timezone.now()
        self.save()

    def reprovar(self, analisador, parecer):
        """Reprova a justificativa"""
        from django.utils import timezone
        self.status = 'REPROVADA'
        self.analisado_por = analisador
        self.parecer = parecer
        self.data_analise = timezone.now()
        self.save()


class SolicitacaoAjuda(models.Model):
    """
    Solicitações formais de ajuda feitas por servidores.
    Atendidas pela Equipe Volante com acompanhamento.
    """
    STATUS_CHOICES = [
        ('PENDENTE', 'Aguardando Atendimento'),
        ('EM_ATENDIMENTO', 'Em Atendimento'),
        ('CONCLUIDA', 'Concluída'),
        ('CANCELADA', 'Cancelada'),
    ]
    
    tarefa = models.ForeignKey(
        'Tarefa',
        on_delete=models.CASCADE,
        related_name='solicitacoes_ajuda',
        verbose_name='Tarefa'
    )
    servidor_solicitante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='solicitacoes_ajuda_feitas',
        verbose_name='Servidor Solicitante'
    )
    
    # Dados da solicitação
    descricao = models.TextField(
        verbose_name='Descrição do Problema',
        help_text='Explique qual dificuldade está enfrentando'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDENTE',
        db_index=True,
        verbose_name='Status'
    )
    
    # Datas de controle
    data_solicitacao = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data da Solicitação'
    )
    data_atendimento = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Data de Início do Atendimento'
    )
    data_conclusao = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Data de Conclusão'
    )
    
    # Atendimento pela Equipe Volante
    atendido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='solicitacoes_ajuda_atendidas',
        verbose_name='Atendido Por'
    )
    observacoes_atendimento = models.TextField(
        blank=True,
        verbose_name='Observações do Atendimento',
        help_text='Registre as ações tomadas e orientações dadas'
    )
    
    # Metadados
    protocolo_original = models.CharField(
        max_length=20,
        db_index=True,
        verbose_name='Protocolo Original'
    )
    
    class Meta:
        verbose_name = 'Solicitação de Ajuda'
        verbose_name_plural = 'Solicitações de Ajuda'
        ordering = ['-data_solicitacao']
        indexes = [
            models.Index(fields=['status', 'data_solicitacao']),
            models.Index(fields=['servidor_solicitante', 'status']),
        ]
    
    def __str__(self):
        return f"Solicitação de {self.servidor_solicitante.nome_completo} - {self.tarefa.numero_protocolo_tarefa}"
    
    @property
    def esta_pendente(self):
        """Verifica se a solicitação está aguardando atendimento"""
        return self.status == 'PENDENTE'
    
    @property
    def esta_em_atendimento(self):
        """Verifica se a solicitação está sendo atendida"""
        return self.status == 'EM_ATENDIMENTO'

    def iniciar_atendimento(self, atendente):
        """Inicia o atendimento da solicitação"""
        from django.utils import timezone
        self.status = 'EM_ATENDIMENTO'
        self.atendido_por = atendente
        self.data_atendimento = timezone.now()
        self.save()

    def concluir(self, observacoes=''):
        """Conclui o atendimento"""
        from django.utils import timezone
        self.status = 'CONCLUIDA'
        self.observacoes_atendimento = observacoes
        self.data_conclusao = timezone.now()
        self.save()

    def cancelar(self, motivo=''):
        """Cancela a solicitação"""
        from django.utils import timezone
        self.status = 'CANCELADA'
        self.observacoes_atendimento = f'CANCELADO: {motivo}'
        self.data_conclusao = timezone.now()
        self.save()


class ServicosCriticidade(models.Model):
    """
    Configuração de serviços que devem ser excluídos da análise de criticidade.
    Coordenadores podem marcar serviços inteiros para não gerarem alertas.
    """
    nome_servico = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        verbose_name='Nome do Serviço',
        help_text='Nome exato do serviço conforme aparece nas tarefas'
    )
    excluido_criticidade = models.BooleanField(
        default=True,
        verbose_name='Excluído da Criticidade',
        help_text='Se marcado, tarefas deste serviço NÃO serão consideradas críticas'
    )
    motivo_exclusao = models.TextField(
        blank=True,
        verbose_name='Motivo da Exclusão',
        help_text='Explique por que este serviço está sendo excluído'
    )
    
    # Controle de alterações
    data_configuracao = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data de Configuração'
    )
    configurado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='servicos_configurados',
        verbose_name='Configurado Por'
    )
    data_ultima_alteracao = models.DateTimeField(
        auto_now=True,
        verbose_name='Data da Última Alteração'
    )
    
    class Meta:
        verbose_name = 'Configuração de Serviço'
        verbose_name_plural = 'Configurações de Serviços'
        ordering = ['nome_servico']
    
    def __str__(self):
        status = "EXCLUÍDO" if self.excluido_criticidade else "INCLUÍDO"
        return f"{self.nome_servico} [{status}]"


# ============================================
# CONFIGURAÇÃO DE FILAS (NOVO)
# ============================================

class Fila(models.Model):
    """
    Modelo para gerenciar filas de trabalho do sistema.
    Permite adicionar, editar ou remover filas dinamicamente via Django Admin.
    """

    # Código único da fila
    codigo = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        verbose_name='Código da Fila',
        help_text='Código único identificador (ex: PGB, CEABRD-23150521, CEAB-BI-23150521)'
    )

    # Nome curto para exibição
    nome = models.CharField(
        max_length=100,
        verbose_name='Nome Curto',
        help_text='Nome curto para exibição (ex: PGB, CEABRD, CEAB-BI)'
    )

    # Nome completo descritivo
    nome_completo = models.CharField(
        max_length=255,
        verbose_name='Nome Completo',
        help_text='Nome completo descritivo da fila'
    )

    # Descrição
    descricao = models.TextField(
        blank=True,
        verbose_name='Descrição',
        help_text='Descrição detalhada sobre o tipo de tarefas desta fila'
    )

    # Cor hexadecimal
    cor = models.CharField(
        max_length=7,
        default='#6c757d',
        verbose_name='Cor (Hexadecimal)',
        help_text='Cor em formato hexadecimal (ex: #007bff)'
    )

    # Ícone FontAwesome
    icone = models.CharField(
        max_length=50,
        default='fas fa-folder',
        verbose_name='Ícone (FontAwesome)',
        help_text='Classe do ícone FontAwesome (ex: fas fa-building)'
    )

    # Ordem de exibição
    ordem = models.IntegerField(
        default=100,
        verbose_name='Ordem de Exibição',
        help_text='Define a ordem de exibição nas listagens (menor = primeiro)'
    )

    # Status
    ativa = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name='Ativa',
        help_text='Se desmarcado, esta fila não aparecerá mais nas opções'
    )

    # Auditoria
    data_criacao = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data de Criação'
    )

    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='filas_criadas',
        verbose_name='Criado Por'
    )

    data_ultima_alteracao = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Alteração'
    )

    alterado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='filas_alteradas',
        verbose_name='Alterado Por'
    )

    class Meta:
        verbose_name = '📋 Fila de Trabalho'
        verbose_name_plural = '📋 Filas de Trabalho'
        ordering = ['ordem', 'nome']
        indexes = [
            models.Index(fields=['codigo', 'ativa']),
            models.Index(fields=['ordem', 'ativa']),
        ]

    def __str__(self):
        return f"{self.nome} ({self.codigo})"

    @classmethod
    def obter_filas_ativas(cls):
        """Retorna todas as filas ativas ordenadas"""
        return cls.objects.filter(ativa=True).order_by('ordem')

    @classmethod
    def obter_choices_filas(cls):
        """Retorna choices para uso em campos do modelo"""
        return [(fila.codigo, f"{fila.nome} - {fila.nome_completo}")
                for fila in cls.obter_filas_ativas()]


class ConfiguracaoFila(models.Model):
    """
    Configuração de classificação de serviços em filas de trabalho.
    Permite gerenciar via Django Admin quais serviços pertencem a cada fila.
    """

    # Identificação do serviço
    nome_servico = models.CharField(
        max_length=255,
        db_index=True,
        verbose_name='Nome do Serviço',
        help_text='Nome exato do serviço conforme aparece nas tarefas'
    )

    # Código da unidade (opcional para algumas regras)
    codigo_unidade = models.IntegerField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name='Código da Unidade',
        help_text='Código da unidade do INSS (ex: 23150521, 23150003). Deixe em branco para aplicar a todas as unidades.'
    )

    # Fila de destino (agora dinâmico - busca do modelo Fila)
    tipo_fila = models.CharField(
        max_length=50,
        db_index=True,
        verbose_name='Fila de Destino',
        help_text='Código da fila para a qual este serviço será direcionado (ex: PGB, CEABRD-23150521)'
    )

    # Prioridade (para casos onde há múltiplas regras)
    prioridade = models.IntegerField(
        default=100,
        verbose_name='Prioridade',
        help_text='Regras com prioridade menor são aplicadas primeiro (1 = maior prioridade)'
    )

    # Controle de ativação
    ativa = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name='Ativa',
        help_text='Se desmarcado, esta regra será ignorada na classificação'
    )

    # Observações
    observacoes = models.TextField(
        blank=True,
        verbose_name='Observações',
        help_text='Anotações sobre esta configuração'
    )

    # Auditoria
    data_criacao = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data de Criação'
    )

    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='configuracoes_fila_criadas',
        verbose_name='Criado Por'
    )

    data_ultima_alteracao = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Alteração'
    )

    alterado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='configuracoes_fila_alteradas',
        verbose_name='Alterado Por'
    )

    class Meta:
        verbose_name = '⚙️ Configuração de Fila'
        verbose_name_plural = '⚙️ Configurações de Filas (Classificação Automática)'
        ordering = ['prioridade', 'tipo_fila', 'nome_servico']
        # Permite mesma combinação serviço+unidade em filas diferentes
        # mas com prioridades diferentes
        indexes = [
            models.Index(fields=['nome_servico', 'codigo_unidade', 'ativa']),
            models.Index(fields=['tipo_fila', 'ativa']),
            models.Index(fields=['prioridade', 'ativa']),
        ]

    def __str__(self):
        if self.codigo_unidade:
            return f"{self.nome_servico} (Unidade {self.codigo_unidade}) → {self.tipo_fila}"
        return f"{self.nome_servico} → {self.tipo_fila}"

    @classmethod
    def obter_fila_para_servico(cls, nome_servico, codigo_unidade):
        """
        Retorna a fila configurada para um serviço específico.

        Args:
            nome_servico (str): Nome do serviço
            codigo_unidade (int): Código da unidade

        Returns:
            str or None: Código da fila ou None se não encontrada
        """
        # Buscar configuração ativa, ordenada por prioridade
        # Primeiro tenta match exato com serviço + unidade
        config = cls.objects.filter(
            nome_servico=nome_servico,
            codigo_unidade=codigo_unidade,
            ativa=True
        ).order_by('prioridade').first()

        # Se não encontrar, tenta match apenas com serviço (unidade = None)
        if not config:
            config = cls.objects.filter(
                nome_servico=nome_servico,
                codigo_unidade__isnull=True,
                ativa=True
            ).order_by('prioridade').first()

        return config.tipo_fila if config else None


# ============================================
# MODEL EXISTENTE: NOTIFICAÇÃO EMAIL
# ============================================

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

# ============================================
# MODELOS PARA AÇÕES AUTOMATIZADAS
# ============================================

class BloqueioServidor(models.Model):
    """Gerencia bloqueios de caixa de servidores por fila."""

    TIPO_BLOQUEIO = 'BLOQUEIO'
    TIPO_DESBLOQUEIO = 'DESBLOQUEIO'
    TIPOS_ACAO = [(TIPO_BLOQUEIO, 'Bloquear Caixa'), (TIPO_DESBLOQUEIO, 'Desbloquear Caixa')]

    STATUS_PENDENTE = 'PENDENTE'
    STATUS_PROCESSANDO = 'PROCESSANDO'
    STATUS_CONCLUIDO = 'CONCLUIDO'
    STATUS_ERRO = 'ERRO'
    STATUS_CANCELADO = 'CANCELADO'
    STATUS_CHOICES = [
        (STATUS_PENDENTE, 'Pendente'), (STATUS_PROCESSANDO, 'Processando'),
        (STATUS_CONCLUIDO, 'Concluído'), (STATUS_ERRO, 'Erro'), (STATUS_CANCELADO, 'Cancelado')
    ]

    servidor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                  related_name='bloqueios',
                                  db_column='siape_servidor', verbose_name='Servidor (SIAPE)')
    codigo_fila = models.CharField(max_length=20, verbose_name='Código da Fila')
    tipo_acao = models.CharField(max_length=20, choices=TIPOS_ACAO, verbose_name='Tipo de Ação')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDENTE,
                               db_index=True, verbose_name='Status')
    data_solicitacao = models.DateTimeField(auto_now_add=True, verbose_name='Data da Solicitação')
    data_processamento = models.DateTimeField(null=True, blank=True, verbose_name='Data do Processamento')
    data_conclusao = models.DateTimeField(null=True, blank=True, verbose_name='Data da Conclusão')
    solicitado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                        null=True, related_name='bloqueios_solicitados',
                                        verbose_name='Solicitado Por')
    resposta_robo = models.TextField(blank=True, verbose_name='Resposta do Robô')
    mensagem_erro = models.TextField(blank=True, verbose_name='Mensagem de Erro')
    observacoes = models.TextField(blank=True, verbose_name='Observações')

    class Meta:
        verbose_name = 'Bloqueio de Servidor'
        verbose_name_plural = '🔒 Bloqueios de Servidores'
        ordering = ['-data_solicitacao']

    def __str__(self):
        return f"{self.get_tipo_acao_display()} - {self.servidor.siape} - Fila {self.codigo_fila}"

    @classmethod
    def servidor_esta_bloqueado(cls, siape, codigo_fila):
        ultimo_bloqueio = cls.objects.filter(servidor__siape=siape, codigo_fila=codigo_fila,
                                               status=cls.STATUS_CONCLUIDO).order_by('-data_conclusao').first()
        return ultimo_bloqueio and ultimo_bloqueio.tipo_acao == cls.TIPO_BLOQUEIO

    def marcar_como_processando(self):
        from django.utils import timezone
        self.status = self.STATUS_PROCESSANDO
        self.data_processamento = timezone.now()
        self.save()

    def marcar_como_concluido(self, resposta_robo=''):
        from django.utils import timezone
        self.status = self.STATUS_CONCLUIDO
        self.data_conclusao = timezone.now()
        self.resposta_robo = resposta_robo
        self.save()

    def marcar_como_erro(self, mensagem_erro=''):
        from django.utils import timezone
        self.status = self.STATUS_ERRO
        self.data_conclusao = timezone.now()
        self.mensagem_erro = mensagem_erro
        self.save()


class SolicitacaoNotificacao(models.Model):
    """Solicitações de criação de tarefas PGB (notificações)."""

    TIPO_PRIMEIRA = 'PRIMEIRA_NOTIFICACAO'
    TIPO_SEGUNDA = 'SEGUNDA_NOTIFICACAO'
    TIPOS_NOTIFICACAO = [(TIPO_PRIMEIRA, 'PGB - Primeira Notificação'), (TIPO_SEGUNDA, 'PGB - Segunda Notificação')]

    STATUS_PENDENTE = 'PENDENTE'
    STATUS_PROCESSANDO = 'PROCESSANDO'
    STATUS_CONCLUIDO = 'CONCLUIDO'
    STATUS_ERRO = 'ERRO'
    STATUS_CANCELADO = 'CANCELADO'
    STATUS_CHOICES = [
        (STATUS_PENDENTE, 'Pendente'), (STATUS_PROCESSANDO, 'Processando'),
        (STATUS_CONCLUIDO, 'Concluído'), (STATUS_ERRO, 'Erro'), (STATUS_CANCELADO, 'Cancelado')
    ]

    servidor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                  related_name='notificacoes_pgb',
                                  db_column='siape_servidor', verbose_name='Servidor (SIAPE)')
    tipo_notificacao = models.CharField(max_length=30, choices=TIPOS_NOTIFICACAO, verbose_name='Tipo de Notificação')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDENTE,
                               db_index=True, verbose_name='Status')
    data_solicitacao = models.DateTimeField(auto_now_add=True, verbose_name='Data da Solicitação')
    data_processamento = models.DateTimeField(null=True, blank=True, verbose_name='Data do Processamento')
    data_conclusao = models.DateTimeField(null=True, blank=True, verbose_name='Data da Conclusão')
    solicitado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                        null=True, related_name='notificacoes_solicitadas',
                                        verbose_name='Solicitado Por')
    numero_protocolo_criado = models.CharField(max_length=20, blank=True, verbose_name='Número do Protocolo Criado')
    resposta_robo = models.TextField(blank=True, verbose_name='Resposta do Robô')
    mensagem_erro = models.TextField(blank=True, verbose_name='Mensagem de Erro')
    observacoes = models.TextField(blank=True, verbose_name='Observações')

    class Meta:
        verbose_name = 'Solicitação de Notificação PGB'
        verbose_name_plural = '📋 Solicitações de Notificações PGB'
        ordering = ['-data_solicitacao']

    def __str__(self):
        return f"{self.get_tipo_notificacao_display()} - {self.servidor.siape}"

    @classmethod
    def servidor_tem_notificacao_ativa(cls, siape):
        return cls.objects.filter(servidor__siape=siape, status=cls.STATUS_CONCLUIDO).exists()

    def marcar_como_processando(self):
        from django.utils import timezone
        self.status = self.STATUS_PROCESSANDO
        self.data_processamento = timezone.now()
        self.save()

    def marcar_como_concluido(self, numero_protocolo='', resposta_robo=''):
        from django.utils import timezone
        self.status = self.STATUS_CONCLUIDO
        self.data_conclusao = timezone.now()
        self.numero_protocolo_criado = numero_protocolo
        self.resposta_robo = resposta_robo
        self.save()

    def marcar_como_erro(self, mensagem_erro=''):
        from django.utils import timezone
        self.status = self.STATUS_ERRO
        self.data_conclusao = timezone.now()
        self.mensagem_erro = mensagem_erro
        self.save()


class HistoricoBloqueio(models.Model):
    """Histórico completo de todas as ações de bloqueio/desbloqueio."""

    bloqueio = models.ForeignKey(BloqueioServidor, on_delete=models.CASCADE,
                                   related_name='historico', verbose_name='Bloqueio')
    servidor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                  related_name='historico_bloqueios',
                                  db_column='siape_servidor', verbose_name='Servidor (SIAPE)')
    codigo_fila = models.CharField(max_length=20, verbose_name='Código da Fila')
    tipo_acao = models.CharField(max_length=20, verbose_name='Tipo de Ação')
    status = models.CharField(max_length=20, verbose_name='Status')
    data_hora = models.DateTimeField(auto_now_add=True, verbose_name='Data/Hora')
    executado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                        null=True, related_name='bloqueios_executados',
                                        verbose_name='Executado Por')
    detalhes = models.TextField(blank=True, verbose_name='Detalhes da Ação')
    resposta_robo = models.TextField(blank=True, verbose_name='Resposta do Robô')

    class Meta:
        verbose_name = 'Histórico de Bloqueio'
        verbose_name_plural = '📜 Histórico de Bloqueios'
        ordering = ['-data_hora']

    def __str__(self):
        return f"{self.tipo_acao} - {self.servidor.siape} - {self.data_hora.strftime('%d/%m/%Y %H:%M')}"


class HistoricoNotificacao(models.Model):
    """Histórico completo de todas as solicitações de notificação PGB."""

    notificacao = models.ForeignKey(SolicitacaoNotificacao, on_delete=models.CASCADE,
                                      related_name='historico', verbose_name='Notificação')
    servidor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                  related_name='historico_notificacoes',
                                  db_column='siape_servidor', verbose_name='Servidor (SIAPE)')
    tipo_notificacao = models.CharField(max_length=30, verbose_name='Tipo de Notificação')
    status = models.CharField(max_length=20, verbose_name='Status')
    data_hora = models.DateTimeField(auto_now_add=True, verbose_name='Data/Hora')
    executado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                        null=True, related_name='notificacoes_executadas',
                                        verbose_name='Executado Por')
    detalhes = models.TextField(blank=True, verbose_name='Detalhes da Ação')
    numero_protocolo = models.CharField(max_length=20, blank=True, verbose_name='Número do Protocolo')
    resposta_robo = models.TextField(blank=True, verbose_name='Resposta do Robô')

    class Meta:
        verbose_name = 'Histórico de Notificação'
        verbose_name_plural = '📜 Histórico de Notificações'
        ordering = ['-data_hora']

    def __str__(self):
        return f"{self.tipo_notificacao} - {self.servidor.siape} - {self.data_hora.strftime('%d/%m/%Y %H:%M')}"


class HistoricoEmail(models.Model):
    """Histórico de todos os emails enviados pelo sistema."""

    STATUS_PENDENTE = 'PENDENTE'
    STATUS_ENVIADO = 'ENVIADO'
    STATUS_ERRO = 'ERRO'
    STATUS_CHOICES = [(STATUS_PENDENTE, 'Pendente'), (STATUS_ENVIADO, 'Enviado'), (STATUS_ERRO, 'Erro')]

    servidor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                  related_name='historico_emails',
                                  db_column='siape_servidor', verbose_name='Servidor Destinatário')
    email_destinatario = models.EmailField(verbose_name='Email Destinatário')
    assunto = models.CharField(max_length=255, verbose_name='Assunto')
    corpo_email = models.TextField(verbose_name='Corpo do Email')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDENTE,
                               db_index=True, verbose_name='Status')
    data_solicitacao = models.DateTimeField(auto_now_add=True, verbose_name='Data da Solicitação')
    data_envio = models.DateTimeField(null=True, blank=True, verbose_name='Data do Envio')
    enviado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                      null=True, related_name='emails_enviados',
                                      verbose_name='Enviado Por')
    resposta_api = models.TextField(blank=True, verbose_name='Resposta da API Microsoft Graph')
    mensagem_erro = models.TextField(blank=True, verbose_name='Mensagem de Erro')

    class Meta:
        verbose_name = 'Histórico de Email'
        verbose_name_plural = '📧 Histórico de Emails'
        ordering = ['-data_solicitacao']

    def __str__(self):
        return f"Email para {self.servidor.siape} - {self.assunto[:50]}"

    def marcar_como_enviado(self, resposta_api=''):
        from django.utils import timezone
        self.status = self.STATUS_ENVIADO
        self.data_envio = timezone.now()
        self.resposta_api = resposta_api
        self.save()

    def marcar_como_erro(self, mensagem_erro=''):
        from django.utils import timezone
        self.status = self.STATUS_ERRO
        self.data_envio = timezone.now()
        self.mensagem_erro = mensagem_erro
        self.save()


class TemplateEmail(models.Model):
    """Templates de email configuráveis via Django Admin."""

    nome = models.CharField(max_length=100, unique=True, verbose_name='Nome do Template')
    descricao = models.TextField(blank=True, verbose_name='Descrição')
    assunto = models.CharField(max_length=255, verbose_name='Assunto do Email')
    corpo_html = models.TextField(verbose_name='Corpo do Email (HTML)')
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name='Data de Criação')
    data_alteracao = models.DateTimeField(auto_now=True, verbose_name='Data de Alteração')
    criado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                     null=True, blank=True, related_name='templates_criados',
                                     verbose_name='Criado Por')

    class Meta:
        verbose_name = 'Template de Email'
        verbose_name_plural = '✉️ Templates de Email'
        ordering = ['nome']

    def __str__(self):
        return self.nome


class HistoricoAcaoLote(models.Model):
    """Histórico de geração de arquivos CSV para ações em lote."""

    TIPO_REMOVER = 'REMOVER_RESPONSAVEL'
    TIPO_TRANSFERIR = 'TRANSFERIR_TAREFA'
    TIPOS_ACAO = [
        (TIPO_REMOVER, 'Remover Responsável em Lote (Tipo 14)'),
        (TIPO_TRANSFERIR, 'Transferir Tarefa em Lote (Tipo 12)')
    ]

    servidor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='historico_acoes_lote',
        db_column='siape_servidor',
        verbose_name='Servidor'
    )
    codigo_fila = models.CharField(
        max_length=50,
        verbose_name='Código da Fila'
    )
    tipo_acao = models.CharField(
        max_length=30,
        choices=TIPOS_ACAO,
        verbose_name='Tipo de Ação'
    )

    # Critério de seleção
    criterio_selecao = models.CharField(
        max_length=20,
        verbose_name='Critério de Seleção',
        help_text='TODAS, SERVICO, QUANTIDADE ou MANUAL'
    )
    servico_selecionado = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Serviço Selecionado'
    )
    quantidade_tarefas = models.IntegerField(
        verbose_name='Quantidade de Tarefas no Arquivo'
    )

    # Dados da transferência (se aplicável)
    uo_destino = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='UO de Destino'
    )
    despacho = models.TextField(
        blank=True,
        verbose_name='Despacho'
    )

    # Auditoria
    data_geracao = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data de Geração'
    )
    gerado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='acoes_lote_geradas',
        verbose_name='Gerado Por'
    )
    nome_arquivo = models.CharField(
        max_length=255,
        verbose_name='Nome do Arquivo Gerado'
    )
    protocolos_incluidos = models.TextField(
        verbose_name='Protocolos Incluídos',
        help_text='Lista de protocolos incluídos no arquivo (separados por vírgula)'
    )

    class Meta:
        verbose_name = 'Histórico de Ação em Lote'
        verbose_name_plural = '📄 Histórico de Ações em Lote'
        ordering = ['-data_geracao']
        indexes = [
            models.Index(fields=['servidor', 'data_geracao']),
            models.Index(fields=['codigo_fila', 'data_geracao']),
            models.Index(fields=['tipo_acao', 'data_geracao']),
        ]

    def __str__(self):
        return f"{self.get_tipo_acao_display()} - {self.servidor.siape} - {self.data_geracao.strftime('%d/%m/%Y %H:%M')}"
