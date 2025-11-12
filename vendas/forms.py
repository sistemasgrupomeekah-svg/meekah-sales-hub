# Em: vendas/forms.py (Atualizado)

from django import forms
from .models import Venda, AnexoVenda
from decimal import Decimal 

# --- NOVOS IMPORTS ---
# Importa os modelos partilhados da app 'common'
from common.models import Produto, FormaPagamento
# --- FIM NOVOS IMPORTS ---

# Os forms 'ClienteForm' e 'ClienteEditForm' foram MOVIDOS para 'common/forms.py'
# Os forms de Comissões e Metas foram MOVIDOS para 'comissoes/forms.py'

# --- FORMULÁRIOS DA PÁGINA 'NOVA VENDA' ---

class AnexoForm(forms.ModelForm):
    """
    Formulário genérico para upload de anexos (CSV, Contrato, NF).
    O atributo 'multiple' é definido no HTML (template), não aqui.
    """
    arquivo = forms.FileField(
        label="Adicionar Anexo(s)", 
        required=True, 
        widget=forms.FileInput(attrs={
            # O nome 'arquivos' é esperado pela view 'detalhe_venda'
            # O nome 'arquivo' é esperado pela view 'nova_venda'
            # O JavaScript nos templates corrige isto.
        })
    )
    
    class Meta:
        model = AnexoVenda
        fields = ['arquivo'] 

class VendaForm(forms.ModelForm):
    """
    Formulário principal para *criar* uma nova venda.
    """
    # Atualiza os imports dos Querysets
    produto = forms.ModelChoiceField(queryset=Produto.objects.all(), widget=forms.Select(attrs={'class': 'form-select'}), label="Produto")
    forma_pagamento = forms.ModelChoiceField(queryset=FormaPagamento.objects.all(), required=False, widget=forms.Select(attrs={'class': 'form-select'}), label="Forma de Pagamento")
    
    honorarios = forms.DecimalField(label="Honorários Totais (Calculado)", required=False, 
                                    widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': True }))
    valor_entrada = forms.DecimalField(label="Valor da Entrada (Negociado)", required=False, 
                                       widget=forms.TextInput(attrs={'class': 'form-control'}))
    num_parcelas = forms.IntegerField(label="Nº de Parcelas (Negociado)", required=False, 
                                      widget=forms.NumberInput(attrs={'class': 'form-control'}))
    valor_parcela = forms.DecimalField(label="Valor da Parcela (Negociado)", required=False, 
                                       widget=forms.TextInput(attrs={'class': 'form-control'}))
    valor_exito = forms.DecimalField(label="Honorários no Êxito (Negociado)", required=False, 
                                     widget=forms.TextInput(attrs={'class': 'form-control'}))
    valor_aporte = forms.DecimalField(label="Valor de Aporte (Negociado)", required=False, 
                                     widget=forms.TextInput(attrs={'class': 'form-control'}))
    observacoes = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}), label="Observações (Internas)")

    class Meta:
        model = Venda
        fields = [
            'produto', 'forma_pagamento', 'honorarios', 
            'valor_entrada', 'num_parcelas', 'valor_parcela',
            'valor_exito', 'valor_aporte',
            'observacoes'
        ]

    def clean(self):
        """ Regra de negócio: Honorários = Entrada + Parcelas + Êxito """
        cleaned_data = super().clean()
        entrada = cleaned_data.get('valor_entrada') or Decimal(0)
        num_parcelas = cleaned_data.get('num_parcelas') or 0
        valor_parcela = cleaned_data.get('valor_parcela') or Decimal(0)
        exito = cleaned_data.get('valor_exito') or Decimal(0)
        
        # 'valor_aporte' NÃO entra na soma
        total_calculado = entrada + (Decimal(num_parcelas) * valor_parcela) + exito
        
        cleaned_data['honorarios'] = total_calculado
        return cleaned_data

# --- FORMULÁRIOS DA PÁGINA 'DETALHE VENDA' ---

# --- Formulários de Edição de Status (por perfil) ---
class VendaStatusAdminForm(forms.ModelForm):
    """ Edita os 3 status (Admin/Gestor) """
    class Meta:
        model = Venda
        fields = ['status_venda', 'status_pagamento', 'status_contrato']
        widgets = {
            'status_venda': forms.Select(attrs={'class': 'form-select'}),
            'status_pagamento': forms.Select(attrs={'class': 'form-select'}),
            'status_contrato': forms.Select(attrs={'class': 'form-select'}),
        }

class VendaStatusVendedorForm(forms.ModelForm):
    """ Edita apenas o status da venda (Vendedor) """
    class Meta:
        model = Venda
        fields = ['status_venda']
        widgets = { 'status_venda': forms.Select(attrs={'class': 'form-select'}) }

class VendaStatusFinanceiroForm(forms.ModelForm):
    """ Edita apenas o status do pagamento (Financeiro) """
    class Meta:
        model = Venda
        fields = ['status_pagamento']
        widgets = { 'status_pagamento': forms.Select(attrs={'class': 'form-select'}) }

class VendaStatusAdvogadoForm(forms.ModelForm):
    """ Edita apenas o status do contrato (Advogado) """
    class Meta:
        model = Venda
        fields = ['status_contrato']
        widgets = { 'status_contrato': forms.Select(attrs={'class': 'form-select'}) }

# --- Formulários de Edição de Dados (Admin/Gestor/Vendedor) ---
class VendaEditForm(forms.ModelForm):
    """ Formulário para *editar* os valores da venda na página de detalhes. """
    honorarios = forms.DecimalField(label="Honorários Totais (Calculado)", required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': True}))
    valor_entrada = forms.DecimalField(label="Valor da Entrada (Negociado)", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    num_parcelas = forms.IntegerField(label="Nº de Parcelas (Negociado)", required=False, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    valor_parcela = forms.DecimalField(label="Valor da Parcela (Negociado)", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    valor_exito = forms.DecimalField(label="Honorários no Êxito (Negociado)", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    valor_aporte = forms.DecimalField(label="Valor de Aporte (Negociado)", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    observacoes = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}), label="Observações (Internas)")
    
    # Atualiza o import do Queryset
    forma_pagamento = forms.ModelChoiceField(queryset=FormaPagamento.objects.all(), required=False, widget=forms.Select(attrs={'class': 'form-select'}), label="Forma de Pagamento")

    # Campo de Comissão (para Admin/Gestor)
    comissao_personalizada_valor = forms.DecimalField(
        label="Comissão Personalizada (R$) (Admin/Gestor)", 
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control'}) 
    )

    class Meta:
        model = Venda
        fields = ['forma_pagamento', 'honorarios', 'valor_entrada', 
                  'num_parcelas', 'valor_parcela', 'valor_exito', 
                  'valor_aporte', 'observacoes', 
                  'comissao_personalizada_valor']
    
    def clean(self):
        """ Repete a regra de negócio do cálculo de honorários. """
        cleaned_data = super().clean()
        entrada = cleaned_data.get('valor_entrada') or Decimal(0)
        num_parcelas = cleaned_data.get('num_parcelas') or 0
        valor_parcela = cleaned_data.get('valor_parcela') or Decimal(0)
        exito = cleaned_data.get('valor_exito') or Decimal(0)
        cleaned_data['honorarios'] = entrada + (Decimal(num_parcelas) * valor_parcela) + exito
        return cleaned_data