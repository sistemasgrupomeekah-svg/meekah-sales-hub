from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Rota da app vendas (inclui dashboard e nova_venda)
    path('', include('vendas.urls')), 
]

# --- Configuração para Mídia (CORREÇÃO) ---
# Em modo DEBUG (desenvolvimento), dizemos ao Django para servir
# os arquivos que estão em MEDIA_ROOT (nossa pasta /media/)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# --- Fim Configuração ---

