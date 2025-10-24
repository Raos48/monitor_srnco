"""
Comando Django para importar e-mails de servidores a partir de arquivo Excel.

Uso:
    python manage.py importar_emails "caminho/para/arquivo.xlsx"
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from usuarios.models import EmailServidor
import openpyxl


class Command(BaseCommand):
    help = 'Importa e-mails de servidores a partir de um arquivo Excel'

    def add_arguments(self, parser):
        parser.add_argument(
            'arquivo_excel',
            type=str,
            help='Caminho para o arquivo Excel (.xlsx) com os e-mails'
        )

    def handle(self, *args, **options):
        arquivo_excel = options['arquivo_excel']
        
        self.stdout.write(self.style.WARNING(f'Iniciando importação de: {arquivo_excel}'))
        
        try:
            # Carrega o arquivo Excel
            workbook = openpyxl.load_workbook(arquivo_excel)
            sheet = workbook.active
            
            # Estatísticas
            total_linhas = 0
            criados = 0
            atualizados = 0
            erros = 0
            
            with transaction.atomic():
                # Itera sobre as linhas (pula o cabeçalho)
                for i, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
                    total_linhas += 1
                    
                    # Extrai os dados (MATR, e-mail)
                    # O modelo EmailServidor só tem 'siape' e 'email'.
                    # A coluna 2 (Nome Servidor) será ignorada.
                    siape = str(row[0]).strip() if row[0] is not None else None
                    email = str(row[1]).strip() if row[1] is not None else None
                    
                    # Validação básica
                    if not siape or not email:
                        self.stdout.write(
                            self.style.WARNING(f'  ⚠️ Linha {i}: SIAPE ou e-mail em branco - pulando')
                        )
                        erros += 1
                        continue
                    
                    # Garante que o SIAPE tenha no máximo 7 caracteres (ou 15, conforme seu modelo)
                    # O modelo EmailServidor define max_length=15 para siape
                    if len(siape) > 15:
                        # Tenta pegar apenas os dígitos se for um número longo (ex: 14777.0)
                        if '.' in siape:
                            try:
                                siape = str(int(float(siape)))
                            except ValueError:
                                pass # Mantém o siape original se não for número
                        
                        if len(siape) > 15:
                             self.stdout.write(
                                 self.style.WARNING(f'  ⚠️ Linha {i}: SIAPE "{siape}" muito longo (max 15) - pulando')
                             )
                             erros += 1
                             continue

                    
                    try:
                        # Tenta criar ou atualizar
                        
                        # !!!!! CORREÇÃO !!!!!
                        # O modelo EmailServidor (em usuarios/models.py) SÓ tem
                        # os campos 'siape' e 'email'.
                        # O campo 'nome_servidor' (ou 'nome') não existe nesse modelo.
                        # Portanto, SÓ podemos salvar o e-mail no 'defaults'.
                        
                        defaults_data = {
                            'email': email
                        }
                        
                        email_obj, created = EmailServidor.objects.update_or_create(
                            siape=siape,
                            defaults=defaults_data
                        )
                        
                        if created:
                            criados += 1
                        else:
                            atualizados += 1
                            
                        # Log a cada 100 registros
                        if (total_linhas % 100) == 0:
                            self.stdout.write(f'  Processadas {total_linhas} linhas...')
                    
                    except Exception as e:
                        erros += 1
                        self.stdout.write(
                            self.style.ERROR(f'  ❌ Linha {i} (SIAPE: {siape}): Erro ao processar - {e}')
                        )
            
            # Resumo final
            self.stdout.write(self.style.SUCCESS('\n' + '='*60))
            self.stdout.write(self.style.SUCCESS('IMPORTAÇÃO CONCLUÍDA!'))
            self.stdout.write(self.style.SUCCESS('='*60))
            self.stdout.write(f'📊 Total de linhas processadas: {total_linhas}')
            self.stdout.write(self.style.SUCCESS(f'✅ Registros criados: {criados}'))
            self.stdout.write(self.style.WARNING(f'🔄 Registros atualizados: {atualizados}'))
            if erros > 0:
                self.stdout.write(self.style.ERROR(f'❌ Erros/Linhas puladas: {erros}'))
        
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(f'❌ Arquivo não encontrado: {arquivo_excel}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erro ao processar arquivo: {e}')
            )

