from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

# A linha "from . import views" foi removida daqui.




urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lambda request: redirect('tarefas:redirect_after_login')),  # ✅ Agora funciona
    path('tarefas/', include('tarefas.urls')),
    path('importar/', include('importar_csv.urls')),  # ✅ ADICIONE ESTA LINHA

]