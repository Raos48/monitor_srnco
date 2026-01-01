from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Página inicial / Dashboard (redireciona para o dashboard apropriado)
    path('', views.DashboardView.as_view(), name='dashboard'),

    # Autenticação
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Visualização de servidor (legado - manter por compatibilidade)
    path('servidor/<str:siape>/', views.ServidorDetailView.as_view(), name='servidor_detail'),

    # Teste visual
    path('teste-visual/', views.teste_visual, name='teste_visual'),
]