"""
Management command para testar o analisador de criticidade
Uso: python manage.py testar_analisador
"""

from django.core.management.base import BaseCommand
from tarefas.analisador import obter_analisador
from tarefas.models import Tarefa


class Command(BaseCommand):
    help = 'Testa o analisador de criticidade em tarefas reais'

    def add_arguments(self, parser):
        parser.add_argument(
            '--protocolo',
            type=str,
            help='Número do protocolo específico para testar',
        )
        parser.add_argument(
            '--limite',
            type=int,
            default=10,
            help='Quantidade de tarefas para analisar (padrão: 10)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('TESTE DO ANALISADOR DE CRITICIDADE'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write('')

        # Obter analisador
        analisador = obter_analisador()
        self.stdout.write(self.style.SUCCESS('✓ Analisador criado com sucesso!'))
        self.stdout.write(f'  Parâmetros: {analisador.parametros}')
        self.stdout.write(f'  Data referência: {analisador.data_referencia}')
        self.stdout.write('')

        # Testar tarefa específica ou primeiras N tarefas
        if options['protocolo']:
            # Testar tarefa específica
            try:
                tarefa = Tarefa.objects.get(numero_protocolo_tarefa=options['protocolo'])
                self.testar_tarefa(analisador, tarefa)
            except Tarefa.DoesNotExist:
                self.stdout.write(self.style.ERROR(
                    f'✗ Tarefa {options["protocolo"]} não encontrada'
                ))
        else:
            # Testar primeiras N tarefas
            tarefas = Tarefa.objects.all()[:options['limite']]
            
            if not tarefas:
                self.stdout.write(self.style.WARNING('⚠ Nenhuma tarefa encontrada no banco'))
                return

            self.stdout.write(self.style.SUCCESS(
                f'📋 Analisando {len(tarefas)} tarefas...\n'
            ))

            # Contadores por severidade
            contador = {
                'CRÍTICA': 0,
                'ALTA': 0,
                'MÉDIA': 0,
                'BAIXA': 0,
                'NENHUMA': 0
            }

            for i, tarefa in enumerate(tarefas, 1):
                self.stdout.write(self.style.HTTP_INFO(f'\n[{i}] Protocolo: {tarefa.numero_protocolo_tarefa}'))
                resultado = self.testar_tarefa(analisador, tarefa, exibir_detalhes=False)
                contador[resultado['severidade']] += 1

            # Exibir resumo
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('=' * 70))
            self.stdout.write(self.style.SUCCESS('RESUMO DA ANÁLISE'))
            self.stdout.write(self.style.SUCCESS('=' * 70))
            self.stdout.write(f'Total analisado: {len(tarefas)}')
            self.stdout.write('')
            self.stdout.write('Por Severidade:')
            self.stdout.write(f'  🔴 CRÍTICA: {contador["CRÍTICA"]}')
            self.stdout.write(f'  🟠 ALTA: {contador["ALTA"]}')
            self.stdout.write(f'  🟡 MÉDIA: {contador["MÉDIA"]}')
            self.stdout.write(f'  🟢 BAIXA: {contador["BAIXA"]}')
            self.stdout.write(f'  ⚪ NENHUMA: {contador["NENHUMA"]}')

    def testar_tarefa(self, analisador, tarefa, exibir_detalhes=True):
        """Testa o analisador em uma tarefa específica"""
        resultado = analisador.analisar_tarefa(tarefa)

        # Colorir por severidade
        severidade_style = {
            'CRÍTICA': self.style.ERROR,
            'ALTA': self.style.WARNING,
            'MÉDIA': self.style.HTTP_INFO,
            'BAIXA': self.style.SUCCESS,
            'NENHUMA': self.style.HTTP_NOT_MODIFIED
        }

        style = severidade_style.get(resultado['severidade'], self.style.SUCCESS)

        if exibir_detalhes:
            self.stdout.write(self.style.SUCCESS('✓ Análise realizada!'))
            self.stdout.write(f'  Servidor: {tarefa.nome_profissional_responsavel}')
            self.stdout.write(f'  Serviço: {tarefa.nome_servico}')
        
        self.stdout.write(f'  Regra: {resultado["regra"]}')
        self.stdout.write(style(f'  Severidade: {resultado["severidade"]}'))
        self.stdout.write(f'  Alerta: {resultado["alerta"]}')
        
        if exibir_detalhes:
            self.stdout.write(f'  Detalhes: {resultado["detalhes"]}')

        return resultado