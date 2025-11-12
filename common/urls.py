from django.urls import path
from . import views 

urlpatterns = [
    # APIs
    path('api/get_produto_data/<int:produto_id>/', views.get_produto_data, name='get_produto_data'),
    path('api/check_cliente/', views.check_cliente, name='check_cliente'),
]