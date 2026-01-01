"""
Comando para arquivar manualmente tarefas que nao estao no ultimo CSV importado.

Este comando deve ser usado APENAS UMA VEZ para corrigir o problema de tarefas
que nao foram arquivadas automaticamente nas importacoes anteriores.

Uso:
    python manage.py arquivar_tarefas_antigas --dry-run  # Ver o que seria arquivado
    python manage.py arquivar_tarefas_antigas --confirmar  # Arquivar de verdade
"""
from django.core.management.base import BaseCommand
from tarefas.models import Tarefa
from importar_csv.models import RegistroImportacao
import csv
import os


class Command(BaseCommand):
    help = 'Arquiva tarefas que nao estao no ultimo CSV importado'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula o arquivamento sem modificar o banco de dados'
        )
        parser.add_argument(
            '--confirmar',
            action='store_true',
            help='CONFIRMA o arquivamento (modifica o banco de dados)'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        confirmar = options['confirmar']

        if not dry_run and not confirmar:
            self.stdout.write(
                self.style.ERROR(
                    "\nERRO: Voce deve especificar --dry-run ou --confirmar"
                )
            )
            self.stdout.write("\nExemplos:")
            self.stdout.write("  python manage.py arquivar_tarefas_antigas --dry-run")
            self.stdout.write("  python manage.py arquivar_tarefas_antigas --confirmar\n")
            return

        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("ARQUIVAMENTO MANUAL DE TAREFAS ANTIGAS")
        self.stdout.write("=" * 80 + "\n")

        # 1. Buscar ultima importacao concluida
        self.stdout.write("[1/4] Buscando ultima importacao concluida...")

        ultima_importacao = RegistroImportacao.objects.filter(
            status='COMPLETED'
        ).order_by('-data_importacao').first()

        if not ultima_importacao:
            self.stdout.write(self.style.ERROR("ERRO: Nenhuma importacao concluida encontrada!"))
            return

        self.stdout.write(f"      Encontrada: {ultima_importacao.nome_arquivo}")
        self.stdout.write(f"      Data: {ultima_importacao.data_importacao.strftime('%d/%m/%Y %H:%M')}")

        # 2. Ler arquivo CSV para obter lista de protocolos
        self.stdout.write("\n[2/4] Lendo arquivo CSV da ultima importacao...")

        if not os.path.exists(ultima_importacao.caminho_arquivo):
            self.stdout.write(
                self.style.ERROR(
                    f"ERRO: Arquivo nao encontrado: {ultima_importacao.caminho_arquivo}"
                )
            )
            self.stdout.write("\nSolucao: Faca uma nova importacao de CSV e execute este comando novamente.")
            return

        # Ler protocolos do CSV
        protocolos_csv = set()

        try:
            with open(ultima_importacao.caminho_arquivo, 'r', encoding='latin-1') as arquivo:
                reader = csv.reader(arquivo, delimiter=',')
                next(reader)  # Pular cabecalho

                for row in reader:
                    if len(row) > 0:
                        protocolo = row[0].strip('"').strip()
                        if protocolo:
                            protocolos_csv.add(protocolo)

            self.stdout.write(f"      Protocolos encontrados no CSV: {len(protocolos_csv):,}")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"ERRO ao ler CSV: {str(e)}"))
            return

        # 3. Identificar tarefas para arquivar
        self.stdout.write("\n[3/4] Identificando tarefas para arquivar...")

        tarefas_ativas_antes = Tarefa.objects.filter(ativa=True).count()
        self.stdout.write(f"      Tarefas ativas no banco: {tarefas_ativas_antes:,}")

        # Buscar tarefas que estao ativas mas NAO estao no CSV
        tarefas_para_arquivar = Tarefa.objects.filter(
            ativa=True
        ).exclude(
            numero_protocolo_tarefa__in=protocolos_csv
        )

        qtd_arquivar = tarefas_para_arquivar.count()

        self.stdout.write(f"      Tarefas a arquivar: {qtd_arquivar:,}")

        if qtd_arquivar == 0:
            self.stdout.write(
                self.style.SUCCESS(
                    "\nSucesso: Nenhuma tarefa precisa ser arquivada. "
                    "Todas as tarefas ativas estao no ultimo CSV!"
                )
            )
            return

        # Mostrar exemplos
        exemplos = tarefas_para_arquivar[:10]
        self.stdout.write("\n      Exemplos de tarefas que serao arquivadas:")
        for t in exemplos:
            self.stdout.write(
                f"        - {t.numero_protocolo_tarefa} | "
                f"{t.nome_servico[:50] if t.nome_servico else 'N/A'} | "
                f"Status: {t.status_tarefa}"
            )

        if qtd_arquivar > 10:
            self.stdout.write(f"        ... e mais {qtd_arquivar - 10:,} tarefas")

        # 4. Executar arquivamento (se confirmado)
        self.stdout.write("\n[4/4] Executando arquivamento...")

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"\n  SIMULACAO (--dry-run): {qtd_arquivar:,} tarefas SERIAM arquivadas"
                )
            )
            self.stdout.write(
                "\n  Para arquivar de verdade, execute:\n"
                "  python manage.py arquivar_tarefas_antigas --confirmar\n"
            )

        elif confirmar:
            self.stdout.write(
                self.style.WARNING(
                    f"\n  ATENCAO: Arquivando {qtd_arquivar:,} tarefas..."
                )
            )

            # Executar update em lote
            tarefas_para_arquivar.update(ativa=False)

            # Confirmar resultado
            tarefas_ativas_depois = Tarefa.objects.filter(ativa=True).count()
            tarefas_arquivadas_total = Tarefa.objects.filter(ativa=False).count()

            self.stdout.write(
                self.style.SUCCESS(
                    f"\n  SUCESSO: {qtd_arquivar:,} tarefas foram arquivadas!"
                )
            )

            self.stdout.write("\n  Resumo final:")
            self.stdout.write(f"    - Tarefas ativas antes: {tarefas_ativas_antes:,}")
            self.stdout.write(f"    - Tarefas ativas agora: {tarefas_ativas_depois:,}")
            self.stdout.write(f"    - Total arquivadas: {tarefas_arquivadas_total:,}")

            # Validar resultado
            if tarefas_ativas_depois == len(protocolos_csv):
                self.stdout.write(
                    self.style.SUCCESS(
                        f"\n  VALIDACAO OK: Total de tarefas ativas ({tarefas_ativas_depois:,}) "
                        f"corresponde ao ultimo CSV ({len(protocolos_csv):,})"
                    )
                )
            else:
                diferenca = abs(tarefas_ativas_depois - len(protocolos_csv))
                self.stdout.write(
                    self.style.WARNING(
                        f"\n  ATENCAO: Diferenca de {diferenca:,} tarefas. "
                        "Isso pode ser normal se houver duplicatas no CSV."
                    )
                )

        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("FIM DO PROCESSO")
        self.stdout.write("=" * 80 + "\n")
