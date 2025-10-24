"""
Testes Unitários para o Analisador de Criticidade
Valida o funcionamento das 4 regras de análise
"""

from django.test import TestCase
from datetime import date, timedelta
from tarefas.models import Tarefa
from tarefas.parametros import ParametrosAnalise
from tarefas.analisador import AnalisadorCriticidade, obter_analisador
from usuarios.models import CustomUser


class AnalisadorCriticidadeTestCase(TestCase):
    """
    Testes para validar o funcionamento do AnalisadorCriticidade
    """
    
    def setUp(self):
        """
        Configuração inicial dos testes.
        Cria usuário, parâmetros e data de referência para testes.
        """
        # Criar usuário de teste
        self.usuario = CustomUser.objects.create(
            siape='1234567',
            nome_completo='Servidor Teste',
            email='teste@inss.gov.br'
        )
        
        # Criar parâmetros de teste
        self.parametros = ParametrosAnalise.objects.create(
            ativo=True,
            prazo_analise_exigencia_cumprida=7,
            prazo_tolerancia_exigencia=5,
            prazo_servidor_apos_vencimento=7,
            prazo_primeira_acao=10
        )
        
        # Data de referência para testes (22/10/2025)
        self.data_referencia = date(2025, 10, 22)
        
        # Criar analisador
        self.analisador = AnalisadorCriticidade(
            parametros=self.parametros,
            data_referencia=self.data_referencia
        )
    
    def criar_tarefa_base(self):
        """Cria uma tarefa básica para testes"""
        return Tarefa.objects.create(
            numero_protocolo_tarefa='1000000001',
            indicador_subtarefas_pendentes=0,
            codigo_unidade_tarefa=23150003,
            nome_servico='Aposentadoria por Idade',
            status_tarefa='Pendente',
            siape_responsavel=self.usuario,
            nome_profissional_responsavel='Servidor Teste',
            tempo_em_pendencia_em_dias=20,
            tempo_ate_ultima_distribuicao_tarefa_em_dias=10
        )
    
    # ============================================
    # TESTES DA REGRA 1
    # ============================================
    
    def test_regra_1_dentro_prazo(self):
        """
        REGRA 1: Exigência cumprida há 5 dias (dentro do prazo de 7 dias)
        Esperado: BAIXA
        """
        tarefa = self.criar_tarefa_base()
        tarefa.status_tarefa = 'Pendente'
        tarefa.descricao_cumprimento_exigencia_tarefa = 'Exigência cumprida'
        tarefa.data_distribuicao_tarefa = date(2025, 9, 1)
        tarefa.data_inicio_ultima_exigencia = date(2025, 9, 5)
        tarefa.data_fim_ultima_exigencia = date(2025, 10, 17)  # 5 dias atrás
        tarefa.save()
        
        resultado = self.analisador.analisar_tarefa(tarefa)
        
        self.assertEqual(resultado['regra'], 'REGRA 1')
        self.assertEqual(resultado['severidade'], 'BAIXA')
        self.assertEqual(resultado['dias_pendente'], 5)
    
    def test_regra_1_prazo_excedido(self):
        """
        REGRA 1: Exigência cumprida há 15 dias (excedeu prazo de 7 dias)
        Esperado: ALTA
        """
        tarefa = self.criar_tarefa_base()
        tarefa.status_tarefa = 'Pendente'
        tarefa.descricao_cumprimento_exigencia_tarefa = 'Exigência cumprida'
        tarefa.data_distribuicao_tarefa = date(2025, 9, 1)
        tarefa.data_inicio_ultima_exigencia = date(2025, 9, 5)
        tarefa.data_fim_ultima_exigencia = date(2025, 10, 7)  # 15 dias atrás
        tarefa.save()
        
        resultado = self.analisador.analisar_tarefa(tarefa)
        
        self.assertEqual(resultado['regra'], 'REGRA 1')
        self.assertEqual(resultado['severidade'], 'ALTA')
        self.assertEqual(resultado['dias_pendente'], 15)
    
    # ============================================
    # TESTES DA REGRA 2
    # ============================================
    
    def test_regra_2_no_prazo(self):
        """
        REGRA 2: Exigência em cumprimento, ainda no prazo
        Esperado: NENHUMA
        """
        tarefa = self.criar_tarefa_base()
        tarefa.status_tarefa = 'Cumprimento de exigência'
        tarefa.descricao_cumprimento_exigencia_tarefa = 'Em cumprimento de exigência'
        tarefa.data_prazo = date(2025, 11, 5)  # Prazo futuro
        tarefa.save()
        
        resultado = self.analisador.analisar_tarefa(tarefa)
        
        self.assertEqual(resultado['regra'], 'REGRA 2')
        self.assertEqual(resultado['severidade'], 'NENHUMA')
    
    def test_regra_2_vencido_servidor_tem_tempo(self):
        """
        REGRA 2: Exigência vencida há 3 dias (servidor ainda tem 4 dias)
        Esperado: MÉDIA
        """
        tarefa = self.criar_tarefa_base()
        tarefa.status_tarefa = 'Cumprimento de exigência'
        tarefa.descricao_cumprimento_exigencia_tarefa = 'Em cumprimento de exigência'
        # Prazo base: 14/10, com +5 dias = 19/10, venceu há 3 dias
        tarefa.data_prazo = date(2025, 10, 14)
        tarefa.save()
        
        resultado = self.analisador.analisar_tarefa(tarefa)
        
        self.assertEqual(resultado['regra'], 'REGRA 2')
        self.assertEqual(resultado['severidade'], 'MÉDIA')
    
    def test_regra_2_critica(self):
        """
        REGRA 2: Exigência vencida há 15 dias (ultrapassou prazo do servidor)
        Esperado: CRÍTICA
        """
        tarefa = self.criar_tarefa_base()
        tarefa.status_tarefa = 'Cumprimento de exigência'
        tarefa.descricao_cumprimento_exigencia_tarefa = 'Em cumprimento de exigência'
        # Prazo base: 02/10, com +5 dias = 07/10, venceu há 15 dias
        tarefa.data_prazo = date(2025, 10, 2)
        tarefa.save()
        
        resultado = self.analisador.analisar_tarefa(tarefa)
        
        self.assertEqual(resultado['regra'], 'REGRA 2')
        self.assertEqual(resultado['severidade'], 'CRÍTICA')
    
    # ============================================
    # TESTES DA REGRA 3
    # ============================================
    
    def test_regra_3_dentro_prazo(self):
        """
        REGRA 3: Tarefa nunca trabalhada há 8 dias (dentro do prazo de 10)
        Esperado: NENHUMA
        """
        tarefa = self.criar_tarefa_base()
        tarefa.status_tarefa = 'Pendente'
        tarefa.descricao_cumprimento_exigencia_tarefa = 'Nunca entrou em exigência'
        tarefa.tempo_em_pendencia_em_dias = 18
        tarefa.tempo_ate_ultima_distribuicao_tarefa_em_dias = 10
        # dias_com_servidor = 18 - 10 = 8
        tarefa.save()
        
        resultado = self.analisador.analisar_tarefa(tarefa)
        
        self.assertEqual(resultado['regra'], 'REGRA 3')
        self.assertEqual(resultado['severidade'], 'NENHUMA')
        self.assertEqual(resultado['dias_pendente'], 8)
    
    def test_regra_3_prazo_excedido(self):
        """
        REGRA 3: Tarefa nunca trabalhada há 15 dias (excedeu prazo de 10)
        Esperado: ALTA
        """
        tarefa = self.criar_tarefa_base()
        tarefa.status_tarefa = 'Pendente'
        tarefa.descricao_cumprimento_exigencia_tarefa = 'Nunca entrou em exigência'
        tarefa.tempo_em_pendencia_em_dias = 65
        tarefa.tempo_ate_ultima_distribuicao_tarefa_em_dias = 50
        # dias_com_servidor = 65 - 50 = 15
        tarefa.save()
        
        resultado = self.analisador.analisar_tarefa(tarefa)
        
        self.assertEqual(resultado['regra'], 'REGRA 3')
        self.assertEqual(resultado['severidade'], 'ALTA')
        self.assertEqual(resultado['dias_pendente'], 15)
    
    # ============================================
    # TESTES DA REGRA 4
    # ============================================
    
    def test_regra_4_dentro_prazo(self):
        """
        REGRA 4: Exigência cumprida antes da atribuição, há 7 dias com servidor
        Esperado: NENHUMA
        """
        tarefa = self.criar_tarefa_base()
        tarefa.status_tarefa = 'Pendente'
        tarefa.descricao_cumprimento_exigencia_tarefa = 'Exigência cumprida'
        tarefa.data_distribuicao_tarefa = date(2025, 10, 4)
        tarefa.data_inicio_ultima_exigencia = date(2025, 8, 14)
        tarefa.data_fim_ultima_exigencia = date(2025, 9, 6)  # Antes da atribuição
        tarefa.tempo_em_pendencia_em_dias = 67
        tarefa.tempo_ate_ultima_distribuicao_tarefa_em_dias = 60
        # dias_com_servidor = 67 - 60 = 7
        tarefa.save()
        
        resultado = self.analisador.analisar_tarefa(tarefa)
        
        self.assertEqual(resultado['regra'], 'REGRA 4')
        self.assertEqual(resultado['severidade'], 'NENHUMA')
        self.assertEqual(resultado['dias_pendente'], 7)
    
    def test_regra_4_prazo_excedido(self):
        """
        REGRA 4: Exigência cumprida antes da atribuição, há 16 dias com servidor
        Esperado: ALTA
        """
        tarefa = self.criar_tarefa_base()
        tarefa.status_tarefa = 'Pendente'
        tarefa.descricao_cumprimento_exigencia_tarefa = 'Exigência cumprida'
        tarefa.data_distribuicao_tarefa = date(2025, 10, 4)
        tarefa.data_inicio_ultima_exigencia = date(2025, 8, 14)
        tarefa.data_fim_ultima_exigencia = date(2025, 9, 6)  # Antes da atribuição
        tarefa.tempo_em_pendencia_em_dias = 67
        tarefa.tempo_ate_ultima_distribuicao_tarefa_em_dias = 51
        # dias_com_servidor = 67 - 51 = 16
        tarefa.save()
        
        resultado = self.analisador.analisar_tarefa(tarefa)
        
        self.assertEqual(resultado['regra'], 'REGRA 4')
        self.assertEqual(resultado['severidade'], 'ALTA')
        self.assertEqual(resultado['dias_pendente'], 16)
    
    # ============================================
    # TESTES GERAIS
    # ============================================
    
    def test_sem_classificacao(self):
        """
        Tarefa que não se enquadra em nenhuma regra
        Esperado: NENHUMA
        """
        tarefa = self.criar_tarefa_base()
        tarefa.status_tarefa = 'Concluído'
        tarefa.save()
        
        resultado = self.analisador.analisar_tarefa(tarefa)
        
        self.assertEqual(resultado['regra'], 'NENHUMA')
        self.assertEqual(resultado['severidade'], 'NENHUMA')
    
    def test_obter_analisador(self):
        """Testa a função auxiliar obter_analisador"""
        analisador = obter_analisador()
        
        self.assertIsInstance(analisador, AnalisadorCriticidade)
        self.assertIsNotNone(analisador.parametros)
        self.assertEqual(analisador.data_referencia, date.today())
    
    def test_calcular_dias_diferenca(self):
        """Testa o cálculo de diferença entre datas"""
        data_inicio = date(2025, 10, 1)
        data_fim = date(2025, 10, 22)
        
        dias = self.analisador.calcular_dias_diferenca(data_inicio, data_fim)
        
        self.assertEqual(dias, 21)
    
    def test_calcular_dias_diferenca_com_none(self):
        """Testa cálculo de dias com data None"""
        dias = self.analisador.calcular_dias_diferenca(None)
        
        self.assertEqual(dias, 0)


