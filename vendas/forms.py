from django import forms
from .models import (
    Venda, Cliente, Produto, FormaPagamento, AnexoVenda, 
    LotePagamentoComissao, TransacaoPagamentoComissao, AnexoLoteComissao
)
from decimal import Decimal 

# --- FORMULÁRIOS DA PÁGINA 'NOVA VENDA' ---

class ClienteForm(forms.ModelForm):
    """
    Formulário usado na página 'Nova Venda' para criar ou atualizar um cliente.
    """
    class Meta:
        model = Cliente
        fields = [
            'cpf_cnpj', 'nome_completo', 'email', 'telefone',
            'cep', 'endereco', 'numero', 'complemento', 
            'bairro', 'cidade', 'estado',
            'responsavel_nome', 'responsavel_cpf', 'responsavel_email'
        ]
        widgets = {
            'cpf_cnpj': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Digite apenas números'}),
            'nome_completo': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'cep': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Digite apenas números'}),
            'endereco': forms.TextInput(attrs={'class': 'form-control'}),
            'numero': forms.TextInput(attrs={'class': 'form-control'}),
            'complemento': forms.TextInput(attrs={'class': 'form-control'}),
            'bairro': forms.TextInput(attrs={'class': 'form-control'}),
            'cidade': forms.TextInput(attrs={'class': 'form-control'}),
            'estado': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 2}),
            'responsavel_nome': forms.TextInput(attrs={'class': 'form-control'}),
            'responsavel_cpf': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Digite apenas números'}),
            'responsavel_email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        """ Torna campos não essenciais opcionais no formulário """
        super(ClienteForm, self).__init__(*args, **kwargs)
        self.fields['complemento'].required = False
        self.fields['responsavel_nome'].required = False
        self.fields['responsavel_cpf'].required = False
        self.fields['responsavel_email'].required = False

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

class ClienteEditForm(forms.ModelForm):
    """ Formulário para *editar* os dados do cliente na página de detalhes. """
    class Meta:
        model = Cliente
        fields = [
            'cpf_cnpj', 'nome_completo', 'email', 'telefone',
            'cep', 'endereco', 'numero', 'complemento', 
            'bairro', 'cidade', 'estado',
            'responsavel_nome', 'responsavel_cpf', 'responsavel_email'
        ]
        # Adiciona widgets para garantir o styling (Bootstrap)
        widgets = {
            'cpf_cnpj': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Digite apenas números'}),
            'nome_completo': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'cep': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Digite apenas números'}),
            'endereco': forms.TextInput(attrs={'class': 'form-control'}),
            'numero': forms.TextInput(attrs={'class': 'form-control'}),
            'complemento': forms.TextInput(attrs={'class': 'form-control'}),
            'bairro': forms.TextInput(attrs={'class': 'form-control'}),
            'cidade': forms.TextInput(attrs={'class': 'form-control'}),
            'estado': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 2}),
            'responsavel_nome': forms.TextInput(attrs={'class': 'form-control'}),
            'responsavel_cpf': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Digite apenas números'}),
            'responsavel_email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
    def __init__(self, *args, **kwargs):
        super(ClienteEditForm, self).__init__(*args, **kwargs)
        self.fields['complemento'].required = False
        self.fields['responsavel_nome'].required = False
        self.fields['responsavel_cpf'].required = False
        self.fields['responsavel_email'].required = False

# --- FORMULÁRIOS DO MÓDULO DE COMISSÕES (ATUALIZADO) ---
class TransacaoPagamentoForm(forms.ModelForm):
    valor_pago = forms.DecimalField(
        label="Valor Pago (R$)",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    # ATUALIZADO: (Obrigatório)
    anexo_comprovativo_pagamento = forms.FileField(
        label="Anexar Comprovativo (do Pagamento)",
        required=True, 
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = TransacaoPagamentoComissao
        # ATUALIZADO: Removido o campo de NF
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