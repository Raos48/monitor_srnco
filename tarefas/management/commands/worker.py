"""
Comando customizado para executar o worker de tarefas em segundo plano
com mensagens informativas e status visível.

Uso:
    python manage.py worker
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
import sys
import time


class Command(BaseCommand):
    help = 'Inicia o worker de processamento de tarefas em segundo plano com logs informativos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--duration',
            type=int,
            default=0,
            help='Duração em segundos para executar (0 = executar indefinidamente)'
        )
        parser.add_argument(
            '--sleep',
            type=int,
            default=5,
            help='Tempo de espera entre verificações em segundos (padrão: 5)'
        )

    def handle(self, *args, **options):
        from background_task.models import Task

        duration = options['duration']
        sleep_time = options['sleep']

        # Banner de inicialização
        self.stdout.write("\n" + "="*80)
        self.stdout.write(self.style.SUCCESS(">>> WORKER DE IMPORTACAO ASSINCRONA - MONITOR SRNCO <<<"))
        self.stdout.write("="*80)
        self.stdout.write(f"[*] Iniciado em: {timezone.now().strftime('%d/%m/%Y %H:%M:%S')}")
        self.stdout.write(f"[*] Intervalo de verificacao: {sleep_time} segundos")
        if duration > 0:
            self.stdout.write(f"[*] Duracao: {duration} segundos")
        else:
            self.stdout.write("[*] Duracao: Executar indefinidamente (Ctrl+C para parar)")
        self.stdout.write("="*80 + "\n")

        self.stdout.write(self.style.WARNING("[OK] Worker ATIVO - Monitorando fila de tarefas..."))
        self.stdout.write(self.style.WARNING("     Aguardando importacoes de CSV...\n"))

        # Importar o processo de tasks
        from django.core.management import call_command

        # Contador de verificações
        check_count = 0
        last_task_count = 0

        try:
            while True:
                check_count += 1

                # Verificar tarefas pendentes
                pending_tasks = Task.objects.filter(failed_at__isnull=True, locked_at__isnull=True).count()
                running_tasks = Task.objects.filter(locked_at__isnull=False).count()

                # Mostrar status a cada 10 verificações (ou quando houver mudança)
                if check_count % 10 == 0 or pending_tasks != last_task_count:
                    timestamp = timezone.now().strftime('%H:%M:%S')

                    if pending_tasks > 0 or running_tasks > 0:
                        self.stdout.write(
                            f"[{timestamp}] "
                            f"{self.style.SUCCESS('[PROCESSANDO]')}: "
                            f"{running_tasks} em execucao | "
                            f"{pending_tasks} na fila"
                        )
                    else:
                        self.stdout.write(
                            f"[{timestamp}] "
                            f"{self.style.WARNING('[AGUARDANDO]')}: Nenhuma tarefa na fila"
                        )

                    last_task_count = pending_tasks

                # Processar tarefas
                call_command('process_tasks', '--duration', str(sleep_time))

                # Verificar se deve parar
                if duration > 0 and check_count * sleep_time >= duration:
                    break

        except KeyboardInterrupt:
            self.stdout.write("\n" + "="*80)
            self.stdout.write(self.style.WARNING("[!] Recebido sinal de interrupcao (Ctrl+C)"))
            self.stdout.write(self.style.SUCCESS("[OK] Worker finalizado com sucesso"))
            self.stdout.write(f"[*] Encerrado em: {timezone.now().strftime('%d/%m/%Y %H:%M:%S')}")
            self.stdout.write(f"[*] Total de verificacoes: {check_count}")
            self.stdout.write("="*80 + "\n")
            sys.exit(0)
        except Exception as e:
            self.stdout.write("\n" + "="*80)
            self.stdout.write(self.style.ERROR(f"[ERRO] ERRO NO WORKER: {str(e)}"))
            self.stdout.write("="*80 + "\n")
            raise

        # Finalização normal (se duration foi especificado)
        self.stdout.write("\n" + "="*80)
        self.stdout.write(self.style.SUCCESS("[OK] Worker finalizado (duracao atingida)"))
        self.stdout.write(f"[*] Encerrado em: {timezone.now().strftime('%d/%m/%Y %H:%M:%S')}")
        self.stdout.write(f"[*] Total de verificacoes: {check_count}")
        self.stdout.write("="*80 + "\n")
