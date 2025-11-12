# Em: vendas/admin.py (Atualizado)

from django.contrib import admin
from .models import Venda, AnexoVenda
from django.utils.html import format_html 

# Registos de Produto, Cliente, FormaPagamento, Regra, Lote, Meta FORAM MOVIDOS

class AnexoVendaInline(admin.TabularInline): 
    model = AnexoVenda
    extra = 1
    fields = ('tipo', 'arquivo', 'descricao') 

@admin.register(Venda)
class VendaAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'produto', 'vendedor', 'honorarios', 'status_pagamento', 'comissao_calculada_final', 'lote_pagamento', 'data_venda')
    search_fields = ('id', 'cliente__nome_completo', 'produto__nome', 'vendedor__username')
    list_filter = ('status_venda', 'status_pagamento', 'status_contrato', 'vendedor', 'produto', 'lote_pagamento')
    inlines = [AnexoVendaInline]
    readonly_fields = ('comissao_calculada_final', 'lote_pagamento')
    
    # Adiciona links para os modelos que agora estão noutra app (common)
    raw_id_fields = ('cliente', 'produto', 'vendedor')

@admin.register(AnexoVenda)
class AnexoVendaAdmin(admin.ModelAdmin):
    list_display = ('venda', 'tipo', 'link_para_o_arquivo', 'data_upload')
    search_fields = ('venda__id',)
    list_filter = ('tipo',) 
    
    def link_para_o_arquivo(self, obj):
        if obj.arquivo: 
            return format_html('<a href="{}" target="_blank">Abrir Anexo</a>', obj.arquivo.url)
        return "Nenhum arquivo"
    link_para_o_arquivo.short_description = "Link do Arquivo"