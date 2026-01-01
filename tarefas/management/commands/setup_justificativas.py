"""
Comando para configurar tipos padrão de justificativas
"""
from django.core.management.base import BaseCommand
from tarefas.models import TipoJustificativa


class Command(BaseCommand):
    help = 'Configura os tipos padrão de justificativas no sistema'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Configurando Tipos de Justificativas ===\n'))

        tipos_padrao = [
            {
                'nome': 'Indisponibilidade de Sistema',
                'descricao': 'Sistema ou serviço completamente indisponível',
                'ordem': 1
            },
            {
                'nome': 'Lentidão no Sistema',
                'descricao': 'Sistema apresentando lentidão ou degradação de performance',
                'ordem': 2
            },
            {
                'nome': 'Erro de Aplicação',
                'descricao': 'Erro ou bug identificado na aplicação',
                'ordem': 3
            },
            {
                'nome': 'Problema de Infraestrutura',
                'descricao': 'Problemas relacionados a infraestrutura (rede, servidor, etc)',
                'ordem': 4
            },
            {
                'nome': 'Problema de Banco de Dados',
                'descricao': 'Problemas relacionados ao banco de dados',
                'ordem': 5
            },
            {
                'nome': 'Integração Falhou',
                'descricao': 'Falha em integração com sistemas externos',
                'ordem': 6
            },
            {
                'nome': 'Manutenção Programada',
                'descricao': 'Indisponibilidade devido a manutenção programada',
                'ordem': 7
            },
            {
                'nome': 'Incidente de Segurança',
                'descricao': 'Problema relacionado a segurança da informação',
                'ordem': 8
            },
            {
                'nome': 'Sobrecarga do Sistema',
                'descricao': 'Sistema sobrecarregado por alto volume de requisições',
                'ordem': 9
            },
            {
                'nome': 'Outros',
                'descricao': 'Outros tipos de problemas não listados',
                'ordem': 99
            }
        ]

        criados = 0
        atualizados = 0
        erros = 0

        for tipo_data in tipos_padrao:
            try:
                tipo, created = TipoJustificativa.objects.get_or_create(
                    nome=tipo_data['nome'],
                    defaults={
                        'descricao': tipo_data['descricao'],
                        'ordem': tipo_data['ordem'],
                        'ativo': True
                    }
                )
                
                if created:
                    criados += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Criado: {tipo.nome}')
                    )
                else:
                    # Atualiza campos se necessário
                    if tipo.descricao != tipo_data['descricao'] or tipo.ordem != tipo_data['ordem']:
                        tipo.descricao = tipo_data['descricao']
                        tipo.ordem = tipo_data['ordem']
                        tipo.save()
                        atualizados += 1
                        self.stdout.write(
                            self.style.WARNING(f'🔄 Atualizado: {tipo.nome}')
                        )
                    else:
                        self.stdout.write(
                            self.style.NOTICE(f'⏭️  Já existe: {tipo.nome}')
                        )
                        
            except Exception as e:
                erros += 1
                self.stdout.write(
                    self.style.ERROR(f'❌ Erro ao processar "{tipo_data["nome"]}": {str(e)}')
                )

        # Resumo
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS(f'\n📊 RESUMO:'))
        self.stdout.write(f'  ✅ Criados: {criados}')
        self.stdout.write(f'  🔄 Atualizados: {atualizados}')
        
        if erros > 0:
            self.stdout.write(self.style.ERROR(f'  ❌ Erros: {erros}'))
        
        total_tipos = TipoJustificativa.objects.filter(ativo=True).count()
        self.stdout.write(self.style.SUCCESS(f'\n✅ Total de tipos ativos: {total_tipos}\n'))
"""
Comando para configurar tipos padrão de justificativas
"""
from django.core.management.base import BaseCommand
from tarefas.models import TipoJustificativa


class Command(BaseCommand):
    help = 'Configura os tipos padrão de justificativas no sistema'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Configurando Tipos de Justificativas ===\n'))

        tipos_padrao = [
            {
                'nome': 'Indisponibilidade de Sistema',
                'descricao': 'Sistema ou serviço completamente indisponível',
                'ordem_exibicao': 1
            },
            {
                'nome': 'Lentidão no Sistema',
                'descricao': 'Sistema apresentando lentidão ou degradação de performance',
                'ordem_exibicao': 2
            },
            {
                'nome': 'Erro de Aplicação',
                'descricao': 'Erro ou bug identificado na aplicação',
                'ordem_exibicao': 3
            },
            {
                'nome': 'Problema de Infraestrutura',
                'descricao': 'Problemas relacionados a infraestrutura (rede, servidor, etc)',
                'ordem_exibicao': 4
            },
            {
                'nome': 'Problema de Banco de Dados',
                'descricao': 'Problemas relacionados ao banco de dados',
                'ordem_exibicao': 5
            },
            {
                'nome': 'Integração Falhou',
                'descricao': 'Falha em integração com sistemas externos',
                'ordem_exibicao': 6
            },
            {
                'nome': 'Manutenção Programada',
                'descricao': 'Indisponibilidade devido a manutenção programada',
                'ordem_exibicao': 7
            },
            {
                'nome': 'Incidente de Segurança',
                'descricao': 'Problema relacionado a segurança da informação',
                'ordem_exibicao': 8
            },
            {
                'nome': 'Sobrecarga do Sistema',
                'descricao': 'Sistema sobrecarregado por alto volume de requisições',
                'ordem_exibicao': 9
            },
            {
                'nome': 'Outros',
                'descricao': 'Outros tipos de problemas não listados',
                'ordem_exibicao': 99
            }
        ]

        criados = 0
        atualizados = 0
        erros = 0

        for tipo_data in tipos_padrao:
            try:
                tipo, created = TipoJustificativa.objects.get_or_create(
                    nome=tipo_data['nome'],
                    defaults={
                        'descricao': tipo_data['descricao'],
                        'ordem_exibicao': tipo_data['ordem_exibicao'],
                        'ativo': True
                    }
                )
                
                if created:
                    criados += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Criado: {tipo.nome}')
                    )
                else:
                    # Atualiza campos se necessário
                    if tipo.descricao != tipo_data['descricao'] or tipo.ordem_exibicao != tipo_data['ordem_exibicao']:
                        tipo.descricao = tipo_data['descricao']
                        tipo.ordem_exibicao = tipo_data['ordem_exibicao']
                        tipo.save()
                        atualizados += 1
                        self.stdout.write(
                            self.style.WARNING(f'🔄 Atualizado: {tipo.nome}')
                        )
                    else:
                        self.stdout.write(
                            self.style.NOTICE(f'⏭️  Já existe: {tipo.nome}')
                        )
                        
            except Exception as e:
                erros += 1
                self.stdout.write(
                    self.style.ERROR(f'❌ Erro ao processar "{tipo_data["nome"]}": {str(e)}')
                )

        # Resumo
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS(f'\n📊 RESUMO:'))
        self.stdout.write(f'  ✅ Criados: {criados}')
        self.stdout.write(f'  🔄 Atualizados: {atualizados}')
        
        if erros > 0:
            self.stdout.write(self.style.ERROR(f'  ❌ Erros: {erros}'))
        
        total_tipos = TipoJustificativa.objects.filter(ativo=True).count()
        self.stdout.write(self.style.SUCCESS(f'\n✅ Total de tipos ativos: {total_tipos}\n'))