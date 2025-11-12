from django.urls import path
from . import views 
from django.contrib.auth import views as auth_views

urlpatterns = [
    # --- Autenticação ---
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # --- Abas Principais (Vendas) ---
    path('', views.dashboard_graficos, name='dashboard'),
    path('vendas/', views.lista_vendas, name='lista_vendas'),
    path('venda/nova/', views.nova_venda, name='nova_venda'),
    path('venda/<int:venda_id>/', views.detalhe_venda, name='detalhe_venda'),
    
    # --- Rotas de Exportação (Vendas) ---
    path('vendas/export/csv/', views.export_vendas_csv, name='export_vendas_csv'),
    path('vendas/export/xlsx/', views.export_vendas_xlsx, name='export_vendas_xlsx'),
    
    # --- API (Apenas de Vendas) ---
    path('anexo/<int:anexo_id>/delete/', views.delete_anexo, name='delete_anexo'),
]