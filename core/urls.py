from django.urls import path, include # <-- CERTIFIQUE-SE DE ADICIONAR 'include'
from django.contrib.auth import views as auth_views
from django.contrib import admin # <-- ADICIONEI O ADMIN QUE APARECEU NO SEU ERRO 404
from . import views

urlpatterns = [
    # Admin (estava no seu erro 404)
    path('admin/', admin.site.urls), 

    # ================================================================
    # ADICIONAMOS ESTA LINHA PARA INCLUIR AS URLS DO APP 'tarefas'
    path('tarefas/', include('tarefas.urls', namespace='tarefas')),
    # ================================================================

    # Página inicial / Dashboard
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('servidor/<str:siape>/', views.ServidorDetailView.as_view(), name='servidor_detail'),
    path('login/', auth_views.LoginView.as_view(template_name='auth/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('teste-visual/', views.teste_visual, name='teste_visual'),
    
    # path('importar/', ...), # Esta rota também apareceu no seu erro 404
]