"""
ANALISADOR DE CRITICIDADE DE TAREFAS - VERSÃO ATUALIZADA
Sistema com suporte a:
- Justificativas Aprovadas (tarefas não são CRÍTICAS)
- Serviços Excluídos da Análise
- Parâmetros Configuráveis

Arquivo: tarefas/analisador.py
"""

from datetime import date, timedelta
from django.utils import timezone
from .parametros import ParametrosAnalise
import sys

# Flag para habilitar debug
DEBUG_ANALISADOR = False  # Defina como True para ver depuração detalhada


def _debug_print(msg, protocolo=""):
    """Função auxiliar para debug"""
    if DEBUG_ANALISADOR:
        if protocolo:
            print(f"[DEBUG-{protocolo}] {msg}", flush=True)
        else:
            print(f"[DEBUG] {msg}", flush=True)
        sys.stdout.flush()


class AnalisadorCriticidade:
    """
    Analisador inteligente de criticidade de tarefas com suporte a justificativas.

    IMPORTANTE:
    - Tarefas com justificativa APROVADA não são classificadas como CRÍTICAS
    - Tarefas de serviços excluídos não são analisadas para criticidade
    - Usa parâmetros configuráveis do banco de dados
    """

    # Códigos das regras
    REGRA_1 = "REGRA_1_EXIGENCIA_CUMPRIDA"
    REGRA_2 = "REGRA_2_CUMPRIMENTO_EXIGENCIA"
    REGRA_3 = "REGRA_3_PRIMEIRA_ACAO_SEM_EXIGENCIA"
    REGRA_4 = "REGRA_4_PRIMEIRA_ACAO_COM_EXIGENCIA"
    SEM_REGRA = "SEM_REGRA"

    # Níveis de criticidade
    CRITICA = "CRÍTICA"
    REGULAR = "REGULAR"
    JUSTIFICADA = "JUSTIFICADA"
    EXCLUIDA = "EXCLUÍDA"

    def __init__(self, tarefa):
        """
        Inicializa o analisador para uma tarefa específica.

        Args:
            tarefa: Instância do model Tarefa
        """
        self.tarefa = tarefa
        self.params = ParametrosAnalise.get_configuracao_ativa()
        self.data_atual = date.today()
        self.protocolo = str(tarefa.numero_protocolo_tarefa) if tarefa else ""

        # Inicializa resultado
        self.resultado = {
            'nivel': self.REGULAR,
            'regra': self.SEM_REGRA,
            'dias_pendente': 0,
            'prazo_limite': 0,
            'alerta': '',
            'descricao': '',
            'cor': '#28a745',  # Verde
            'emoji': '✅'
        }

        _debug_print(f"Iniciando análise", self.protocolo)
    
    def analisar(self):
        """
        Realiza análise completa da criticidade da tarefa.

        Returns:
            dict: Resultado da análise com nível, regra, alertas, etc.
        """
        # VERIFICAÇÃO 0: Tarefas com subtarefas são sempre REGULARES
        if self.tarefa.indicador_subtarefas_pendentes and self.tarefa.indicador_subtarefas_pendentes > 0:
            self.resultado['nivel'] = self.REGULAR
            self.resultado['regra'] = 'TEM_SUBTAREFAS'
            self.resultado['alerta'] = '✅ REGULAR: Tarefa possui subtarefas pendentes'
            self.resultado['descricao'] = f'Tarefa com {self.tarefa.indicador_subtarefas_pendentes} subtarefa(s) pendente(s).'
            self.resultado['cor'] = '#28a745'  # Verde
            return self.resultado

        # VERIFICAÇÃO 1: Serviço excluído da análise
        if self.tarefa.servico_excluido_criticidade:
            return self._criar_resultado_excluido()

        # VERIFICAÇÃO 2: Justificativa aprovada
        if self.tarefa.tem_justificativa_ativa:
            return self._criar_resultado_justificado()

        # Calcula dias em pendência
        dias_pendente = self._calcular_dias_pendencia()
        self.resultado['dias_pendente'] = dias_pendente

        # Aplica regras de criticidade na ordem de prioridade
        regras = [
            self._aplicar_regra_1,
            self._aplicar_regra_4,  # Mudei ordem para aplicar REGRA_4 antes de REGRA_2
            self._aplicar_regra_2,
            self._aplicar_regra_3,
        ]

        for regra in regras:
            if regra():
                break

        return self.resultado
    
    def _criar_resultado_excluido(self):
        """Cria resultado para serviço excluído da análise"""
        return {
            'nivel': self.EXCLUIDA,
            'regra': 'SERVICO_EXCLUIDO',
            'dias_pendente': self._calcular_dias_pendencia(),
            'prazo_limite': 0,
            'alerta': 'Serviço excluído da análise de criticidade',
            'descricao': f'O serviço "{self.tarefa.nome_servico}" foi configurado para não ser incluído na análise de criticidade.',
            'cor': '#6c757d',  # Cinza
            'emoji': '⊘'
        }
    
    def _criar_resultado_justificado(self):
        """Cria resultado para tarefa com justificativa aprovada"""
        justificativa = self.tarefa.justificativa_ativa
        
        return {
            'nivel': self.JUSTIFICADA,
            'regra': 'JUSTIFICATIVA_APROVADA',
            'dias_pendente': self._calcular_dias_pendencia(),
            'prazo_limite': 0,
            'alerta': 'Tarefa com justificativa aprovada',
            'descricao': f'Esta tarefa possui justificativa aprovada do tipo "{justificativa.tipo_justificativa.nome}". '
                        f'Aprovada em {justificativa.data_analise.strftime("%d/%m/%Y")} por {justificativa.analisado_por.nome_completo}.',
            'cor': '#17a2b8',  # Azul info
            'emoji': '📋'
        }
    
    def _calcular_dias_pendencia(self):
        """Calcula dias em pendência considerando apenas tempo com servidor"""
        if not self.tarefa.tempo_em_pendencia_em_dias:
            return 0
        
        # Tempo líquido = Pendência total - Tempo em exigência
        tempo_liquido = (
            self.tarefa.tempo_em_pendencia_em_dias - 
            (self.tarefa.tempo_em_exigencia_em_dias or 0)
        )
        
        return max(0, tempo_liquido)
    
    def _aplicar_regra_1(self):
        """
        REGRA 1: Exigência Cumprida - Aguardando Análise do Servidor

        Condições:
        - Status: "Pendente"
        - Descrição contém "Exigência cumprida"
        - Exigência foi CADASTRADA PELO SERVIDOR (data_inicio >= data_atribuicao)
        - Exigência foi CUMPRIDA (tem data_fim)
        - Servidor tem X dias para analisar após cumprimento

        Returns:
            bool: True se a regra foi aplicada
        """
        _debug_print("=== TESTANDO REGRA_1 ===", self.protocolo)

        # Verificar status
        status = (self.tarefa.status_tarefa or '').lower()
        _debug_print(f"Status: {status}", self.protocolo)
        if 'pendente' not in status:
            _debug_print("Status nao e Pendente - REGRA_1 nao se aplica", self.protocolo)
            return False

        # Verificar descrição de cumprimento
        descricao = (self.tarefa.descricao_cumprimento_exigencia_tarefa or '').lower()
        _debug_print(f"Descricao: {descricao}", self.protocolo)
        if 'exigência cumprida' not in descricao and 'exigencia cumprida' not in descricao:
            _debug_print("Descricao nao contem 'Exigencia cumprida' - REGRA_1 nao se aplica", self.protocolo)
            return False

        # Deve ter data de fim de exigência (foi cumprida)
        if not self.tarefa.data_fim_ultima_exigencia:
            _debug_print("Nao tem data_fim_ultima_exigencia - REGRA_1 nao se aplica", self.protocolo)
            return False

        # Deve ter data de início de exigência
        if not self.tarefa.data_inicio_ultima_exigencia:
            _debug_print("Nao tem data_inicio_ultima_exigencia - REGRA_1 nao se aplica", self.protocolo)
            return False

        # Exigência deve ter sido cadastrada APÓS a atribuição (servidor cadastrou)
        if not self.tarefa.data_distribuicao_tarefa:
            _debug_print("Nao tem data_distribuicao_tarefa - REGRA_1 nao se aplica", self.protocolo)
            return False

        _debug_print(f"Data atribuicao: {self.tarefa.data_distribuicao_tarefa}", self.protocolo)
        _debug_print(f"Data inicio exigencia: {self.tarefa.data_inicio_ultima_exigencia}", self.protocolo)
        _debug_print(f"Data fim exigencia: {self.tarefa.data_fim_ultima_exigencia}", self.protocolo)

        if self.tarefa.data_inicio_ultima_exigencia < self.tarefa.data_distribuicao_tarefa:
            # Exigência foi cadastrada ANTES da atribuição - isso é REGRA_4
            _debug_print("Exigencia cadastrada ANTES da atribuicao - e REGRA_4, nao REGRA_1", self.protocolo)
            return False

        prazo_dias = self.params.prazo_analise_exigencia_cumprida
        data_limite = self.tarefa.data_fim_ultima_exigencia + timedelta(days=prazo_dias)
        dias_ate_limite = (data_limite - self.data_atual).days

        _debug_print(f"REGRA_1 APLICADA! Prazo: {prazo_dias} dias, Dias ate limite: {dias_ate_limite}", self.protocolo)

        self.resultado['regra'] = self.REGRA_1
        self.resultado['prazo_limite'] = prazo_dias

        if dias_ate_limite < 0:
            self.resultado['nivel'] = self.CRITICA
            self.resultado['cor'] = '#dc3545'  # Vermelho
            self.resultado['emoji'] = '⛔'
            self.resultado['alerta'] = (
                f'⛔ CRÍTICA: Prazo para análise de exigência cumprida vencido há {abs(dias_ate_limite)} dias'
            )
            self.resultado['descricao'] = (
                f'Servidor cadastrou exigência em {self.tarefa.data_inicio_ultima_exigencia.strftime("%d/%m/%Y")} '
                f'que foi cumprida em {self.tarefa.data_fim_ultima_exigencia.strftime("%d/%m/%Y")}. '
                f'O prazo de {prazo_dias} dias para análise venceu em {data_limite.strftime("%d/%m/%Y")}.'
            )
        else:
            self.resultado['nivel'] = self.REGULAR
            self.resultado['alerta'] = (
                f'✅ REGULAR: Faltam {dias_ate_limite} dias para análise da exigência'
            )
            self.resultado['descricao'] = (
                f'Exigência cumprida em {self.tarefa.data_fim_ultima_exigencia.strftime("%d/%m/%Y")}. '
                f'O servidor tem até {data_limite.strftime("%d/%m/%Y")} para analisar ({dias_ate_limite} dias restantes).'
            )

        return True
    
    def _aplicar_regra_2(self):
        """
        REGRA 2: Cumprimento de Exigência pelo Segurado

        Condições:
        - Tarefa está EM EXIGÊNCIA (tem data_inicio_ultima_exigencia e NÃO tem data_fim)
        - OU status contém "exigência" mas NÃO é "cumprida"
        - Tem data_prazo para calcular vencimento
        - Calcula: data_prazo + tolerância + prazo_servidor

        Returns:
            bool: True se a regra foi aplicada
        """
        # Verificar se está exigência cumprida (já tratada pela regra 1)
        status = (self.tarefa.status_tarefa or '').lower()
        if 'exigência cumprida' in status or 'exigencia cumprida' in status:
            return False

        # Verificar se a tarefa está EM EXIGÊNCIA
        em_exigencia = False

        # Condição 1: Tem data de início de exigência e NÃO tem data de fim
        if self.tarefa.data_inicio_ultima_exigencia and not self.tarefa.data_fim_ultima_exigencia:
            em_exigencia = True

        # Condição 2: Status indica exigência
        if 'exigência' in status or 'exigencia' in status:
            em_exigencia = True

        # Se não está em exigência, não aplica esta regra
        if not em_exigencia:
            return False

        # Deve ter data_prazo para calcular
        if not self.tarefa.data_prazo:
            return False

        tolerancia = self.params.prazo_tolerancia_exigencia
        prazo_servidor = self.params.prazo_servidor_apos_vencimento
        prazo_total = tolerancia + prazo_servidor

        data_limite = self.tarefa.data_prazo + timedelta(days=prazo_total)
        dias_ate_limite = (data_limite - self.data_atual).days

        self.resultado['regra'] = self.REGRA_2
        self.resultado['prazo_limite'] = prazo_total

        if dias_ate_limite < 0:
            self.resultado['nivel'] = self.CRITICA
            self.resultado['cor'] = '#dc3545'
            self.resultado['emoji'] = '⛔'
            self.resultado['alerta'] = (
                f'⛔ CRÍTICA: Prazo total de exigência vencido há {abs(dias_ate_limite)} dias'
            )
            self.resultado['descricao'] = (
                f'Exigência enviada em {self.tarefa.data_inicio_ultima_exigencia.strftime("%d/%m/%Y") if self.tarefa.data_inicio_ultima_exigencia else "data desconhecida"}. '
                f'Prazo para cumprimento: {self.tarefa.data_prazo.strftime("%d/%m/%Y")}. '
                f'Com tolerância de {tolerancia} dias + {prazo_servidor} dias para o servidor analisar, '
                f'o prazo total venceu em {data_limite.strftime("%d/%m/%Y")}. '
                f'Tarefa está {abs(dias_ate_limite)} dias em atraso.'
            )
        else:
            self.resultado['nivel'] = self.REGULAR
            self.resultado['alerta'] = (
                f'✅ REGULAR: Faltam {dias_ate_limite} dias do prazo total da exigência'
            )
            self.resultado['descricao'] = (
                f'Exigência em andamento. Prazo para cumprimento: {self.tarefa.data_prazo.strftime("%d/%m/%Y")}. '
                f'Com tolerância de {tolerancia} dias, o segurado tem até {(self.tarefa.data_prazo + timedelta(days=tolerancia)).strftime("%d/%m/%Y")}. '
                f'Após isso, servidor tem {prazo_servidor} dias adicionais para análise.'
            )

        return True
    
    def _aplicar_regra_3(self):
        """
        REGRA 3: Primeira Ação do Servidor (Tarefa SEM Exigência)
        
        Condições:
        - NÃO tem data de início de exigência
        - Servidor tem X dias desde a distribuição
        
        Returns:
            bool: True se a regra foi aplicada
        """
        # Se tem exigência, não aplica esta regra
        if self.tarefa.data_inicio_ultima_exigencia:
            return False
        
        if not self.tarefa.data_distribuicao_tarefa:
            return False
        
        prazo_dias = self.params.prazo_primeira_acao
        data_limite = self.tarefa.data_distribuicao_tarefa + timedelta(days=prazo_dias)
        dias_ate_limite = (data_limite - self.data_atual).days
        
        self.resultado['regra'] = self.REGRA_3
        self.resultado['prazo_limite'] = prazo_dias
        
        if dias_ate_limite < 0:
            self.resultado['nivel'] = self.CRITICA
            self.resultado['cor'] = '#dc3545'
            self.resultado['emoji'] = '⛔'
            self.resultado['alerta'] = (
                f'⛔ CRÍTICA: Prazo para primeira ação vencido há {abs(dias_ate_limite)} dias'
            )
            self.resultado['descricao'] = (
                f'Tarefa distribuída em {self.tarefa.data_distribuicao_tarefa.strftime("%d/%m/%Y")}. '
                f'O servidor tinha {prazo_dias} dias para realizar a primeira ação. '
                f'Prazo venceu em {data_limite.strftime("%d/%m/%Y")}.'
            )
        else:
            self.resultado['nivel'] = self.REGULAR
            self.resultado['alerta'] = (
                f'✅ REGULAR: Faltam {dias_ate_limite} dias para primeira ação'
            )
            self.resultado['descricao'] = (
                f'Tarefa distribuída em {self.tarefa.data_distribuicao_tarefa.strftime("%d/%m/%Y")}. '
                f'O servidor tem até {data_limite.strftime("%d/%m/%Y")} para primeira ação ({dias_ate_limite} dias restantes).'
            )
        
        return True
    
    def _aplicar_regra_4(self):
        """
        REGRA 4: Exigência Cumprida Anterior (Antes da Atribuição)

        Condições:
        - Status: "Pendente"
        - Descrição contém "Exigência cumprida"
        - Exigência foi CADASTRADA ANTES DA ATRIBUIÇÃO (data_inicio < data_distribuicao)
        - Exigência já estava CUMPRIDA antes da atribuição (data_fim < data_distribuicao)
        - Servidor tem X dias para analisar desde a atribuição

        Returns:
            bool: True se a regra foi aplicada
        """
        _debug_print("=== TESTANDO REGRA_4 ===", self.protocolo)

        # Verificar status
        status = (self.tarefa.status_tarefa or '').lower()
        _debug_print(f"Status: {status}", self.protocolo)
        if 'pendente' not in status:
            _debug_print("Status nao e Pendente - REGRA_4 nao se aplica", self.protocolo)
            return False

        # Verificar descrição de cumprimento
        descricao = (self.tarefa.descricao_cumprimento_exigencia_tarefa or '').lower()
        _debug_print(f"Descricao: {descricao}", self.protocolo)
        if 'exigência cumprida' not in descricao and 'exigencia cumprida' not in descricao:
            _debug_print("Descricao nao contem 'Exigencia cumprida' - REGRA_4 nao se aplica", self.protocolo)
            return False

        # Deve ter data de fim de exigência (foi cumprida)
        if not self.tarefa.data_fim_ultima_exigencia:
            _debug_print("Nao tem data_fim_ultima_exigencia - REGRA_4 nao se aplica", self.protocolo)
            return False

        # Deve ter data de início de exigência
        if not self.tarefa.data_inicio_ultima_exigencia:
            _debug_print("Nao tem data_inicio_ultima_exigencia - REGRA_4 nao se aplica", self.protocolo)
            return False

        # Deve ter data de distribuição
        if not self.tarefa.data_distribuicao_tarefa:
            _debug_print("Nao tem data_distribuicao_tarefa - REGRA_4 nao se aplica", self.protocolo)
            return False

        _debug_print(f"Data atribuicao: {self.tarefa.data_distribuicao_tarefa}", self.protocolo)
        _debug_print(f"Data inicio exigencia: {self.tarefa.data_inicio_ultima_exigencia}", self.protocolo)
        _debug_print(f"Data fim exigencia: {self.tarefa.data_fim_ultima_exigencia}", self.protocolo)

        # Exigência deve ter sido cadastrada ANTES da atribuição (outro servidor cadastrou)
        if self.tarefa.data_inicio_ultima_exigencia >= self.tarefa.data_distribuicao_tarefa:
            # Exigência foi cadastrada DEPOIS da atribuição - isso é REGRA_1
            _debug_print("Exigencia cadastrada DEPOIS da atribuicao - e REGRA_1, nao REGRA_4", self.protocolo)
            return False

        prazo_dias = self.params.prazo_primeira_acao
        data_limite = self.tarefa.data_distribuicao_tarefa + timedelta(days=prazo_dias)
        dias_ate_limite = (data_limite - self.data_atual).days

        _debug_print(f"REGRA_4 APLICADA! Prazo: {prazo_dias} dias, Dias ate limite: {dias_ate_limite}", self.protocolo)

        self.resultado['regra'] = self.REGRA_4
        self.resultado['prazo_limite'] = prazo_dias

        if dias_ate_limite < 0:
            self.resultado['nivel'] = self.CRITICA
            self.resultado['cor'] = '#dc3545'
            self.resultado['emoji'] = '⛔'
            self.resultado['alerta'] = (
                f'⛔ CRÍTICA: Prazo para análise de exigência cumprida anterior vencido há {abs(dias_ate_limite)} dias'
            )
            self.resultado['descricao'] = (
                f'Servidor puxou tarefa em {self.tarefa.data_distribuicao_tarefa.strftime("%d/%m/%Y")} '
                f'com exigência já cumprida em {self.tarefa.data_fim_ultima_exigencia.strftime("%d/%m/%Y")} (antes da atribuição). '
                f'O prazo de {prazo_dias} dias para análise venceu em {data_limite.strftime("%d/%m/%Y")}.'
            )
        else:
            self.resultado['nivel'] = self.REGULAR
            self.resultado['alerta'] = (
                f'✅ REGULAR: Faltam {dias_ate_limite} dias para análise da exigência anterior'
            )
            self.resultado['descricao'] = (
                f'Tarefa puxada em {self.tarefa.data_distribuicao_tarefa.strftime("%d/%m/%Y")} com exigência já cumprida anteriormente. '
                f'O servidor tem até {data_limite.strftime("%d/%m/%Y")} para analisar ({dias_ate_limite} dias restantes).'
            )

        return True
    
    @classmethod
    def analisar_tarefa(cls, tarefa):
        """
        Método de classe para análise rápida de uma tarefa.
        
        Args:
            tarefa: Instância do model Tarefa
            
        Returns:
            dict: Resultado da análise
        """
        analisador = cls(tarefa)
        return analisador.analisar()
    
    @classmethod
    def recalcular_todas_tarefas(cls):
        """
        Recalcula a criticidade de todas as tarefas ativas.
        Útil após mudança de parâmetros ou importação.
        """
        from .models import Tarefa
        
        tarefas = Tarefa.objects.all()
        total = tarefas.count()
        atualizadas = 0
        
        for tarefa in tarefas:
            # Atualiza flags de justificativa e serviço
            if hasattr(tarefa, 'atualizar_flags_justificativa'):
                tarefa.atualizar_flags_justificativa()
            else:
                # Atualizar flags manualmente se o método não existe
                tarefa.tem_justificativa_ativa = tarefa.justificativas.filter(
                    status='APROVADA'
                ).exists() if hasattr(tarefa, 'justificativas') else False
                
                tarefa.tem_solicitacao_ajuda = tarefa.solicitacoes_ajuda.filter(
                    status__in=['PENDENTE', 'EM_ATENDIMENTO']
                ).exists() if hasattr(tarefa, 'solicitacoes_ajuda') else False
                
                tarefa.servico_excluido_criticidade = False
            
            # Analisa criticidade
            resultado = cls.analisar_tarefa(tarefa)
            
            # Atualiza campos
            tarefa.nivel_criticidade_calculado = resultado['nivel']
            tarefa.regra_aplicada_calculado = resultado['regra']
            tarefa.alerta_criticidade_calculado = resultado['alerta']
            tarefa.descricao_criticidade_calculado = resultado['descricao']
            tarefa.cor_criticidade_calculado = resultado['cor']
            tarefa.data_calculo_criticidade = timezone.now()
            
            # Calcular pontuação para ordenação
            pontuacao = 0
            if resultado['nivel'] == 'CRÍTICA':
                pontuacao = 1000 + resultado.get('dias_pendente', 0)
            
            tarefa.pontuacao_criticidade = pontuacao
            
            tarefa.save(update_fields=[
                'tem_justificativa_ativa',
                'tem_solicitacao_ajuda',
                'servico_excluido_criticidade',
                'nivel_criticidade_calculado',
                'regra_aplicada_calculado',
                'alerta_criticidade_calculado',
                'descricao_criticidade_calculado',
                'cor_criticidade_calculado',
                'pontuacao_criticidade',
                'data_calculo_criticidade',
            ])
            
            atualizadas += 1
        
        return {
            'total': total,
            'atualizadas': atualizadas,
            'sucesso': True
        }


