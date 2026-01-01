from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.http import JsonResponse

# View de teste simples
def test_view(request):
    return JsonResponse({
        'status': 'ok',
        'message': 'Django está funcionando!',
        'path': request.path,
        'method': request.method
    })

urlpatterns = [
    # View de teste (temporário para debug)
    path('test/', test_view, name='test'),

    path('admin/', admin.site.urls),

    # URLs do app core (login, logout, dashboard)
    path('', include('core.urls')),

    # URLs do app tarefas (com namespace)
    path('tarefas/', include('tarefas.urls')),

    # URLs do app importar_csv
    path('importar/', include('importar_csv.urls')),

    # API REST para integração com robô externo
    path('api/', include('tarefas.api.urls')),
]

# Adicionar Django Debug Toolbar apenas em modo DEBUG
if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns