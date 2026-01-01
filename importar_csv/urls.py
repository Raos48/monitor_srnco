"""
URLs para Importar CSV
Arquivo: importar_csv/urls.py
"""

from django.urls import path
from .views import ImportarCSVView, StatusImportacaoAPIView

app_name = 'importar_csv'

urlpatterns = [
    # View principal de importação
    path('', ImportarCSVView.as_view(), name='importar_csv'),

    # API para verificar status de uma importação em tempo real
    path('status/<int:registro_id>/', StatusImportacaoAPIView.as_view(), name='status_importacao'),
]