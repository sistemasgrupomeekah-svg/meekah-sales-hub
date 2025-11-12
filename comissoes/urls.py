from django.urls import path
from . import views 

urlpatterns = [
    # Dashboards de Comissão
    path('comissoes/', views.comissoes_dashboard_graficos, name='comissoes_dashboard'),
    path('comissoes/historico/', views.comissoes_historico_lotes, name='comissoes_historico'),
    
    # Fluxo de Pagamento de Lotes
    path('comissoes/fechamento/', views.comissoes_fechamento, name='comissoes_fechamento'),
    path('comissoes/lote/<int:lote_id>/', views.comissoes_lote_detalhe, name='comissoes_lote_detalhe'),

    # Exports de Lotes
    path('comissoes/export/csv/', views.export_lotes_csv, name='export_lotes_csv'),
    path('comissoes/export/xlsx/', views.export_lotes_xlsx, name='export_lotes_xlsx'),
    
    # Gestão de Metas (CRUD)
    path('metas/', views.lista_metas, name='lista_metas'),
    path('metas/nova/', views.criar_meta, name='criar_meta'),
    path('metas/<int:meta_id>/editar/', views.editar_meta, name='editar_meta'),
    path('metas/<int:meta_id>/apagar/', views.apagar_meta, name='apagar_meta'),
]