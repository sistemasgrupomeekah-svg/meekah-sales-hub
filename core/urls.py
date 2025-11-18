# Em: core/urls.py (Atualizado)

from django.contrib import admin
from django.urls import path, include # <-- Adicione 'include'
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # --- ROTAS ATUALIZADAS ---
    
    # APIs (de 'common')
    path('', include('common.urls')), 
    
    # Rotas de Comissões e Metas (de 'comissoes')
    path('', include('comissoes.urls')),
    
    # Rotas de Vendas (de 'vendas')
    path('', include('vendas.urls')), 
    
    # --- FIM ROTAS ATUALIZADAS ---
]

# 🧪 ROTA DE TESTE - REMOVER EM PRODUÇÃO
from vendas.views import test_s3
urlpatterns.append(path('test-s3/', test_s3))

# (A sua configuração de Mídia para DEBUG permanece a mesma)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)