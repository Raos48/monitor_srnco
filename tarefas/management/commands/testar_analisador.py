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

            # Contadores por nível
            contador = {
                'CRÍTICA': 0,
                'JUSTIFICADA': 0,
                'EXCLUÍDA': 0,
                'REGULAR': 0,
            }

            for i, tarefa in enumerate(tarefas, 1):
                self.stdout.write(self.style.HTTP_INFO(f'\n[{i}] Protocolo: {tarefa.numero_protocolo_tarefa}'))
                resultado = self.testar_tarefa(analisador, tarefa, exibir_detalhes=False)
                nivel = resultado['nivel']
                contador[nivel] = contador.get(nivel, 0) + 1

            # Exibir resumo
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('=' * 70))
            self.stdout.write(self.style.SUCCESS('RESUMO DA ANÁLISE'))
            self.stdout.write(self.style.SUCCESS('=' * 70))
            self.stdout.write(f'Total analisado: {len(tarefas)}')
            self.stdout.write('')
            self.stdout.write('Por Nível:')
            self.stdout.write(f'  ⛔ CRÍTICA: {contador["CRÍTICA"]}')
            self.stdout.write(f'  📋 JUSTIFICADA: {contador["JUSTIFICADA"]}')
            self.stdout.write(f'  ⊘ EXCLUÍDA: {contador["EXCLUÍDA"]}')
            self.stdout.write(f'  ✅ REGULAR: {contador["REGULAR"]}')

    def testar_tarefa(self, analisador, tarefa, exibir_detalhes=True):
        """Testa o analisador em uma tarefa específica"""
        resultado = analisador.analisar_tarefa(tarefa)

        # Colorir por nível
        nivel_style = {
            'CRÍTICA': self.style.ERROR,
            'JUSTIFICADA': self.style.HTTP_INFO,
            'EXCLUÍDA': self.style.HTTP_NOT_MODIFIED,
            'REGULAR': self.style.SUCCESS,
        }

        style = nivel_style.get(resultado['nivel'], self.style.SUCCESS)

        if exibir_detalhes:
            self.stdout.write(self.style.SUCCESS('✓ Análise realizada!'))
            self.stdout.write(f'  Servidor: {tarefa.nome_profissional_responsavel}')
            self.stdout.write(f'  Serviço: {tarefa.nome_servico}')
        
        self.stdout.write(f'  Regra: {resultado["regra"]}')
        self.stdout.write(style(f'  Nível: {resultado["nivel"]}'))
        self.stdout.write(f'  Alerta: {resultado["alerta"]}')

        if exibir_detalhes:
            self.stdout.write(f'  Descrição: {resultado["descricao"]}')

        return resultado