def aplicar_analise_criticidade(tarefa):
    """
    Função auxiliar para aplicar análise de criticidade em uma tarefa.
    Atualiza os campos calculados diretamente no objeto.
    
    Args:
        tarefa: Instância do model Tarefa
        
    Returns:
        Tarefa: Tarefa com campos atualizados (não salva automaticamente)
    """
    # Atualiza flags primeiro
    if hasattr(tarefa, 'atualizar_flags_justificativa'):
        tarefa.atualizar_flags_justificativa()
    
    # Analisa criticidade
    resultado = AnalisadorCriticidade.analisar_tarefa(tarefa)
    
    # Atualiza campos da tarefa
    tarefa.nivel_criticidade_calculado = resultado['nivel']
    tarefa.regra_aplicada_calculado = resultado['regra']
    tarefa.alerta_criticidade_calculado = resultado['alerta']
    tarefa.descricao_criticidade_calculado = resultado['descricao']
    tarefa.cor_criticidade_calculado = resultado['cor']
    tarefa.data_calculo_criticidade = timezone.now()
    
    return tarefa


# Instância global do analisador (Singleton)
_analisador_instance = None


def obter_analisador():
    """
    Retorna instância do AnalisadorCriticidade (padrão Singleton).

    Esta função é usada pelo models.py para obter o analisador
    sem precisar instanciar toda vez.

    Returns:
        class: Classe AnalisadorCriticidade
    """
    global _analisador_instance
    if _analisador_instance is None:
        _analisador_instance = AnalisadorCriticidade
    return _analisador_instance


def obter_nome_regra_amigavel(codigo_regra):
    """
    Retorna o nome amigável de uma regra de criticidade.

    Args:
        codigo_regra: Código da regra (ex: REGRA_1_EXIGENCIA_CUMPRIDA)

    Returns:
        str: Nome amigável da regra
    """
    mapeamento = {
        'REGRA_1_EXIGENCIA_CUMPRIDA': 'Exigência Cumprida - Aguardando Análise',
        'REGRA_2_CUMPRIMENTO_EXIGENCIA': 'Cumprimento de Exigência pelo Segurado',
        'REGRA_3_PRIMEIRA_ACAO_SEM_EXIGENCIA': 'Tarefa Nunca Trabalhada',
        'REGRA_4_PRIMEIRA_ACAO_COM_EXIGENCIA': 'Exigência Cumprida Anterior',
        'SERVICO_EXCLUIDO': 'Serviço Excluído da Análise',
        'JUSTIFICATIVA_APROVADA': 'Justificativa Aprovada',
        'TEM_SUBTAREFAS': 'Possui Subtarefas Pendentes',
        'SEM_REGRA': 'Sem Regra Aplicada',
    }
    return mapeamento.get(codigo_regra, codigo_regra)