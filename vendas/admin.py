from django.contrib import admin
from .models import (
    Produto, Cliente, Venda, AnexoVenda, FormaPagamento, 
    RegraComissaoVendedor, LotePagamentoComissao, TransacaoPagamentoComissao, AnexoLoteComissao
)
from django.utils.html import format_html 

# (FormaPagamento, Produto, Cliente, AnexoVendaInline, Venda, AnexoVendaAdmin, RegraComissaoVendedorAdmin - Sem alterações)
@admin.register(FormaPagamento)
class FormaPagamentoAdmin(admin.ModelAdmin): list_display = ('nome',); search_fields = ('nome',)
@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin): list_display = ('nome', 'valor', 'tipo_comissao', 'valor_comissao', 'valor_entrada_sugerido', 'valor_exito_sugerido', 'valor_aporte_sugerido'); search_fields = ('nome',); list_filter = ('tipo_comissao',)
@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin): list_display = ('nome_completo', 'email', 'cpf_cnpj', 'telefone'); search_fields = ('nome_completo', 'email', 'cpf_cnpj')
class AnexoVendaInline(admin.TabularInline): model = AnexoVenda; extra = 1; fields = ('tipo', 'arquivo', 'descricao') 
@admin.register(Venda)
class VendaAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'produto', 'vendedor', 'honorarios', 'status_pagamento', 'comissao_calculada_final', 'lote_pagamento', 'data_venda')
    search_fields = ('id', 'cliente__nome_completo', 'produto__nome', 'vendedor__username')
    list_filter = ('status_venda', 'status_pagamento', 'status_contrato', 'vendedor', 'produto', 'lote_pagamento')
    inlines = [AnexoVendaInline]
    readonly_fields = ('comissao_calculada_final', 'lote_pagamento')
@admin.register(AnexoVenda)
class AnexoVendaAdmin(admin.ModelAdmin):
    list_display = ('venda', 'tipo', 'link_para_o_arquivo', 'data_upload'); search_fields = ('venda__id',); list_filter = ('tipo',) 
    def link_para_o_arquivo(self, obj):
        if obj.arquivo: return format_html('<a href="{}" target="_blank">Abrir Anexo</a>', obj.arquivo.url)
        return "Nenhum arquivo"
    link_para_o_arquivo.short_description = "Link do Arquivo"
@admin.register(RegraComissaoVendedor)
class RegraComissaoVendedorAdmin(admin.ModelAdmin):
    list_display = ('vendedor', 'produto', 'tipo_comissao', 'valor_comissao'); search_fields = ('vendedor__username', 'produto__nome'); list_filter = ('vendedor', 'produto', 'tipo_comissao')

# --- LOTE ADMIN (ATUALIZADO Req 3) ---
class TransacaoPagamentoComissaoInline(admin.TabularInline):
    model = TransacaoPagamentoComissao
    extra = 0 
    # ATUALIZADO: Corrigido o nome do campo
    fields = ('responsavel_pagamento', 'data_pagamento', 'valor_pago', 'anexo_comprovativo_pagamento')
    readonly_fields = ('responsavel_pagamento', 'data_pagamento', 'valor_pago', 'anexo_comprovativo_pagamento')
    can_delete = False
    def has_add_permission(self, request, obj=None): return False

# NOVO INLINE (Sua Solicitação)
class AnexoLoteComissaoInline(admin.TabularInline):
    model = AnexoLoteComissao
    extra = 0 # Não permite adicionar pelo Admin (só pela view)
    fields = ('anexo_nf_vendedor', 'descricao', 'data_upload')
    readonly_fields = ('anexo_nf_vendedor', 'descricao', 'data_upload')
    can_delete = False
    def has_add_permission(self, request, obj=None): return False

@admin.register(LotePagamentoComissao)
class LotePagamentoComissaoAdmin(admin.ModelAdmin):
    list_display = ('id', 'vendedor', 'periodo_inicio', 'periodo_fim', 'responsavel_fechamento', 'status', 'total_comissoes', 'total_pago_efetivamente', 'data_fechamento')
    list_filter = ('status', 'responsavel_fechamento', 'vendedor') 
    search_fields = ('id', 'responsavel_fechamento__username', 'vendedor__username')
    readonly_fields = ('total_comissoes', 'total_pago_efetivamente', 'responsavel_fechamento', 'data_fechamento', 'vendedor', 'periodo_inicio', 'periodo_fim')
    
    # ATUALIZADO: Mostra os dois inlines
    inlines = [TransacaoPagamentoComissaoInline, AnexoLoteComissaoInline]
    
    def has_add_permission(self, request): return False
    def has_delete_permission(self, request, obj=None): return False