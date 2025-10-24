from django import forms

class CSVImportForm(forms.Form):
    arquivo_csv = forms.FileField(
        label="Selecione o arquivo CSV",
        help_text="O arquivo deve ser separado por ponto e vírgula (;)",
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.csv'})
    )
