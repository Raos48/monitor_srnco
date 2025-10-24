"""
URLs para Importar CSV
Arquivo: importar_csv/urls.py
"""

from django.urls import path
from .views import ImportarCSVView  # ✅ Importa a CLASSE, não função

app_name = 'importar_csv'

urlpatterns = [
    # View baseada em classe precisa do .as_view()
    path('', ImportarCSVView.as_view(), name='importar_csv'),
]