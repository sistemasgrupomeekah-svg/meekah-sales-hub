from django import forms
from .models import Cliente

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