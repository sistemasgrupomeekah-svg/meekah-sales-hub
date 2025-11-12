from django import forms
from .models import (
    LotePagamentoComissao, TransacaoPagamentoComissao, AnexoLoteComissao, MetaVenda
)
from decimal import Decimal 
from django.contrib.auth.models import Group, User

class TransacaoPagamentoForm(forms.ModelForm):
    valor_pago = forms.DecimalField(
        label="Valor Pago (R$)",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    anexo_comprovativo_pagamento = forms.FileField(
        label="Anexar Comprovativo (do Pagamento)",
        required=True, 
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = TransacaoPagamentoComissao
        fields = ['valor_pago', 'anexo_comprovativo_pagamento']

    def __init__(self, *args, **kwargs):
        self.lote = kwargs.pop('lote', None) 
        super(TransacaoPagamentoForm, self).__init__(*args, **kwargs)

    def clean_valor_pago(self):
        valor_pago = self.cleaned_data.get('valor_pago')
        if valor_pago <= 0:
            raise forms.ValidationError("O valor pago deve ser positivo.")
        if self.lote:
            saldo_devedor = self.lote.total_comissoes - self.lote.total_pago_efetivamente
            if valor_pago > (saldo_devedor + Decimal('0.01')):
                raise forms.ValidationError(
                    f"O valor pago (R$ {valor_pago}) é maior que o saldo devedor (R$ {saldo_devedor})."
                )
        return valor_pago
    
class AnexoLoteForm(forms.ModelForm):
    """
    Formulário separado para anexar a NF do Vendedor ao Lote.
    """
    anexo_nf_vendedor = forms.FileField(
        label="Anexar Nota Fiscal (do Vendedor)",
        required=True, # A NF é obrigatória *neste* formulário
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = AnexoLoteComissao
        fields = ['anexo_nf_vendedor']

class MetaVendaForm(forms.ModelForm):
    """ Formulário para Admin/Gestor criar ou editar metas no front-end. """
    
    # Filtra o queryset para mostrar apenas vendedores (não Admin/Financeiro/etc.)
    vendedor = forms.ModelChoiceField(
        queryset=User.objects.filter(groups__name='Vendedor'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Vendedor (Individual)"
    )
    
    # Filtra para mostrar apenas grupos relevantes (opcional, mas boa prática)
    grupo = forms.ModelChoiceField(
        queryset=Group.objects.exclude(name__in=['Gestor', 'Financeiro', 'Advogado']),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Equipa (Grupo)"
    )

    class Meta:
        model = MetaVenda
        fields = [
            'data_inicio', 'data_fim', 'valor_meta', 
            'vendedor', 'grupo'
        ]
        widgets = {
            'data_inicio': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'data_fim': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'valor_meta': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 50000.00'}),
        }
        
    def clean(self):
        """ Re-aplica a validação do modelo """
        cleaned_data = super().clean()
        vendedor = cleaned_data.get('vendedor')
        grupo = cleaned_data.get('grupo')
        
        if vendedor and grupo:
            raise forms.ValidationError(
                "Uma meta não pode ser definida para um Vendedor individual E uma Equipa ao mesmo tempo. Escolha apenas um."
            )
        return cleaned_data