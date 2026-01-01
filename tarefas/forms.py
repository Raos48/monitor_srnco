"""
FORMULÁRIOS PARA JUSTIFICATIVAS E SOLICITAÇÕES
Arquivo: tarefas/forms.py (criar novo arquivo ou adicionar ao existente)
"""

from django import forms
from .models import Justificativa, SolicitacaoAjuda, TipoJustificativa


class JustificativaForm(forms.ModelForm):
    """
    Formulário para o servidor submeter justificativa de tarefa crítica.
    """
    
    class Meta:
        model = Justificativa
        fields = ['tipo_justificativa', 'descricao']
        widgets = {
            'tipo_justificativa': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Descreva detalhadamente o motivo da situação crítica...',
                'required': True
            }),
        }
        labels = {
            'tipo_justificativa': 'Tipo de Justificativa',
            'descricao': 'Descrição Detalhada'
        }
        help_texts = {
            'tipo_justificativa': 'Selecione o tipo que melhor descreve a situação',
            'descricao': 'Explique claramente o motivo e o contexto da situação'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtra apenas tipos ativos
        self.fields['tipo_justificativa'].queryset = TipoJustificativa.objects.filter(ativo=True)
        
    def clean_descricao(self):
        """Valida que a descrição tenha conteúdo suficiente"""
        descricao = self.cleaned_data.get('descricao', '')
        
        if len(descricao.strip()) < 20:
            raise forms.ValidationError(
                'A descrição deve ter pelo menos 20 caracteres. Seja mais detalhado.'
            )
        
        return descricao.strip()


class AvaliacaoJustificativaForm(forms.Form):
    """
    Formulário para a Equipe Volante avaliar justificativas.
    """
    
    DECISAO_CHOICES = [
        ('APROVAR', '✅ Aprovar Justificativa'),
        ('REPROVAR', '❌ Reprovar Justificativa'),
    ]
    
    decisao = forms.ChoiceField(
        choices=DECISAO_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        }),
        label='Decisão',
        required=True
    )
    
    observacao = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Adicione observações sobre sua decisão...'
        }),
        label='Observações',
        required=False,
        help_text='Opcional: Adicione comentários sobre a aprovação ou reprovação'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        decisao = cleaned_data.get('decisao')
        observacao = cleaned_data.get('observacao', '').strip()
        
        # Se reprovar, observação é obrigatória
        if decisao == 'REPROVAR' and not observacao:
            raise forms.ValidationError({
                'observacao': 'Ao reprovar uma justificativa, você deve informar o motivo.'
            })
        
        return cleaned_data


class SolicitacaoAjudaForm(forms.ModelForm):
    """
    Formulário para o servidor solicitar ajuda da Equipe Volante.
    """
    
    class Meta:
        model = SolicitacaoAjuda
        fields = ['descricao']
        widgets = {
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Descreva o problema e o tipo de ajuda necessária...',
                'required': True
            }),
        }
        labels = {
            'descricao': 'Descrição do Problema'
        }
        help_texts = {
            'descricao': 'Explique claramente a situação e que tipo de suporte você precisa'
        }
    
    def clean_descricao(self):
        """Valida que a descrição tenha conteúdo suficiente"""
        descricao = self.cleaned_data.get('descricao', '')
        
        if len(descricao.strip()) < 20:
            raise forms.ValidationError(
                'A descrição deve ter pelo menos 20 caracteres. Seja mais específico sobre o problema.'
            )
        
        return descricao.strip()


class AtendimentoSolicitacaoForm(forms.Form):
    """
    Formulário para a Equipe Volante atender solicitações de ajuda.
    """
    
    ACAO_CHOICES = [
        ('INICIAR', '🔵 Iniciar Atendimento'),
        ('CONCLUIR', '✅ Concluir Atendimento'),
        ('CANCELAR', '❌ Cancelar Solicitação'),
    ]
    
    acao = forms.ChoiceField(
        choices=ACAO_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        }),
        label='Ação',
        required=True
    )
    
    observacao = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Descreva as ações realizadas ou o motivo do cancelamento...'
        }),
        label='Observações',
        required=False
    )
    
    def clean(self):
        cleaned_data = super().clean()
        acao = cleaned_data.get('acao')
        observacao = cleaned_data.get('observacao', '').strip()
        
        # Se concluir ou cancelar, observação é obrigatória
        if acao in ['CONCLUIR', 'CANCELAR'] and not observacao:
            if acao == 'CONCLUIR':
                mensagem = 'Ao concluir um atendimento, descreva as ações realizadas.'
            else:
                mensagem = 'Ao cancelar uma solicitação, informe o motivo.'
            
            raise forms.ValidationError({
                'observacao': mensagem
            })
        
        return cleaned_data


class FiltroJustificativasForm(forms.Form):
    """
    Formulário para filtrar justificativas no painel da Equipe Volante.
    """
    
    STATUS_CHOICES = [
        ('', 'Todos os Status'),
        ('PENDENTE', 'Pendente de Análise'),
        ('APROVADA', 'Aprovadas'),
        ('REPROVADA', 'Reprovadas'),
    ]
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    
    tipo = forms.ModelChoiceField(
        queryset=TipoJustificativa.objects.filter(ativo=True),
        required=False,
        empty_label='Todos os Tipos',
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    
    servidor = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'SIAPE ou nome do servidor'
        })
    )
    
    protocolo = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'Número do protocolo'
        })
    )
    
    data_inicial = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control form-control-sm',
            'type': 'date'
        })
    )
    
    data_final = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control form-control-sm',
            'type': 'date'
        })
    )


class FiltroSolicitacoesForm(forms.Form):
    """
    Formulário para filtrar solicitações de ajuda.
    """
    
    STATUS_CHOICES = [
        ('', 'Todos os Status'),
        ('PENDENTE', 'Pendentes'),
        ('EM_ATENDIMENTO', 'Em Atendimento'),
        ('CONCLUIDA', 'Concluídas'),
    ]
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    
    servidor = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'SIAPE ou nome do servidor'
        })
    )
    
    protocolo = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'Número do protocolo'
        })
    )
