"""
Comando para calcular e atualizar o tipo_fila de todas as tarefas existentes.

Uso:
    python manage.py calcular_tipo_fila
    python manage.py calcular_tipo_fila --batch-size=5000
"""
from django.core.management.base import BaseCommand
from django.db.models import Count
from tarefas.models import Tarefa


class Command(BaseCommand):
    help = 'Calcula e atualiza o tipo_fila de todas as tarefas usando bulk_update'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=2000,
            help='Tamanho do lote para bulk_update (padrão: 2000)'
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']

        self.stdout.write("\n" + "="*80)
        self.stdout.write(self.style.SUCCESS(">>> CALCULO DE TIPO DE FILA PARA TODAS AS TAREFAS <<<"))
        self.stdout.write("="*80)

        # Contar total de tarefas
        total_tarefas = Tarefa.objects.count()
        self.stdout.write(f"[*] Total de tarefas: {total_tarefas:,}")
        self.stdout.write(f"[*] Tamanho do lote: {batch_size:,}")
        self.stdout.write("="*80 + "\n")

        # Processar em lotes
        processadas = 0
        lote_numero = 0

        # Buscar todas as tarefas em lotes
        tarefas_queryset = Tarefa.objects.all().iterator(chunk_size=batch_size)

        tarefas_lote = []
        for tarefa in tarefas_queryset:
            # Classificar a fila
            tarefa.tipo_fila = tarefa.classificar_fila()
            tarefas_lote.append(tarefa)

            # Quando o lote atingir o tamanho especificado, fazer bulk_update
            if len(tarefas_lote) >= batch_size:
                lote_numero += 1
                Tarefa.objects.bulk_update(tarefas_lote, ['tipo_fila'])
                processadas += len(tarefas_lote)

                self.stdout.write(
                    f"[{lote_numero}] Processadas {processadas:,}/{total_tarefas:,} tarefas "
                    f"({(processadas/total_tarefas*100):.1f}%)"
                )

                tarefas_lote = []

        # Processar lote final (se houver)
        if tarefas_lote:
            lote_numero += 1
            Tarefa.objects.bulk_update(tarefas_lote, ['tipo_fila'])
            processadas += len(tarefas_lote)

            self.stdout.write(
                f"[{lote_numero}] Processadas {processadas:,}/{total_tarefas:,} tarefas "
                f"({(processadas/total_tarefas*100):.1f}%)"
            )

        # Estatísticas finais
        self.stdout.write("\n" + "="*80)
        self.stdout.write(self.style.SUCCESS("[OK] CALCULO CONCLUIDO!"))
        self.stdout.write("="*80)

        # Mostrar distribuição por tipo de fila
        self.stdout.write("\n" + self.style.WARNING("[DISTRIBUICAO POR TIPO DE FILA]"))
        self.stdout.write("-"*80)

        distribuicao = Tarefa.objects.values('tipo_fila').annotate(
            total=Count('numero_protocolo_tarefa')
        ).order_by('-total')

        for item in distribuicao:
            fila = item['tipo_fila']
            total = item['total']
            percentual = (total / processadas * 100) if processadas > 0 else 0

            self.stdout.write(
                f"  {fila:25s} | {total:8,} tarefas ({percentual:5.1f}%)"
            )

        self.stdout.write("-"*80 + "\n")
