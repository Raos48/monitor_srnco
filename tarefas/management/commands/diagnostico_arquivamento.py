"""
Comando para diagnosticar o estado das tarefas arquivadas.
Verifica se o processo de arquivamento automatico esta funcionando corretamente.

Uso:
    python manage.py diagnostico_arquivamento
"""
from django.core.management.base import BaseCommand
from django.db.models import Count, Q
from tarefas.models import Tarefa
from importar_csv.models import RegistroImportacao


class Command(BaseCommand):
    help = 'Diagnostica o estado das tarefas arquivadas e verifica o processo de arquivamento'

    def handle(self, *args, **options):
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("DIAGNOSTICO DE ARQUIVAMENTO DE TAREFAS")
        self.stdout.write("=" * 80 + "\n")

        # 1. Estatisticas Gerais
        self.stdout.write(self.style.SUCCESS("\n[ESTATISTICAS GERAIS]"))
        self.stdout.write("-" * 80)

        total_tarefas = Tarefa.objects.count()
        tarefas_ativas = Tarefa.objects.filter(ativa=True).count()
        tarefas_arquivadas = Tarefa.objects.filter(ativa=False).count()

        self.stdout.write(f"Total de tarefas no banco: {total_tarefas:,}")
        self.stdout.write(f"  - Ativas (ativa=True):      {tarefas_ativas:,} ({(tarefas_ativas/total_tarefas*100):.1f}%)")
        self.stdout.write(f"  - Arquivadas (ativa=False): {tarefas_arquivadas:,} ({(tarefas_arquivadas/total_tarefas*100):.1f}%)")

        # 2. Historico de Importacoes
        self.stdout.write(self.style.SUCCESS("\n[HISTORICO DE IMPORTACOES]"))
        self.stdout.write("-" * 80)

        importacoes = RegistroImportacao.objects.filter(status='COMPLETED').order_by('-data_importacao')[:5]

        if importacoes.exists():
            self.stdout.write(f"Ultimas {importacoes.count()} importacoes concluidas:\n")
            for i, imp in enumerate(importacoes, 1):
                self.stdout.write(
                    f"{i}. {imp.data_importacao.strftime('%d/%m/%Y %H:%M')} - "
                    f"{imp.nome_arquivo} - "
                    f"{imp.registros_criados:,} criadas, {imp.registros_atualizados:,} atualizadas"
                )
        else:
            self.stdout.write(self.style.WARNING("AVISO: Nenhuma importacao concluida encontrada!"))

        # 3. Verificar ultima importacao
        self.stdout.write(self.style.SUCCESS("\n[ANALISE DA ULTIMA IMPORTACAO]"))
        self.stdout.write("-" * 80)

        ultima_importacao = RegistroImportacao.objects.filter(status='COMPLETED').order_by('-data_importacao').first()

        if ultima_importacao:
            self.stdout.write(f"Data: {ultima_importacao.data_importacao.strftime('%d/%m/%Y %H:%M')}")
            self.stdout.write(f"Arquivo: {ultima_importacao.nome_arquivo}")
            self.stdout.write(f"Linhas processadas: {ultima_importacao.total_linhas:,}")
            self.stdout.write(f"Tarefas criadas: {ultima_importacao.registros_criados:,}")
            self.stdout.write(f"Tarefas atualizadas: {ultima_importacao.registros_atualizados:,}")

            # Total esperado no CSV
            total_csv = ultima_importacao.registros_criados + ultima_importacao.registros_atualizados
            self.stdout.write(f"\nTotal de tarefas unicas no ultimo CSV: {total_csv:,}")

            # Comparar com tarefas ativas
            diferenca = tarefas_ativas - total_csv

            if diferenca > 0:
                self.stdout.write(
                    self.style.WARNING(
                        f"\nATENCAO: Ha {diferenca:,} tarefas ativas a mais do que o esperado!"
                    )
                )
                self.stdout.write(
                    "   Isso pode indicar que o arquivamento automatico nao esta funcionando."
                )
            elif diferenca < 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"\nOK: Ha {abs(diferenca):,} tarefas a menos (arquivadas corretamente)"
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        "\nOK: Total de tarefas ativas corresponde ao ultimo CSV importado"
                    )
                )
        else:
            self.stdout.write(self.style.WARNING("AVISO: Nenhuma importacao concluida encontrada!"))

        # 4. Distribuicao por Status de Ativa
        self.stdout.write(self.style.SUCCESS("\n[DISTRIBUICAO POR TIPO DE FILA - Apenas Ativas]"))
        self.stdout.write("-" * 80)

        distribuicao_fila = Tarefa.objects.filter(ativa=True).values('tipo_fila').annotate(
            total=Count('numero_protocolo_tarefa')
        ).order_by('-total')

        for fila in distribuicao_fila:
            tipo = fila['tipo_fila'] or 'SEM FILA'
            self.stdout.write(f"{tipo}: {fila['total']:,} tarefas")

        # 5. Tarefas Arquivadas por Data
        self.stdout.write(self.style.SUCCESS("\n[ANALISE DE TAREFAS ARQUIVADAS]"))
        self.stdout.write("-" * 80)

        if tarefas_arquivadas > 0:
            # Mostrar algumas tarefas arquivadas como exemplo
            exemplos = Tarefa.objects.filter(ativa=False).order_by('-data_ultima_atualizacao')[:10]

            self.stdout.write(f"Exemplos de tarefas arquivadas (ultimas 10 por data de atualizacao):\n")
            for t in exemplos:
                self.stdout.write(
                    f"  - Protocolo: {t.numero_protocolo_tarefa} | "
                    f"Ultima atualizacao: {t.data_ultima_atualizacao.strftime('%d/%m/%Y') if t.data_ultima_atualizacao else 'N/A'} | "
                    f"Status: {t.status_tarefa}"
                )
        else:
            self.stdout.write(self.style.WARNING("AVISO: Nenhuma tarefa arquivada encontrada!"))
            self.stdout.write(
                "\nIsso indica que o processo de arquivamento automatico pode nao estar funcionando.\n"
                "Verifique se o worker do django-background-tasks esta rodando corretamente."
            )

        # 6. Recomendacoes
        self.stdout.write(self.style.SUCCESS("\n[RECOMENDACOES]"))
        self.stdout.write("-" * 80)

        if tarefas_arquivadas == 0 and total_tarefas > 100000:
            self.stdout.write(
                self.style.WARNING(
                    "ACAO NECESSARIA: Nao ha tarefas arquivadas, mas ha muitas tarefas no banco."
                )
            )
            self.stdout.write("\nPara corrigir:")
            self.stdout.write("1. Verifique se o worker esta rodando: python manage.py process_tasks")
            self.stdout.write("2. Faca uma nova importacao de CSV para acionar o arquivamento automatico")
            self.stdout.write("3. Ou execute: python manage.py recalcular_tarefas (se disponivel)")

        elif ultima_importacao and diferenca > 10000:
            self.stdout.write(
                self.style.WARNING(
                    f"ACAO NECESSARIA: Ha {diferenca:,} tarefas a mais do que o esperado."
                )
            )
            self.stdout.write("\nPossiveis causas:")
            self.stdout.write("1. O codigo de arquivamento nao foi executado na ultima importacao")
            self.stdout.write("2. O worker nao estava rodando durante a importacao")
            self.stdout.write("3. Houve um erro durante o processo de arquivamento")
            self.stdout.write("\nVerifique os logs da ultima importacao no Django Admin.")

        else:
            self.stdout.write(
                self.style.SUCCESS(
                    "OK: O sistema parece estar funcionando corretamente!"
                )
            )

        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("FIM DO DIAGNOSTICO")
        self.stdout.write("=" * 80 + "\n")
