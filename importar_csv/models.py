from django.db import models
from usuarios.models import CustomUser
from tarefas.models import Tarefa

class RegistroImportacao(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pendente'),
        ('PROCESSING', 'Processando'),
        ('COMPLETED', 'Concluída'),
        ('FAILED', 'Falhou'),
    ]

    usuario = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Usuário Responsável"
    )
    data_importacao = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data da Importação"
    )
    nome_arquivo = models.CharField(
        max_length=255,
        verbose_name="Nome do Arquivo CSV"
    )
    caminho_arquivo = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="Caminho do Arquivo Temporário"
    )

    # Campos de rastreamento assíncrono
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        verbose_name="Status da Importação"
    )
    total_linhas = models.PositiveIntegerField(
        default=0,
        verbose_name="Total de Linhas no CSV"
    )
    linhas_processadas = models.PositiveIntegerField(
        default=0,
        verbose_name="Linhas Processadas"
    )
    progresso_percentual = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="Progresso (%)"
    )

    # Campos de resultado
    registros_criados = models.PositiveIntegerField(
        default=0,
        verbose_name="Tarefas Novas Criadas"
    )
    registros_atualizados = models.PositiveIntegerField(
        default=0,
        verbose_name="Tarefas Atualizadas"
    )
    usuarios_criados = models.PositiveIntegerField(
        default=0,
        verbose_name="Usuários Criados"
    )

    # Controle de tempo
    data_inicio_processamento = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Início do Processamento"
    )
    data_fim_processamento = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fim do Processamento"
    )

    # Mensagens de erro
    mensagem_erro = models.TextField(
        blank=True,
        null=True,
        verbose_name="Mensagem de Erro"
    )

    def __str__(self):
        data_formatada = self.data_importacao.strftime('%d/%m/%Y às %H:%M')
        nome_usuario = self.usuario.nome_completo if self.usuario else "Usuário Desconhecido"
        return f"Importação em {data_formatada} por {nome_usuario} - {self.get_status_display()}"

    def calcular_progresso(self):
        """Calcula e atualiza o percentual de progresso"""
        if self.total_linhas > 0:
            self.progresso_percentual = (self.linhas_processadas / self.total_linhas) * 100
        else:
            self.progresso_percentual = 0
        return self.progresso_percentual

    def duracao_processamento(self):
        """Retorna a duração do processamento em segundos"""
        if self.data_inicio_processamento and self.data_fim_processamento:
            delta = self.data_fim_processamento - self.data_inicio_processamento
            return delta.total_seconds()
        return None

    def arquivo_existe(self):
        """Verifica se o arquivo ainda existe no disco"""
        import os
        if self.caminho_arquivo:
            return os.path.exists(self.caminho_arquivo)
        return False

    def tamanho_arquivo_mb(self):
        """Retorna o tamanho do arquivo em MB"""
        import os
        if self.caminho_arquivo and os.path.exists(self.caminho_arquivo):
            tamanho_bytes = os.path.getsize(self.caminho_arquivo)
            return tamanho_bytes / (1024 * 1024)
        return None

    def deletar_arquivo(self):
        """Deleta o arquivo do disco de forma segura"""
        import os
        if self.caminho_arquivo and os.path.exists(self.caminho_arquivo):
            try:
                os.remove(self.caminho_arquivo)
                return True, f"Arquivo deletado com sucesso: {self.nome_arquivo}"
            except Exception as e:
                return False, f"Erro ao deletar arquivo: {str(e)}"
        return False, "Arquivo não encontrado no disco"

    class Meta:
        verbose_name = "Registro de Importação"
        verbose_name_plural = "Registros de Importações"
        ordering = ['-data_importacao']


class HistoricoTarefa(models.Model):
    # Rastreamento
    tarefa_original = models.ForeignKey(
        Tarefa, 
        on_delete=models.CASCADE, 
        related_name="historicos", 
        verbose_name="Tarefa Original"
    )
    registro_importacao = models.ForeignKey(
        RegistroImportacao, 
        on_delete=models.CASCADE, 
        related_name="historicos_gerados", 
        verbose_name="Registro de Importação"
    )

    # Campos espelhados COMPLETOS (incluindo os 3 novos)
    status_tarefa = models.CharField(max_length=100, blank=True, null=True)
    descricao_cumprimento_exigencia_tarefa = models.TextField(blank=True, null=True)
    siape_responsavel = models.CharField(max_length=20, blank=True, null=True)
    cpf_responsavel = models.CharField(max_length=14, blank=True, null=True)
    nome_profissional_responsavel = models.CharField(max_length=255, blank=True, null=True)
    codigo_gex_responsavel = models.CharField(max_length=10, blank=True, null=True)
    nome_gex_responsavel = models.CharField(max_length=255, blank=True, null=True)
    
    # Datas (incluindo os 2 novos campos de data)
    data_distribuicao_tarefa = models.DateField(blank=True, null=True)
    data_ultima_atualizacao = models.DateField(blank=True, null=True)
    data_prazo = models.DateField(blank=True, null=True, verbose_name="Data do Prazo")  # ← NOVO CAMPO
    data_inicio_ultima_exigencia = models.DateField(blank=True, null=True, verbose_name="Data de Início da Última Exigência")  # ← NOVO CAMPO
    data_fim_ultima_exigencia = models.DateField(blank=True, null=True)
    data_processamento_tarefa = models.DateTimeField(blank=True, null=True)
    
    # Indicadores
    indicador_tarefa_reaberta = models.IntegerField(default=0, verbose_name="Indicador de Tarefa Reaberta")  # ← NOVO CAMPO
    
    # Tempos
    tempo_ultima_exigencia_em_dias = models.IntegerField(blank=True, null=True)
    tempo_em_pendencia_em_dias = models.IntegerField(default=0)
    tempo_em_exigencia_em_dias = models.IntegerField(default=0)
    tempo_ate_ultima_distribuicao_tarefa_em_dias = models.IntegerField(default=0)

    def __str__(self):
        data_formatada = self.registro_importacao.data_importacao.strftime('%d/%m/%Y')
        return f"Histórico de {self.tarefa_original.numero_protocolo_tarefa} em {data_formatada}"
    class Meta:
        verbose_name = "Histórico de Tarefa"
        verbose_name_plural = "Históricos de Tarefas"
        ordering = ['-registro_importacao__data_importacao']