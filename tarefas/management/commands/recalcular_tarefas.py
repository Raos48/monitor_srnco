from django.core.management.base import BaseCommand
from tarefas.models import Tarefa
from tarefas.analisador import obter_analisador
from django.utils import timezone

class Command(BaseCommand):
    help = "Recalcula criticidade de todas as tarefas com o novo sistema binário (CRÍTICA/REGULAR)."

    def handle(self, *args, **kwargs):
        analisador = obter_analisador()
        tarefas = Tarefa.objects.all()
        total = tarefas.count()
        self.stdout.write(f"[RECALCULO] Recalculando {total} tarefas...\n")

        contador = 0
        for tarefa in tarefas:
            resultado = analisador.analisar_tarefa(tarefa)

            # CORRIGIDO: Usar 'nivel' e 'descricao' em vez de 'severidade' e 'detalhes'
            tarefa.nivel_criticidade_calculado = resultado['nivel']
            tarefa.regra_aplicada_calculado = resultado['regra']
            tarefa.alerta_criticidade_calculado = resultado['alerta']
            tarefa.descricao_criticidade_calculado = resultado['descricao']
            tarefa.dias_pendente_criticidade_calculado = resultado['dias_pendente']
            tarefa.prazo_limite_criticidade_calculado = resultado['prazo_limite']
            tarefa.pontuacao_criticidade = 100 if resultado['nivel'] == 'CRÍTICA' else 0
            tarefa.cor_criticidade_calculado = resultado['cor']  # Usar cor do resultado
            tarefa.data_calculo_criticidade = timezone.now()
            tarefa.save()

            contador += 1
            if contador % 1000 == 0:
                self.stdout.write(f"  [OK] {contador}/{total} processadas...")

        self.stdout.write(f"\n[SUCESSO] {total} tarefas recalculadas com sucesso!\n")

        stats = Tarefa.estatisticas_criticidade()
        self.stdout.write("[ESTATISTICAS] DO NOVO SISTEMA:")
        self.stdout.write(f"   Total de tarefas: {stats['total']}")
        self.stdout.write(f"   [CRITICA] Criticas: {stats['criticas']} ({stats.get('percentual_criticas', 0)}%)")
        self.stdout.write(f"   [REGULAR] Regulares: {stats['regulares']} ({stats.get('percentual_regulares', 0)}%)")
