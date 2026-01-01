"""
Comando para popular a tabela Fila com as filas iniciais do sistema.

Este comando cria os 8 tipos de filas padrão baseadas nas configurações
existentes no arquivo tarefas/filas.py.

Uso:
    python manage.py popular_filas_iniciais
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from tarefas.models import Fila

User = get_user_model()


class Command(BaseCommand):
    help = 'Popula a tabela Fila com as filas iniciais do sistema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Força a recriação sem pedir confirmação',
        )

    def handle(self, *args, **options):
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("POPULAÇÃO INICIAL DE FILAS DO SISTEMA")
        self.stdout.write("=" * 80 + "\n")

        # Buscar usuário admin ou criar um genérico para audit trail
        try:
            usuario_sistema = User.objects.filter(is_superuser=True).first()
            if not usuario_sistema:
                self.stdout.write(
                    self.style.WARNING(
                        "AVISO: Nenhum superusuário encontrado. "
                        "Campos de auditoria ficarão em branco."
                    )
                )
        except Exception:
            usuario_sistema = None

        # Limpar filas existentes
        total_existentes = Fila.objects.count()
        if total_existentes > 0:
            self.stdout.write(
                self.style.WARNING(
                    f"\nATENÇÃO: Já existem {total_existentes} fila(s) no banco."
                )
            )

            if not options['force']:
                resposta = input("\nDeseja limpar e recriar todas as filas? (s/N): ")
                if resposta.lower() != 's':
                    self.stdout.write(self.style.ERROR("\nOperação cancelada pelo usuário."))
                    return
            else:
                self.stdout.write("\nModo --force ativado. Recriando todas as filas...")

            Fila.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f"{total_existentes} fila(s) removida(s)."))

        # Contador de registros criados
        total_criados = 0

        # ==================================================================
        # DEFINIÇÃO DAS FILAS
        # ==================================================================
        filas_dados = [
            {
                'codigo': 'PGB',
                'nome': 'PGB',
                'nome_completo': 'Programa de Gerenciamento de Benefícios',
                'descricao': 'Tarefas da unidade 23150003 - Processamento e análise de benefícios gerenciados',
                'cor': '#007bff',
                'icone': 'fas fa-building',
                'ordem': 10,
            },
            {
                'codigo': 'CEABRD-23150521',
                'nome': 'CEABRD',
                'nome_completo': 'Central de Análise de Benefícios e Reconhecimento de Direitos',
                'descricao': 'Aposentadorias, Pensões, BPC, Salário-Maternidade, Certidões e Revisões gerais',
                'cor': '#28a745',
                'icone': 'fas fa-user-check',
                'ordem': 20,
            },
            {
                'codigo': 'CEAB-BI-23150521',
                'nome': 'CEAB-BI',
                'nome_completo': 'Central de Análise de Benefícios por Incapacidade',
                'descricao': 'Auxílio-Doença, Perícias Médicas, Acertos Pós-Perícia e Pendências SABI',
                'cor': '#ffc107',
                'icone': 'fas fa-user-injured',
                'ordem': 30,
            },
            {
                'codigo': 'CEAB-RECURSO-23150521',
                'nome': 'CEAB-RECURSO',
                'nome_completo': 'Central de Análise de Recursos',
                'descricao': 'Recursos Ordinários e Especiais, Acórdãos, Cumprimento de Decisões Judiciais',
                'cor': '#dc3545',
                'icone': 'fas fa-gavel',
                'ordem': 40,
            },
            {
                'codigo': 'CEAB-DEFESO-23150521',
                'nome': 'CEAB-DEFESO',
                'nome_completo': 'Central de Análise de Seguro Defeso',
                'descricao': 'Seguro Defeso para Pescador Artesanal e Protocolos em Contingência',
                'cor': '#17a2b8',
                'icone': 'fas fa-fish',
                'ordem': 50,
            },
            {
                'codigo': 'CEAB-COMPREV-23150521',
                'nome': 'CEAB-COMPREV',
                'nome_completo': 'Central de Análise de Compensação Previdenciária',
                'descricao': 'COMPREV-RI, COMPREV-RO, Certidão de Tempo de Contribuição (CTC)',
                'cor': '#6f42c1',
                'icone': 'fas fa-exchange-alt',
                'ordem': 60,
            },
            {
                'codigo': 'CEAB-MOB-23150521',
                'nome': 'CEAB-MOB',
                'nome_completo': 'Central de Análise de Apuração de Irregularidades (MOB)',
                'descricao': 'Apuração de Irregularidades, Força Tarefa, Batimento Contínuo, Acordãos TCU',
                'cor': '#fd7e14',
                'icone': 'fas fa-search',
                'ordem': 70,
            },
            {
                'codigo': 'OUTROS',
                'nome': 'OUTROS',
                'nome_completo': 'Outras Tarefas',
                'descricao': 'Tarefas que não se encaixam nas categorias específicas acima',
                'cor': '#6c757d',
                'icone': 'fas fa-ellipsis-h',
                'ordem': 999,
            },
        ]

        self.stdout.write("\nCriando filas...\n")

        for i, dados in enumerate(filas_dados, 1):
            self.stdout.write(f"[{i}/8] Criando fila '{dados['nome']}'...")

            # Preparar dados com auditoria se disponível
            dados_criacao = dados.copy()
            if usuario_sistema:
                dados_criacao['criado_por'] = usuario_sistema
                dados_criacao['alterado_por'] = usuario_sistema

            fila = Fila.objects.create(**dados_criacao)
            total_criados += 1

            self.stdout.write(
                f"      OK - {dados['codigo']} - {dados['nome_completo']}"
            )

        # ==================================================================
        # RESUMO FINAL
        # ==================================================================
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("RESUMO DA POPULAÇÃO")
        self.stdout.write("=" * 80)

        self.stdout.write(f"\nTotal de filas criadas: {total_criados}")

        # Listar filas criadas
        self.stdout.write("\nFilas ativas no sistema:")
        for fila in Fila.objects.filter(ativa=True).order_by('ordem'):
            self.stdout.write(
                f"  [{fila.ordem:3d}] {fila.codigo:25s} - {fila.nome_completo}"
            )

        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(self.style.SUCCESS("POPULAÇÃO CONCLUÍDA COM SUCESSO!"))
        self.stdout.write("=" * 80)

        self.stdout.write(
            "\nPróximos passos:"
            "\n1. Acesse o Django Admin em /admin/tarefas/fila/"
            "\n2. Revise as filas criadas"
            "\n3. Adicione novas filas ou edite as existentes conforme necessário"
            "\n4. As configurações de serviços já existentes continuam funcionando"
            "\n5. Ao criar novas configurações, o dropdown mostrará estas filas\n"
        )
