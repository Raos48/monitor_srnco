"""
Serviço de envio de emails usando Microsoft Graph API.

Integração com Azure AD para envio de emails automatizados
usando credenciais de aplicação.
"""
import os
import requests
import msal
from django.conf import settings
from django.template import Template, Context
from django.utils import timezone
from tarefas.models import HistoricoEmail, TemplateEmail


class EmailService:
    """
    Serviço para envio de emails via Microsoft Graph API.
    """

    def __init__(self):
        """Inicializa o serviço com as credenciais do Azure AD."""
        self.client_id = getattr(settings, 'AZURE_AD_CLIENT_ID', os.getenv('AZURE_AD_CLIENT_ID'))
        self.client_secret = getattr(settings, 'AZURE_AD_CLIENT_SECRET', os.getenv('AZURE_AD_CLIENT_SECRET'))
        self.tenant_id = getattr(settings, 'AZURE_AD_TENANT_ID', os.getenv('AZURE_AD_TENANT_ID'))
        self.sender_email = getattr(settings, 'SENDER_EMAIL', os.getenv('SENDER_EMAIL'))

        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.scope = ["https://graph.microsoft.com/.default"]

    def get_access_token(self):
        """
        Obtém o token de acesso para o aplicativo.

        Returns:
            str: Token de acesso

        Raises:
            Exception: Se falhar ao obter o token
        """
        app = msal.ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=self.authority
        )

        result = app.acquire_token_for_client(scopes=self.scope)

        if "access_token" in result:
            return result["access_token"]
        else:
            error_description = result.get("error_description", "Sem detalhes.")
            raise Exception(f"Falha ao obter token de acesso: {error_description}")

    def enviar_email(self, destinatario_email, assunto, corpo_html, servidor, enviado_por):
        """
        Envia um email usando o Microsoft Graph API.

        Args:
            destinatario_email (str): Email do destinatário
            assunto (str): Assunto do email
            corpo_html (str): Corpo do email em HTML
            servidor (CustomUser): Objeto do servidor destinatário
            enviado_por (CustomUser): Usuário que está enviando o email

        Returns:
            tuple: (sucesso: bool, historico: HistoricoEmail)
        """
        # Criar registro de histórico
        historico = HistoricoEmail.objects.create(
            servidor=servidor,
            email_destinatario=destinatario_email,
            assunto=assunto,
            corpo_email=corpo_html,
            enviado_por=enviado_por,
            status=HistoricoEmail.STATUS_PENDENTE
        )

        try:
            # Obter token de acesso
            access_token = self.get_access_token()

            # Preparar requisição
            url = f"https://graph.microsoft.com/v1.0/users/{self.sender_email}/sendMail"

            email_msg = {
                "message": {
                    "subject": assunto,
                    "body": {"contentType": "HTML", "content": corpo_html},
                    "toRecipients": [{"emailAddress": {"address": destinatario_email}}]
                },
                "saveToSentItems": "true"
            }

            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }

            # Enviar email
            response = requests.post(url, headers=headers, json=email_msg)

            if response.status_code == 202:
                # Sucesso
                historico.marcar_como_enviado(resposta_api=f"Status: {response.status_code}")
                return True, historico
            else:
                # Erro
                erro_msg = f"Status: {response.status_code} - {response.text}"
                historico.marcar_como_erro(mensagem_erro=erro_msg)
                return False, historico

        except Exception as e:
            # Erro na execução
            historico.marcar_como_erro(mensagem_erro=str(e))
            return False, historico

    def enviar_email_por_template(self, template_nome, servidor, enviado_por, contexto_extra=None):
        """
        Envia email usando um template configurado no Django Admin.

        Args:
            template_nome (str): Nome do template a ser usado
            servidor (CustomUser): Servidor destinatário
            enviado_por (CustomUser): Usuário que está enviando
            contexto_extra (dict): Dados adicionais para o template

        Returns:
            tuple: (sucesso: bool, historico: HistoricoEmail)
        """
        try:
            # Buscar template
            template_email = TemplateEmail.objects.get(nome=template_nome, ativo=True)
        except TemplateEmail.DoesNotExist:
            raise ValueError(f"Template '{template_nome}' não encontrado ou inativo.")

        # Preparar contexto base
        contexto = {
            'nome_servidor': servidor.get_full_name() or servidor.username,
            'siape': servidor.siape,
            'email': servidor.email,
            'data_hoje': timezone.now().strftime('%d/%m/%Y'),
        }

        # Adicionar contexto extra
        if contexto_extra:
            contexto.update(contexto_extra)

        # Renderizar template
        template_assunto = Template(template_email.assunto)
        template_corpo = Template(template_email.corpo_html)

        assunto_renderizado = template_assunto.render(Context(contexto))
        corpo_renderizado = template_corpo.render(Context(contexto))

        # Enviar email
        return self.enviar_email(
            destinatario_email=servidor.email,
            assunto=assunto_renderizado,
            corpo_html=corpo_renderizado,
            servidor=servidor,
            enviado_por=enviado_por
        )

    def criar_lista_tarefas_html(self, tarefas):
        """
        Cria uma lista HTML formatada com as tarefas.

        Args:
            tarefas (QuerySet): QuerySet de tarefas

        Returns:
            str: HTML formatado com a lista de tarefas
        """
        html = '<table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">'
        html += '<thead><tr style="background-color: #007bff; color: white;">'
        html += '<th>Protocolo</th><th>Serviço</th><th>Prazo</th><th>Dias Pendente</th><th>Criticidade</th>'
        html += '</tr></thead><tbody>'

        for tarefa in tarefas:
            cor_linha = '#ffcccc' if tarefa.nivel_criticidade_calculado == 'CRÍTICA' else '#ffffff'

            html += f'<tr style="background-color: {cor_linha};">'
            html += f'<td>{tarefa.numero_protocolo_tarefa}</td>'
            html += f'<td>{tarefa.nome_servico}</td>'
            html += f'<td>{tarefa.data_prazo.strftime("%d/%m/%Y") if tarefa.data_prazo else "-"}</td>'
            html += f'<td style="text-align: center;">{tarefa.dias_pendente_criticidade_calculado}</td>'
            html += f'<td style="text-align: center;">{tarefa.nivel_criticidade_calculado}</td>'
            html += '</tr>'

        html += '</tbody></table>'
        return html