class ParametrosAnaliseTestCase(TestCase):
    """
    Testes para validar o modelo ParametrosAnalise
    """
    
    def test_criar_configuracao_padrao(self):
        """Testa criação de configuração padrão"""
        config = ParametrosAnalise.get_configuracao_ativa()
        
        self.assertIsNotNone(config)
        self.assertTrue(config.ativo)
        self.assertEqual(config.prazo_analise_exigencia_cumprida, 7)
        self.assertEqual(config.prazo_primeira_acao, 10)
    
    def test_validacao_unica_configuracao_ativa(self):
        """Testa que só pode haver uma configuração ativa"""
        from django.core.exceptions import ValidationError
        
        # Criar primeira configuração ativa
        config1 = ParametrosAnalise.objects.create(
            ativo=True,
            prazo_analise_exigencia_cumprida=7
        )
        
        # Tentar criar segunda configuração ativa
        config2 = ParametrosAnalise(
            ativo=True,
            prazo_analise_exigencia_cumprida=10
        )
        
        with self.assertRaises(ValidationError):
            config2.save()
    
    def test_ativar_desativa_outras(self):
        """Testa que ativar uma config desativa as outras"""
        config1 = ParametrosAnalise.objects.create(ativo=True)
        config2 = ParametrosAnalise.objects.create(ativo=False)
        
        config2.ativar()
        config1.refresh_from_db()
        
        self.assertFalse(config1.ativo)
        self.assertTrue(config2.ativo)
    
    def test_duplicar_configuracao(self):
        """Testa duplicação de configuração"""
        config1 = ParametrosAnalise.objects.create(
            ativo=True,
            prazo_analise_exigencia_cumprida=7,
            prazo_primeira_acao=10
        )
        
        config2 = config1.duplicar()
        
        self.assertNotEqual(config1.id, config2.id)
        self.assertFalse(config2.ativo)
        self.assertEqual(config1.prazo_analise_exigencia_cumprida, 
                        config2.prazo_analise_exigencia_cumprida)


# Para executar os testes:
# python manage.py test tarefas.tests.AnalisadorCriticidadeTestCase
# python manage.py test tarefas.tests.ParametrosAnaliseTestCase