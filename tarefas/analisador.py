"""
Analisador de Criticidade de Tarefas INSS
Sistema para análise de tarefas e identificação de níveis de criticidade

Este módulo implementa as 4 regras de negócio documentadas:
- REGRA 1: Exigência Cumprida - Aguardando Análise
- REGRA 2: Cumprimento de Exigência pelo Segurado
- REGRA 3: Tarefa Nunca Trabalhada
- REGRA 4: Exigência Cumprida Antes da Atribuição

Cada regra classifica a tarefa em um dos 5 níveis de severidade:
- CRÍTICA: Prazo severamente excedido
- ALTA: Prazo excedido
- MÉDIA: Próximo do vencimento
- BAIXA: Dentro do prazo mas em observação
- NENHUMA: Regular, dentro dos prazos
"""

from datetime import datetime, timedelta, date
from typing import Dict, Optional
from .parametros import ParametrosAnalise


class AnalisadorCriticidade:
    """
    Classe principal para análise de criticidade de tarefas do INSS.
    
    Esta classe encapsula toda a lógica de negócio para determinar
    o nível de criticidade de uma tarefa com base nas 4 regras estabelecidas.
    
    Attributes:
        parametros (ParametrosAnalise): Parâmetros de prazos configuráveis
        data_referencia (date): Data de referência para cálculos (padrão: hoje)
    """
    
    def __init__(self, parametros: Optional[ParametrosAnalise] = None, data_referencia: Optional[date] = None):
        """
        Inicializa o analisador.
        
        Args:
            parametros: Instância de ParametrosAnalise. Se None, busca a config ativa.
            data_referencia: Data para usar nos cálculos. Se None, usa hoje.
        """
        self.parametros = parametros if parametros else ParametrosAnalise.get_configuracao_ativa()
        self.data_referencia = data_referencia if data_referencia else date.today()
    
    def calcular_dias_diferenca(self, data_inicio: Optional[date], data_fim: Optional[date] = None) -> int:
        """
        Calcula diferença em dias entre duas datas.
        
        Args:
            data_inicio: Data inicial
            data_fim: Data final (padrão: data_referencia)
        
        Returns:
            int: Número de dias de diferença (0 se data_inicio for None)
        """
        if data_inicio is None:
            return 0
        
        if data_fim is None:
            data_fim = self.data_referencia
        
        return (data_fim - data_inicio).days
    
    def aplicar_regra_1(self, tarefa) -> Optional[Dict]:
        """
        REGRA 1: Exigência Cumprida pelo Servidor - Aguardando Análise
        
        Contexto:
            Quando um servidor cadastra uma exigência e o segurado a cumpre,
            o servidor tem um prazo para analisar os documentos apresentados.
        
        Condições de Aplicação:
            - Status: "Pendente"
            - Descrição: "Exigência cumprida"
            - Servidor cadastrou a exigência (data início >= data atribuição)
            - Exigência foi cumprida (data fim preenchida)
        
        Prazos:
            - 7 dias (configurável) após o cumprimento da exigência
        
        Alertas Gerados:
            - <= 7 dias: "Exigência cumprida aguardando análise" (BAIXA)
            - > 7 dias: "Exigência Cumprida sem movimentação" (ALTA)
        
        Args:
            tarefa: Instância do modelo Tarefa
        
        Returns:
            Dict com análise ou None se regra não se aplica
        """
        # Verificar condições básicas
        if tarefa.status_tarefa != 'Pendente':
            return None
        
        if tarefa.descricao_cumprimento_exigencia_tarefa != 'Exigência cumprida':
            return None
        
        # Verificar datas necessárias
        if not tarefa.data_inicio_ultima_exigencia or not tarefa.data_distribuicao_tarefa:
            return None
        
        if not tarefa.data_fim_ultima_exigencia:
            return None
        
        # Verificar se servidor cadastrou a exigência
        if tarefa.data_inicio_ultima_exigencia < tarefa.data_distribuicao_tarefa:
            return None  # Exigência foi cadastrada antes - cai na REGRA 4
        
        # Calcular dias desde o cumprimento
        dias_desde_cumprimento = self.calcular_dias_diferenca(tarefa.data_fim_ultima_exigencia)
        
        # Classificar por severidade
        if dias_desde_cumprimento <= self.parametros.prazo_analise_exigencia_cumprida:
            return {
                'regra': 'REGRA 1',
                'alerta': 'Exigência cumprida aguardando análise do servidor',
                'severidade': 'BAIXA',
                'dias_pendente': dias_desde_cumprimento,
                'prazo_limite': self.parametros.prazo_analise_exigencia_cumprida,
                'detalhes': f'Exigência cumprida há {dias_desde_cumprimento} dias. '
                           f'Prazo para análise: {self.parametros.prazo_analise_exigencia_cumprida} dias.'
            }
        else:
            return {
                'regra': 'REGRA 1',
                'alerta': 'Exigência Cumprida sem movimentação',
                'severidade': 'ALTA',
                'dias_pendente': dias_desde_cumprimento,
                'prazo_limite': self.parametros.prazo_analise_exigencia_cumprida,
                'detalhes': f'Exigência cumprida há {dias_desde_cumprimento} dias. '
                           f'PRAZO EXCEDIDO! Limite: {self.parametros.prazo_analise_exigencia_cumprida} dias.'
            }
    
    def aplicar_regra_2(self, tarefa) -> Optional[Dict]:
        """
        REGRA 2: Cumprimento de Exigência pelo Segurado
        
        Contexto:
            Quando um servidor cadastra uma exigência, o segurado tem 30 dias
            para apresentar os documentos, mais 5 dias de tolerância.
            Após vencimento sem cumprimento, servidor tem 7 dias para concluir.
        
        Condições de Aplicação:
            - Status: "Cumprimento de exigência"
            - Descrição: "Em cumprimento de exigência"
            - Data início exigência preenchida
            - Data fim exigência vazia (não cumprida)
        
        Prazos:
            - Prazo para segurado: Data do prazo + 5 dias (tolerância)
            - Prazo para servidor após vencimento: 7 dias adicionais
        
        Alertas Gerados:
            - Dentro do prazo: "Sem alerta - No prazo" (NENHUMA)
            - 0-7 dias após vencimento: "Prazo vencido - Servidor deve concluir" (MÉDIA)
            - > 7 dias após vencimento: "Prazo de exigência e conclusão vencidos" (CRÍTICA)
        
        Args:
            tarefa: Instância do modelo Tarefa
        
        Returns:
            Dict com análise ou None se regra não se aplica
        """
        # Verificar condições básicas
        if tarefa.status_tarefa != 'Cumprimento de exigência':
            return None
        
        if tarefa.descricao_cumprimento_exigencia_tarefa != 'Em cumprimento de exigência':
            return None
        
        # Verificar data do prazo
        if not tarefa.data_prazo:
            return None
        
        # Calcular prazo real (data prazo + tolerância)
        prazo_real = tarefa.data_prazo + timedelta(days=self.parametros.prazo_tolerancia_exigencia)
        dias_ate_prazo = self.calcular_dias_diferenca(self.data_referencia, prazo_real)
        
        # Ainda no prazo
        if dias_ate_prazo >= 0:
            return {
                'regra': 'REGRA 2',
                'alerta': 'Sem alerta - No prazo para cumprimento de exigência',
                'severidade': 'NENHUMA',
                'dias_pendente': 0,
                'prazo_limite': dias_ate_prazo,
                'detalhes': f'Prazo para cumprimento: {prazo_real.strftime("%d/%m/%Y")}. '
                           f'Faltam {dias_ate_prazo} dias.'
            }
        
        # Prazo vencido
        dias_apos_vencimento = abs(dias_ate_prazo)
        
        # Servidor ainda tem tempo para concluir (0-7 dias após vencimento)
        if dias_apos_vencimento <= self.parametros.prazo_servidor_apos_vencimento:
            prazo_final = prazo_real + timedelta(days=self.parametros.prazo_servidor_apos_vencimento)
            return {
                'regra': 'REGRA 2',
                'alerta': 'Prazo de exigência vencido - Servidor deve concluir',
                'severidade': 'MÉDIA',
                'dias_pendente': dias_apos_vencimento,
                'prazo_limite': self.parametros.prazo_servidor_apos_vencimento,
                'detalhes': f'Prazo vencido há {dias_apos_vencimento} dias. '
                           f'Servidor tem até {prazo_final.strftime("%d/%m/%Y")} para concluir.'
            }
        
        # Prazo totalmente vencido (> 7 dias)
        else:
            return {
                'regra': 'REGRA 2',
                'alerta': 'Prazo de exigência e conclusão vencidos',
                'severidade': 'CRÍTICA',
                'dias_pendente': dias_apos_vencimento,
                'prazo_limite': self.parametros.prazo_servidor_apos_vencimento,
                'detalhes': f'Prazo vencido há {dias_apos_vencimento} dias. '
                           f'CRÍTICO! Ultrapassou prazo do servidor em '
                           f'{dias_apos_vencimento - self.parametros.prazo_servidor_apos_vencimento} dias.'
            }
    
    def aplicar_regra_3(self, tarefa) -> Optional[Dict]:
        """
        REGRA 3: Tarefa Nunca Trabalhada
        
        Contexto:
            Quando um servidor puxa uma tarefa da fila e nunca realizou nenhuma
            ação (não cadastrou exigência, não mudou status, não criou subtarefa).
        
        Condições de Aplicação:
            - Status: "Pendente"
            - Descrição: "Nunca entrou em exigência"
            - Data início exigência: vazia ou zero
        
        Prazos:
            - 10 dias (configurável) após atribuição para primeira ação
        
        Cálculo:
            dias_com_servidor = tempo_em_pendencia - tempo_ate_ultima_distribuicao
        
        Alertas Gerados:
            - <= 10 dias: "Sem alerta - Dentro do prazo inicial" (NENHUMA)
            - > 10 dias: "Puxada sem nenhuma ação - X dias sem movimentação" (ALTA)
        
        Args:
            tarefa: Instância do modelo Tarefa
        
        Returns:
            Dict com análise ou None se regra não se aplica
        """
        # Verificar condições básicas
        if tarefa.status_tarefa != 'Pendente':
            return None
        
        if tarefa.descricao_cumprimento_exigencia_tarefa != 'Nunca entrou em exigência':
            return None
        
        # Verificar que não tem exigência cadastrada
        if tarefa.data_inicio_ultima_exigencia:
            return None
        
        # Calcular dias com o servidor
        dias_com_servidor = tarefa.tempo_em_pendencia_em_dias - tarefa.tempo_ate_ultima_distribuicao_tarefa_em_dias
        
        # Classificar por severidade
        if dias_com_servidor <= self.parametros.prazo_primeira_acao:
            return {
                'regra': 'REGRA 3',
                'alerta': 'Sem alerta - Dentro do prazo inicial',
                'severidade': 'NENHUMA',
                'dias_pendente': dias_com_servidor,
                'prazo_limite': self.parametros.prazo_primeira_acao,
                'detalhes': f'Tarefa com servidor há {dias_com_servidor} dias. '
                           f'Prazo para primeira ação: {self.parametros.prazo_primeira_acao} dias.'
            }
        else:
            return {
                'regra': 'REGRA 3',
                'alerta': f'Puxada sem nenhuma ação - {dias_com_servidor} dias sem movimentação',
                'severidade': 'ALTA',
                'dias_pendente': dias_com_servidor,
                'prazo_limite': self.parametros.prazo_primeira_acao,
                'detalhes': f'Tarefa puxada há {dias_com_servidor} dias sem nenhuma movimentação. '
                           f'PRAZO EXCEDIDO! Limite: {self.parametros.prazo_primeira_acao} dias.'
            }
    
    def aplicar_regra_4(self, tarefa) -> Optional[Dict]:
        """
        REGRA 4: Exigência Cumprida Antes da Atribuição
        
        Contexto:
            Quando um servidor puxa uma tarefa que já estava com exigência cumprida
            (cumprida por outro servidor ou antes da distribuição).
            O servidor tem prazo para analisar os documentos já apresentados.
        
        Condições de Aplicação:
            - Status: "Pendente"
            - Descrição: "Exigência cumprida"
            - Exigência anterior à atribuição (data fim < data atribuição)
        
        Prazos:
            - 10 dias (configurável) após atribuição para análise
        
        Cálculo:
            dias_com_servidor = tempo_em_pendencia - tempo_ate_ultima_distribuicao
        
        Alertas Gerados:
            - <= 10 dias: "Sem alerta - Dentro do prazo de análise" (NENHUMA)
            - > 10 dias: "Exigência cumprida antes da atribuição - sem análise" (ALTA)
        
        Args:
            tarefa: Instância do modelo Tarefa
        
        Returns:
            Dict com análise ou None se regra não se aplica
        """
        # Verificar condições básicas
        if tarefa.status_tarefa != 'Pendente':
            return None
        
        if tarefa.descricao_cumprimento_exigencia_tarefa != 'Exigência cumprida':
            return None
        
        # Verificar datas necessárias
        if not tarefa.data_fim_ultima_exigencia or not tarefa.data_distribuicao_tarefa:
            return None
        
        # Verificar se exigência foi cumprida ANTES da atribuição
        if tarefa.data_fim_ultima_exigencia >= tarefa.data_distribuicao_tarefa:
            return None  # Exigência cumprida depois - cai na REGRA 1
        
        # Calcular dias com o servidor
        dias_com_servidor = tarefa.tempo_em_pendencia_em_dias - tarefa.tempo_ate_ultima_distribuicao_tarefa_em_dias
        
        # Classificar por severidade
        if dias_com_servidor <= self.parametros.prazo_primeira_acao:
            return {
                'regra': 'REGRA 4',
                'alerta': 'Sem alerta - Dentro do prazo de análise',
                'severidade': 'NENHUMA',
                'dias_pendente': dias_com_servidor,
                'prazo_limite': self.parametros.prazo_primeira_acao,
                'detalhes': f'Exigência cumprida antes da atribuição. '
                           f'Servidor com tarefa há {dias_com_servidor} dias. '
                           f'Prazo: {self.parametros.prazo_primeira_acao} dias.'
            }
        else:
            return {
                'regra': 'REGRA 4',
                'alerta': 'Exigência cumprida antes da atribuição - sem análise',
                'severidade': 'ALTA',
                'dias_pendente': dias_com_servidor,
                'prazo_limite': self.parametros.prazo_primeira_acao,
                'detalhes': f'Exigência cumprida antes da atribuição. '
                           f'Servidor com tarefa há {dias_com_servidor} dias sem análise. '
                           f'PRAZO EXCEDIDO! Limite: {self.parametros.prazo_primeira_acao} dias.'
            }
    
    def analisar_tarefa(self, tarefa) -> Dict:
        """
        Analisa uma tarefa individual aplicando todas as regras em ordem de prioridade.
        
        A ordem de aplicação das regras é:
        1. REGRA 1: Exigência cumprida aguardando análise
        2. REGRA 2: Cumprimento de exigência pelo segurado
        3. REGRA 3: Tarefa nunca trabalhada
        4. REGRA 4: Exigência cumprida antes da atribuição
        
        Args:
            tarefa: Instância do modelo Tarefa
        
        Returns:
            Dict contendo:
                - regra: Qual regra foi aplicada (REGRA 1, 2, 3, 4 ou NENHUMA)
                - alerta: Descrição do alerta identificado
                - severidade: Nível de criticidade (CRÍTICA, ALTA, MÉDIA, BAIXA, NENHUMA)
                - dias_pendente: Quantidade de dias em situação irregular
                - prazo_limite: Prazo estabelecido para a ação
                - detalhes: Explicação detalhada da situação
        """
        # Tenta aplicar cada regra em ordem de prioridade
        resultado = self.aplicar_regra_1(tarefa)
        if resultado:
            return resultado
        
        resultado = self.aplicar_regra_2(tarefa)
        if resultado:
            return resultado
        
        resultado = self.aplicar_regra_3(tarefa)
        if resultado:
            return resultado
        
        resultado = self.aplicar_regra_4(tarefa)
        if resultado:
            return resultado
        
        # Nenhuma regra se aplicou
        return {
            'regra': 'NENHUMA',
            'alerta': 'Sem classificação',
            'severidade': 'NENHUMA',
            'dias_pendente': 0,
            'prazo_limite': 0,
            'detalhes': 'Tarefa não se enquadra em nenhuma regra de criticidade.'
        }


def obter_analisador(data_referencia: Optional[date] = None) -> AnalisadorCriticidade:
    """
    Função auxiliar para obter um analisador configurado.
    
    Esta função busca automaticamente a configuração ativa de parâmetros
    e cria uma instância do analisador pronta para uso.
    
    Args:
        data_referencia: Data para usar nos cálculos. Se None, usa hoje.
    
    Returns:
        AnalisadorCriticidade: Instância configurada do analisador
    
    Example:
        >>> analisador = obter_analisador()
        >>> resultado = analisador.analisar_tarefa(tarefa)
        >>> print(resultado['severidade'])  # CRÍTICA, ALTA, MÉDIA, BAIXA ou NENHUMA
    """
    parametros = ParametrosAnalise.get_configuracao_ativa()
    return AnalisadorCriticidade(parametros=parametros, data_referencia=data_referencia)