from django.contrib import admin
from django import forms
from .models import (
    RegraComissaoVendedor, 
    LotePagamentoComissao, 
    TransacaoPagamentoComissao, 
    AnexoLoteComissao,
    MetaVenda
)

@admin.register(RegraComissaoVendedor)
class RegraComissaoVendedorAdmin(admin.ModelAdmin):
    list_display = ('vendedor', 'produto', 'tipo_comissao', 'valor_comissao')
    search_fields = ('vendedor__username', 'produto__nome')
    list_filter = ('vendedor', 'produto', 'tipo_comissao')

# --- LOTE ADMIN ---
class TransacaoPagamentoComissaoInline(admin.TabularInline):
    model = TransacaoPagamentoComissao
    extra = 0 
    fields = ('responsavel_pagamento', 'data_pagamento', 'valor_pago', 'anexo_comprovativo_pagamento')
    readonly_fields = ('responsavel_pagamento', 'data_pagamento', 'valor_pago', 'anexo_comprovativo_pagamento')
    can_delete = False
    def has_add_permission(self, request, obj=None): return False

class AnexoLoteComissaoInline(admin.TabularInline):
    model = AnexoLoteComissao
    extra = 0
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
    inlines = [TransacaoPagamentoComissaoInline, AnexoLoteComissaoInline]
    def has_add_permission(self, request): return False
    def has_delete_permission(self, request, obj=None): return False

# --- META ADMIN ---
class MetaVendaForm(forms.ModelForm):
    class Meta:
        model = MetaVenda
        fields = '__all__'

@admin.register(MetaVenda)
class MetaVendaAdmin(admin.ModelAdmin):
    form = MetaVendaForm
    list_display = ('data_inicio', 'data_fim', 'tipo_meta', 'valor_meta')
    list_filter = ('grupo', 'vendedor', 'data_inicio')
    search_fields = ('vendedor__username', 'grupo__name')
    fieldsets = (
        (None, {
            'fields': ('valor_meta', ('data_inicio', 'data_fim'))
        }),
        ('Tipo de Meta (Escolha apenas um, ou deixe ambos em branco para Meta Geral)', {
            'fields': ('vendedor', 'grupo')
        }),
    )
    def tipo_meta(self, obj):
        if obj.vendedor: return f"Individual ({obj.vendedor.username})"
        if obj.grupo: return f"Equipa ({obj.grupo.name})"
        return "Geral"
    tipo_meta.short_description = "Tipo de Meta"