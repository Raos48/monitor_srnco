"""
Serviço para gerenciar ações de bloqueio e notificações.

Centraliza a lógica de negócio para criação e gerenciamento
de solicitações de ações automatizadas.
"""
from django.utils import timezone
from tarefas.models import (
    BloqueioServidor,
    SolicitacaoNotificacao,
    HistoricoBloqueio,
    HistoricoNotificacao
)


class AcoesService:
    """
    Serviço para gerenciar ações de bloqueio, desbloqueio e notificações.
    """

    @staticmethod
    def solicitar_bloqueio(servidor, codigo_fila, solicitado_por, observacoes=''):
        """
        Cria uma solicitação de bloqueio de caixa para um servidor.

        Args:
            servidor (CustomUser): Servidor a ser bloqueado
            codigo_fila (str): Código da fila (ex: '23150521')
            solicitado_por (CustomUser): Usuário que está solicitando
            observacoes (str): Observações adicionais

        Returns:
            BloqueioServidor: Objeto da solicitação criada
        """
        # Criar solicitação
        bloqueio = BloqueioServidor.objects.create(
            servidor=servidor,
            codigo_fila=codigo_fila,
            tipo_acao=BloqueioServidor.TIPO_BLOQUEIO,
            solicitado_por=solicitado_por,
            observacoes=observacoes
        )

        # Criar registro no histórico
        HistoricoBloqueio.objects.create(
            bloqueio=bloqueio,
            servidor=servidor,
            codigo_fila=codigo_fila,
            tipo_acao=BloqueioServidor.TIPO_BLOQUEIO,
            status=BloqueioServidor.STATUS_PENDENTE,
            executado_por=solicitado_por,
            detalhes=f"Solicitação de bloqueio criada. {observacoes}"
        )

        return bloqueio

    @staticmethod
    def solicitar_desbloqueio(servidor, codigo_fila, solicitado_por, observacoes=''):
        """
        Cria uma solicitação de desbloqueio de caixa para um servidor.

        Args:
            servidor (CustomUser): Servidor a ser desbloqueado
            codigo_fila (str): Código da fila (ex: '23150521')
            solicitado_por (CustomUser): Usuário que está solicitando
            observacoes (str): Observações adicionais

        Returns:
            BloqueioServidor: Objeto da solicitação criada
        """
        # Criar solicitação
        desbloqueio = BloqueioServidor.objects.create(
            servidor=servidor,
            codigo_fila=codigo_fila,
            tipo_acao=BloqueioServidor.TIPO_DESBLOQUEIO,
            solicitado_por=solicitado_por,
            observacoes=observacoes
        )

        # Criar registro no histórico
        HistoricoBloqueio.objects.create(
            bloqueio=desbloqueio,
            servidor=servidor,
            codigo_fila=codigo_fila,
            tipo_acao=BloqueioServidor.TIPO_DESBLOQUEIO,
            status=BloqueioServidor.STATUS_PENDENTE,
            executado_por=solicitado_por,
            detalhes=f"Solicitação de desbloqueio criada. {observacoes}"
        )

        return desbloqueio

    @staticmethod
    def solicitar_notificacao_pgb(servidor, tipo_notificacao, solicitado_por, observacoes=''):
        """
        Cria uma solicitação de notificação PGB.

        Args:
            servidor (CustomUser): Servidor que receberá a notificação
            tipo_notificacao (str): PRIMEIRA_NOTIFICACAO ou SEGUNDA_NOTIFICACAO
            solicitado_por (CustomUser): Usuário que está solicitando
            observacoes (str): Observações adicionais

        Returns:
            SolicitacaoNotificacao: Objeto da solicitação criada
        """
        # Validar tipo de notificação
        tipos_validos = [
            SolicitacaoNotificacao.TIPO_PRIMEIRA,
            SolicitacaoNotificacao.TIPO_SEGUNDA
        ]
        if tipo_notificacao not in tipos_validos:
            raise ValueError(f"Tipo de notificação inválido: {tipo_notificacao}")

        # Criar solicitação
        notificacao = SolicitacaoNotificacao.objects.create(
            servidor=servidor,
            tipo_notificacao=tipo_notificacao,
            solicitado_por=solicitado_por,
            observacoes=observacoes
        )

        # Criar registro no histórico
        HistoricoNotificacao.objects.create(
            notificacao=notificacao,
            servidor=servidor,
            tipo_notificacao=tipo_notificacao,
            status=SolicitacaoNotificacao.STATUS_PENDENTE,
            executado_por=solicitado_por,
            detalhes=f"Solicitação de notificação criada. {observacoes}"
        )

        return notificacao

    @staticmethod
    def obter_solicitacoes_bloqueio_pendentes():
        """
        Retorna todas as solicitações de bloqueio/desbloqueio pendentes.

        Returns:
            QuerySet: Solicitações pendentes
        """
        return BloqueioServidor.objects.filter(
            status=BloqueioServidor.STATUS_PENDENTE
        ).select_related('servidor', 'solicitado_por').order_by('data_solicitacao')

    @staticmethod
    def obter_solicitacoes_notificacao_pendentes():
        """
        Retorna todas as solicitações de notificação PGB pendentes.

        Returns:
            QuerySet: Solicitações pendentes
        """
        return SolicitacaoNotificacao.objects.filter(
            status=SolicitacaoNotificacao.STATUS_PENDENTE
        ).select_related('servidor', 'solicitado_por').order_by('data_solicitacao')

    @staticmethod
    def processar_resposta_bloqueio(bloqueio_id, sucesso, resposta_robo='', mensagem_erro=''):
        """
        Processa a resposta do robô para uma solicitação de bloqueio.

        Args:
            bloqueio_id (int): ID da solicitação
            sucesso (bool): Se a operação foi bem-sucedida
            resposta_robo (str): Resposta técnica do robô
            mensagem_erro (str): Mensagem de erro (se houver)

        Returns:
            BloqueioServidor: Solicitação atualizada
        """
        bloqueio = BloqueioServidor.objects.get(pk=bloqueio_id)

        if sucesso:
            bloqueio.marcar_como_concluido(resposta_robo=resposta_robo)

            # Registrar no histórico
            HistoricoBloqueio.objects.create(
                bloqueio=bloqueio,
                servidor=bloqueio.servidor,
                codigo_fila=bloqueio.codigo_fila,
                tipo_acao=bloqueio.tipo_acao,
                status=BloqueioServidor.STATUS_CONCLUIDO,
                executado_por=None,  # Robô
                detalhes="Ação concluída com sucesso pelo robô.",
                resposta_robo=resposta_robo
            )
        else:
            bloqueio.marcar_como_erro(mensagem_erro=mensagem_erro)

            # Registrar no histórico
            HistoricoBloqueio.objects.create(
                bloqueio=bloqueio,
                servidor=bloqueio.servidor,
                codigo_fila=bloqueio.codigo_fila,
                tipo_acao=bloqueio.tipo_acao,
                status=BloqueioServidor.STATUS_ERRO,
                executado_por=None,  # Robô
                detalhes=f"Erro ao processar ação: {mensagem_erro}",
                resposta_robo=resposta_robo
            )

        return bloqueio

    @staticmethod
    def processar_resposta_notificacao(notificacao_id, sucesso, numero_protocolo='', resposta_robo='', mensagem_erro=''):
        """
        Processa a resposta do robô para uma solicitação de notificação.

        Args:
            notificacao_id (int): ID da solicitação
            sucesso (bool): Se a operação foi bem-sucedida
            numero_protocolo (str): Protocolo da tarefa criada
            resposta_robo (str): Resposta técnica do robô
            mensagem_erro (str): Mensagem de erro (se houver)

        Returns:
            SolicitacaoNotificacao: Solicitação atualizada
        """
        notificacao = SolicitacaoNotificacao.objects.get(pk=notificacao_id)

        if sucesso:
            notificacao.marcar_como_concluido(
                numero_protocolo=numero_protocolo,
                resposta_robo=resposta_robo
            )

            # Registrar no histórico
            HistoricoNotificacao.objects.create(
                notificacao=notificacao,
                servidor=notificacao.servidor,
                tipo_notificacao=notificacao.tipo_notificacao,
                status=SolicitacaoNotificacao.STATUS_CONCLUIDO,
                executado_por=None,  # Robô
                detalhes="Notificação criada com sucesso pelo robô.",
                numero_protocolo=numero_protocolo,
                resposta_robo=resposta_robo
            )
        else:
            notificacao.marcar_como_erro(mensagem_erro=mensagem_erro)

            # Registrar no histórico
            HistoricoNotificacao.objects.create(
                notificacao=notificacao,
                servidor=notificacao.servidor,
                tipo_notificacao=notificacao.tipo_notificacao,
                status=SolicitacaoNotificacao.STATUS_ERRO,
                executado_por=None,  # Robô
                detalhes=f"Erro ao processar notificação: {mensagem_erro}",
                resposta_robo=resposta_robo
            )

        return notificacao

    @staticmethod
    def verificar_status_servidor(siape, codigo_fila):
        """
        Verifica o status de bloqueio de um servidor para uma fila.

        Args:
            siape (str): SIAPE do servidor
            codigo_fila (str): Código da fila

        Returns:
            dict: Dicionário com informações de status
        """
        bloqueado = BloqueioServidor.servidor_esta_bloqueado(siape, codigo_fila)

        resultado = {
            'bloqueado': bloqueado,
            'tem_solicitacao_pendente': False,
            'ultima_solicitacao': None
        }

        # Verificar se há solicitação pendente
        solicitacao_pendente = BloqueioServidor.objects.filter(
            servidor__siape=siape,
            codigo_fila=codigo_fila,
            status=BloqueioServidor.STATUS_PENDENTE
        ).order_by('-data_solicitacao').first()

        if solicitacao_pendente:
            resultado['tem_solicitacao_pendente'] = True
            resultado['ultima_solicitacao'] = solicitacao_pendente

        return resultado
