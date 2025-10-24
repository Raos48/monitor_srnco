from django.db import models
from usuarios.models import CustomUser
from tarefas.models import Tarefa

class RegistroImportacao(models.Model):
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

    def __str__(self):
        data_formatada = self.data_importacao.strftime('%d/%m/%Y às %H:%M')
        nome_usuario = self.usuario.nome_completo if self.usuario else "Usuário Desconhecido"
        return f"Importação em {data_formatada} por {nome_usuario}"

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