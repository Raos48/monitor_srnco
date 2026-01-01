"""
Comando de diagnóstico para identificar tarefas que deveriam se enquadrar nas regras de criticidade
"""
from django.core.management.base import BaseCommand
from tarefas.models import Tarefa
from tarefas.analisador import AnalisadorCriticidade
from datetime import date


class Command(BaseCommand):
    help = 'Diagnóstico de regras de criticidade - identifica tarefas que deveriam se enquadrar nas regras'

    def handle(self, *args, **options):
        self.stdout.write('='*80)
        self.stdout.write(self.style.SUCCESS('DIAGNÓSTICO DAS REGRAS DE CRITICIDADE'))
        self.stdout.write('='*80)

        # Buscar tarefas com status Pendente e descrição "Exigência cumprida"
        tarefas_exigencia_cumprida = Tarefa.objects.filter(
            status_tarefa__icontains='Pendente'
        ).filter(
            descricao_cumprimento_exigencia_tarefa__icontains='Exigência cumprida'
        )

        total = tarefas_exigencia_cumprida.count()
        self.stdout.write(f'\n[INFO] Total de tarefas com status Pendente + "Exigencia cumprida": {total}')

        # Analisar características dessas tarefas
        com_data_inicio = tarefas_exigencia_cumprida.exclude(data_inicio_ultima_exigencia__isnull=True).count()
        com_data_fim = tarefas_exigencia_cumprida.exclude(data_fim_ultima_exigencia__isnull=True).count()
        com_data_distribuicao = tarefas_exigencia_cumprida.exclude(data_distribuicao_tarefa__isnull=True).count()

        self.stdout.write(f'\n[CARACTERISTICAS] Das tarefas:')
        self.stdout.write(f'   Com data_inicio_ultima_exigencia: {com_data_inicio}')
        self.stdout.write(f'   Com data_fim_ultima_exigencia: {com_data_fim}')
        self.stdout.write(f'   Com data_distribuicao_tarefa: {com_data_distribuicao}')

        # Separar por tipo de exigência
        tarefas_completas = tarefas_exigencia_cumprida.exclude(
            data_inicio_ultima_exigencia__isnull=True
        ).exclude(
            data_fim_ultima_exigencia__isnull=True
        ).exclude(
            data_distribuicao_tarefa__isnull=True
        )

        total_completas = tarefas_completas.count()
        self.stdout.write(f'\n[OK] Tarefas com TODAS as datas necessarias: {total_completas}')

        if total_completas == 0:
            self.stdout.write(self.style.WARNING('\n[AVISO] NENHUMA tarefa tem todas as datas necessarias!'))
            self.stdout.write(self.style.WARNING('   Isso explica por que REGRA_1 e REGRA_4 nao estao sendo aplicadas.'))

            # Mostrar exemplos de tarefas sem as datas
            self.stdout.write('\n[ANALISE] Analisando alguns exemplos de tarefas...\n')
            for tarefa in tarefas_exigencia_cumprida[:5]:
                self.stdout.write(f'\n   Protocolo: {tarefa.numero_protocolo_tarefa}')
                self.stdout.write(f'   Status: {tarefa.status_tarefa}')
                self.stdout.write(f'   Descricao: {tarefa.descricao_cumprimento_exigencia_tarefa}')
                self.stdout.write(f'   Data distribuicao: {tarefa.data_distribuicao_tarefa}')
                self.stdout.write(f'   Data inicio exigencia: {tarefa.data_inicio_ultima_exigencia}')
                self.stdout.write(f'   Data fim exigencia: {tarefa.data_fim_ultima_exigencia}')
                self.stdout.write(f'   Regra aplicada: {tarefa.regra_aplicada_calculado}')

            return

        # Analisar as tarefas completas
        regra_1_candidatas = 0  # Exigência cadastrada DEPOIS da atribuição
        regra_4_candidatas = 0  # Exigência cadastrada ANTES da atribuição

        self.stdout.write('\n[ANALISE] Analisando tarefas candidatas...\n')

        for tarefa in tarefas_completas[:10]:  # Mostrar primeiras 10
            # Comparar datas
            exigencia_depois = tarefa.data_inicio_ultima_exigencia >= tarefa.data_distribuicao_tarefa

            if exigencia_depois:
                regra_1_candidatas += 1
                tipo = "REGRA_1 (servidor cadastrou)"
            else:
                regra_4_candidatas += 1
                tipo = "REGRA_4 (exigência anterior)"

            self.stdout.write(f'\n   [PROTOCOLO] {tarefa.numero_protocolo_tarefa}')
            self.stdout.write(f'      Status: {tarefa.status_tarefa}')
            self.stdout.write(f'      Descricao: {tarefa.descricao_cumprimento_exigencia_tarefa}')
            self.stdout.write(f'      Atribuicao: {tarefa.data_distribuicao_tarefa.strftime("%d/%m/%Y")}')
            self.stdout.write(f'      Inicio exigencia: {tarefa.data_inicio_ultima_exigencia.strftime("%d/%m/%Y")}')
            self.stdout.write(f'      Fim exigencia: {tarefa.data_fim_ultima_exigencia.strftime("%d/%m/%Y")}')
            self.stdout.write(f'      Tipo: {tipo}')
            self.stdout.write(f'      Regra atual: {tarefa.regra_aplicada_calculado}')

            # Testar análise
            resultado = AnalisadorCriticidade.analisar_tarefa(tarefa)
            self.stdout.write(f'      Analise agora: {resultado["regra"]} - {resultado["nivel"]}')

        # Contar total de cada tipo
        for tarefa in tarefas_completas:
            exigencia_depois = tarefa.data_inicio_ultima_exigencia >= tarefa.data_distribuicao_tarefa
            if exigencia_depois:
                regra_1_candidatas += 1
            else:
                regra_4_candidatas += 1

        self.stdout.write('\n' + '='*80)
        self.stdout.write(self.style.SUCCESS('RESUMO'))
        self.stdout.write('='*80)
        self.stdout.write(f'\n   Candidatas REGRA_1 (servidor cadastrou exigência): {regra_1_candidatas}')
        self.stdout.write(f'   Candidatas REGRA_4 (exigência cumprida anterior): {regra_4_candidatas}')

        # Verificar quantas estão marcadas corretamente
        regra_1_salvas = Tarefa.objects.filter(
            regra_aplicada_calculado='REGRA_1_EXIGENCIA_CUMPRIDA'
        ).count()
        regra_4_salvas = Tarefa.objects.filter(
            regra_aplicada_calculado='REGRA_4_PRIMEIRA_ACAO_COM_EXIGENCIA'
        ).count()

        self.stdout.write(f'\n   Tarefas salvas com REGRA_1: {regra_1_salvas}')
        self.stdout.write(f'   Tarefas salvas com REGRA_4: {regra_4_salvas}')

        if regra_1_candidatas > regra_1_salvas or regra_4_candidatas > regra_4_salvas:
            self.stdout.write(self.style.WARNING('\n[PROBLEMA] PROBLEMA ENCONTRADO!'))
            self.stdout.write(self.style.WARNING('   Ha tarefas que deveriam ter as regras mas nao estao marcadas.'))
            self.stdout.write(self.style.WARNING('   Execute: python manage.py recalcular_tarefas'))
