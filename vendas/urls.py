from django.urls import path
from . import views 
from django.contrib.auth import views as auth_views

urlpatterns = [
    # --- Autenticação ---
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # --- Abas Principais ---
    path('', views.dashboard_graficos, name='dashboard'),
    path('vendas/', views.lista_vendas, name='lista_vendas'),
    path('venda/nova/', views.nova_venda, name='nova_venda'),
    
    # --- Rotas de Comissões (As que faltavam) ---
    path('comissoes/', views.comissoes_dashboard, name='comissoes_dashboard'),
    path('comissoes/fechamento/', views.comissoes_fechamento, name='comissoes_fechamento'),
    path('comissoes/lote/<int:lote_id>/', views.comissoes_lote_detalhe, name='comissoes_lote_detalhe'),

    # --- Rotas de Exportação ---
    path('vendas/export/csv/', views.export_vendas_csv, name='export_vendas_csv'),
    path('vendas/export/xlsx/', views.export_vendas_xlsx, name='export_vendas_xlsx'),
    
    # (Resto das rotas)
    path('venda/<int:venda_id>/', views.detalhe_venda, name='detalhe_venda'),
    path('anexo/<int:anexo_id>/delete/', views.delete_anexo, name='delete_anexo'),
    
    # --- APIs ---
    path('api/get_produto_data/<int:produto_id>/', views.get_produto_data, name='get_produto_data'),
    path('api/check_cliente/', views.check_cliente, name='check_cliente'),
]