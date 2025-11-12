from django.contrib import admin
from .models import Produto, Cliente, FormaPagamento

@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'valor', 'tipo_comissao', 'valor_comissao')
    search_fields = ('nome',)
    list_filter = ('tipo_comissao',)

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nome_completo', 'email', 'cpf_cnpj', 'telefone')
    search_fields = ('nome_completo', 'email', 'cpf_cnpj')

@admin.register(FormaPagamento)
class FormaPagamentoAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)