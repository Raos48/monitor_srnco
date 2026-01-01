"""
Comando para popular a tabela ConfiguracaoFila com as configuracoes iniciais
baseadas nas regras hardcoded existentes no metodo classificar_fila().

Este comando deve ser executado APENAS UMA VEZ apos criar a tabela ConfiguracaoFila.

Uso:
    python manage.py popular_configuracoes_filas
"""
from django.core.management.base import BaseCommand
from tarefas.models import ConfiguracaoFila


class Command(BaseCommand):
    help = 'Popula a tabela ConfiguracaoFila com configuracoes iniciais'

    def handle(self, *args, **options):
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("POPULACAO INICIAL DE CONFIGURACOES DE FILAS")
        self.stdout.write("=" * 80 + "\n")

        # Limpar configurações existentes
        total_existentes = ConfiguracaoFila.objects.count()
        if total_existentes > 0:
            self.stdout.write(
                self.style.WARNING(
                    f"\nATENCAO: Ja existem {total_existentes} configuracao(oes) no banco."
                )
            )
            resposta = input("\nDeseja limpar e recriar todas as configuracoes? (s/N): ")

            if resposta.lower() != 's':
                self.stdout.write(self.style.ERROR("\nOperacao cancelada pelo usuario."))
                return

            ConfiguracaoFila.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f"{total_existentes} configuracao(oes) removida(s)."))

        # Contador de registros criados
        total_criados = 0

        # ==================================================================
        # FILA: CEABRD-23150521 (Beneficios Regulares/Diretos)
        # ==================================================================
        self.stdout.write("\n[1/7] Populando CEABRD-23150521...")

        servicos_ceabrd = [
            'Aposentadoria da Pessoa com Deficiencia por Idade',
            'Aposentadoria da Pessoa com Deficiencia por Tempo de Contribuicao',
            'Aposentadoria por Idade Rural',
            'Aposentadoria por Idade Urbana',
            'Aposentadoria por Tempo de Contribuicao',
            'Cancelar Certidao de Tempo de Contribuicao',
            'Certidao de Tempo de Contribuicao',
            'Peculio',
            'Acerto para Integracao - SIBE',
            'Acertos para analise',
            'Auxilio-Acidente',
            'Antecipacao de beneficio assistencial (B16)',
            'Beneficio Assistencial a Pessoa com Deficiencia',
            'Beneficio Assistencial a Pessoa com Deficiencia - Microcefalia',
            'Beneficio Assistencial ao Idoso',
            'Beneficio Assistencial ao Trabalhador Portuario Avulso',
            'Auxilio-Reclusao Rural',
            'Auxilio-Reclusao Urbano',
            'Pensao Especial - Criancas com Sindrome Congenita do Zika Virus',
            'Pensao Especial - Sindrome da Talidomida',
            'Pensao Especial das Vitimas de Hemodialise de Caruaru-PE',
            'Pensao Mensal Vitalicia do Seringueiro (Soldado da Borracha)',
            'Pensao Mensal Vitalicia dos Dependentes de Seringueiro (Soldado da Borracha)',
            'Pensao por Morte Rural',
            'Pensao por Morte Urbana',
            'Salario-Maternidade Rural',
            'Salario-Maternidade Urbano',
            'Revisao',
            'Revisao - Entidade Conveniada',
            'Revisao Administrativa de Beneficio por Incapacidade',
            'Revisao Administrativa em Fase Recursal',
            'Revisao de Certidao de Tempo de Contribuicao',
            'Revisao de Oficio',
            'Revisao Extraordinaria',
            'Revisao Legado',
            'Revisao para COMPREV',
            'Solicitar Contestacao de NTEP',
            'Solicitar Recurso de NTEP',
            'APOSENTADORIA DA PESSOA COM DEFICIENCIA',
            'Aposentadoria por Idade Urbana - Meu INSS',
            'Auxilio-Inclusao a Pessoa com Deficiencia',
        ]

        for servico in servicos_ceabrd:
            ConfiguracaoFila.objects.create(
                nome_servico=servico,
                codigo_unidade=23150521,
                tipo_fila='CEABRD-23150521',
                prioridade=10,
                ativa=True,
                observacoes='Configuracao inicial migrada das regras hardcoded'
            )
            total_criados += 1

        self.stdout.write(f"      {len(servicos_ceabrd)} servicos cadastrados")

        # ==================================================================
        # FILA: CEAB-BI-23150521 (Beneficios por Incapacidade)
        # ==================================================================
        self.stdout.write("\n[2/7] Populando CEAB-BI-23150521...")

        servicos_bi = [
            'Aeronauta Gestante - Auxilio-Doenca',
            'Auxilio-Doenca - Rural (Acerto Pos-pericia)',
            'Auxilio-Doenca - Urbano (Acerto Pos-pericia)',
            'Auxilio-Doenca com Documento Medico (Acao Civil Publica)',
            'Envio de Documentos para Auxilio-Doenca Rural',
            'Pedido de prorrogacao com documento medico',
            'Requerimento de Antecipacao de Pagamento da Revisao do Art. 29',
            'Revisao de Auxilio Doenca com Documento Medico',
            'Solicitacao de Pericia Hospitalar ou Domiciliar',
            'Pendencias Administrativas SABI',
            'Acertos para Analise - BI Urbano',
            'Beneficio por Incapacidade',
            'Acertos para integracao - BI',
            'Acertos para Analise - BI Rural',
            'Revisao de Oficio - Beneficio por Incapacidade',
            'Pedido de Prorrogacao de Beneficio por Incapacidade',
            'Acertos pos-pericia SIBE - Rural',
            'Acertos pos-pericia SIBE - Urbano',
            'Acertos para Marcacao de Pericia Medica',
        ]

        for servico in servicos_bi:
            ConfiguracaoFila.objects.create(
                nome_servico=servico,
                codigo_unidade=23150521,
                tipo_fila='CEAB-BI-23150521',
                prioridade=20,
                ativa=True,
                observacoes='Configuracao inicial migrada das regras hardcoded'
            )
            total_criados += 1

        self.stdout.write(f"      {len(servicos_bi)} servicos cadastrados")

        # ==================================================================
        # FILA: CEAB-RECURSO-23150521 (Recursos)
        # ==================================================================
        self.stdout.write("\n[3/7] Populando CEAB-RECURSO-23150521...")

        servicos_recurso = [
            'Cumprimento de Acordao com Implantacao de Beneficio',
            'Cumprimento de Acordao com Implantacao de Beneficio/BI',
            'Cumprimento de Acordao com Implantacao de Beneficio/Defeso',
            'Cumprimento de Acordao com Implantacao de Beneficio/LOAS',
            'Cumprimento de Acordao de Apuracao de Irregularidade - MOB',
            'Cumprimento de Acordao sem Implantacao de Beneficio',
            'Instrucao de Processo de Recurso',
            'Recurso - Cumprimento de Diligencia',
            'Recurso - Seguro Defeso',
            'Recurso de Beneficio por Incapacidade',
            'Recurso Ordinario (Inicial)',
            'Recurso - Entidade Conveniada',
            'Recurso de Seguro Defeso - Entidade Conveniada',
            'Recurso Especial - Entidade Conveniada',
            'Recurso - Acordao com Implantacao de Beneficio/Aposentadorias',
            'Recurso - Acordao com Implantacao de Beneficio/BI',
            'Recurso - Acordao com Implantacao de Beneficio/Defeso',
            'Recurso - Acordao com Implantacao de Beneficio/LOAS',
            'Recurso - Acordao com Implantacao de Beneficio/Outros',
            'Recurso - Acordao com Implantacao de Beneficio/Pensoes',
            'Recurso - Acordao sem Implantacao de Beneficio',
        ]

        for servico in servicos_recurso:
            ConfiguracaoFila.objects.create(
                nome_servico=servico,
                codigo_unidade=23150521,
                tipo_fila='CEAB-RECURSO-23150521',
                prioridade=30,
                ativa=True,
                observacoes='Configuracao inicial migrada das regras hardcoded'
            )
            total_criados += 1

        self.stdout.write(f"      {len(servicos_recurso)} servicos cadastrados")

        # ==================================================================
        # FILA: CEAB-DEFESO-23150521 (Seguro Defeso)
        # ==================================================================
        self.stdout.write("\n[4/7] Populando CEAB-DEFESO-23150521...")

        servicos_defeso = [
            'Reemitir Parcelas - Seguro Defeso',
            'Seguro Defeso - Pescador Artesanal',
            'Seguro Defeso - Protocolo em Contingencia',
            'Monitorar e Acompanhar o Processamento de Tarefas de SD',
        ]

        for servico in servicos_defeso:
            ConfiguracaoFila.objects.create(
                nome_servico=servico,
                codigo_unidade=23150521,
                tipo_fila='CEAB-DEFESO-23150521',
                prioridade=40,
                ativa=True,
                observacoes='Configuracao inicial migrada das regras hardcoded'
            )
            total_criados += 1

        self.stdout.write(f"      {len(servicos_defeso)} servicos cadastrados")

        # ==================================================================
        # FILA: CEAB-COMPREV-23150521 (Compensacao Previdenciaria)
        # ==================================================================
        self.stdout.write("\n[5/7] Populando CEAB-COMPREV-23150521...")

        servicos_comprev = [
            'Compensacao Previdenciaria - COMPREV-RI',
            'Compensacao Previdenciaria - COMPREV-RI Integrado',
            'Compensacao Previdenciaria - COMPREV-RO',
            'Emissao de Certidao de Tempo de Contribuicao - CTC',
            'Exigencias do Ente - COMPREV-RI',
        ]

        for servico in servicos_comprev:
            ConfiguracaoFila.objects.create(
                nome_servico=servico,
                codigo_unidade=23150521,
                tipo_fila='CEAB-COMPREV-23150521',
                prioridade=50,
                ativa=True,
                observacoes='Configuracao inicial migrada das regras hardcoded'
            )
            total_criados += 1

        self.stdout.write(f"      {len(servicos_comprev)} servicos cadastrados")

        # ==================================================================
        # FILA: CEAB-MOB-23150521 (Apuracao de Irregularidades)
        # ==================================================================
        self.stdout.write("\n[6/7] Populando CEAB-MOB-23150521...")

        servicos_mob = [
            'Apuracao Batimento Continuo/MDS - Decreto no 9.462/2018',
            'Apuracao de Irregularidade - Forca Tarefa Previdenciaria',
            'Apuracao de Irregularidade - MCC DIRBEN/DIRAT no 52 - Renda Mensal Divergente',
            'Apuracao de Irregularidades',
            'Apuracao de Irregularidade - Acordao TCU no 1058/2017',
        ]

        for servico in servicos_mob:
            ConfiguracaoFila.objects.create(
                nome_servico=servico,
                codigo_unidade=23150521,
                tipo_fila='CEAB-MOB-23150521',
                prioridade=60,
                ativa=True,
                observacoes='Configuracao inicial migrada das regras hardcoded'
            )
            total_criados += 1

        self.stdout.write(f"      {len(servicos_mob)} servicos cadastrados")

        # ==================================================================
        # FILA: PGB (Regra especial por codigo de unidade)
        # ==================================================================
        self.stdout.write("\n[7/7] Criando regra especial para PGB...")

        # Nao precisamos criar registro para cada servico, pois a regra PGB
        # e baseada apenas no codigo_unidade = 23150003
        # A regra hardcoded ja cuida disso

        self.stdout.write("      Regra mantida como hardcoded (baseada em codigo_unidade)")

        # ==================================================================
        # RESUMO FINAL
        # ==================================================================
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("RESUMO DA POPULACAO")
        self.stdout.write("=" * 80)

        self.stdout.write(f"\nTotal de configuracoes criadas: {total_criados}")

        # Mostrar distribuicao por fila
        distribuicao = {}
        for config in ConfiguracaoFila.objects.all():
            if config.tipo_fila not in distribuicao:
                distribuicao[config.tipo_fila] = 0
            distribuicao[config.tipo_fila] += 1

        self.stdout.write("\nDistribuicao por fila:")
        for fila, qtd in sorted(distribuicao.items()):
            self.stdout.write(f"  - {fila}: {qtd} servicos")

        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(self.style.SUCCESS("POPULACAO CONCLUIDA COM SUCESSO!"))
        self.stdout.write("=" * 80)

        self.stdout.write(
            "\nProximos passos:"
            "\n1. Acesse o Django Admin em /admin/tarefas/configuracaofila/"
            "\n2. Revise as configuracoes criadas"
            "\n3. Adicione, edite ou remova configuracoes conforme necessario"
            "\n4. Execute 'python manage.py calcular_tipo_fila' para recalcular todas as tarefas\n"
        )
