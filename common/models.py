# Em: common/models.py

from django.db import models

# (Nota: Não precisamos de 'User' aqui, pois estes modelos são "passivos")

class Produto(models.Model):
    nome = models.CharField(max_length=255, verbose_name="Nome do Produto")
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição")
    valor = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor Base (Honorários Iniciais)")
    
    TIPO_COMISSAO_CHOICES = (('P', 'Percentual'), ('F', 'Valor Fixo'),)
    tipo_comissao = models.CharField(max_length=1, choices=TIPO_COMISSAO_CHOICES, default='P', verbose_name="Tipo de Comissão")
    valor_comissao = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor da Comissão")

    valor_entrada_sugerido = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Entrada Sugerida")
    num_parcelas_sugerido = models.IntegerField(null=True, blank=True, verbose_name="Nº de Parcelas Sugerido")
    valor_parcela_sugerido = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Valor da Parcela Sugerido")
    valor_exito_sugerido = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Êxito Sugerido")
    valor_aporte_sugerido = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Aporte Sugerido")

    class Meta:
        db_table = 'vendas_produto' # <-- Informa ao Django para usar a tabela antiga

    def __str__(self): 
        return self.nome

class Cliente(models.Model):
    nome_completo = models.CharField(max_length=255, verbose_name="Nome Completo / Razão Social")
    email = models.EmailField(max_length=255, unique=True, verbose_name="E-mail")
    cpf_cnpj = models.CharField(max_length=18, unique=True, verbose_name="CPF/CNPJ")
    telefone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefone")
    
    endereco = models.CharField(max_length=255, blank=True, null=True, verbose_name="Endereço")
    numero = models.CharField(max_length=20, blank=True, null=True, verbose_name="Número")
    complemento = models.CharField(max_length=100, blank=True, null=True, verbose_name="Complemento")
    bairro = models.CharField(max_length=100, blank=True, null=True, verbose_name="Bairro")
    cidade = models.CharField(max_length=100, blank=True, null=True, verbose_name="Cidade")
    estado = models.CharField(max_length=2, blank=True, null=True, verbose_name="UF")
    cep = models.CharField(max_length=10, blank=True, null=True, verbose_name="CEP")

    responsavel_nome = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nome do Responsável")
    responsavel_cpf = models.CharField(max_length=14, blank=True, null=True, verbose_name="CPF do Responsável")
    responsavel_email = models.EmailField(max_length=255, blank=True, null=True, verbose_name="E-mail do Responsável")
    
    class Meta:
        db_table = 'vendas_cliente' # <-- Informa ao Django para usar a tabela antiga

    def __str__(self): 
        return f"{self.nome_completo} ({self.cpf_cnpj})"

class FormaPagamento(models.Model):
    nome = models.CharField(max_length=100, unique=True, verbose_name="Nome da Forma de Pagamento")
    
    class Meta: 
        db_table = 'vendas_formapagamento' # <-- Informa ao Django para usar a tabela antiga
        verbose_name = "Forma de Pagamento"
        verbose_name_plural = "Formas de Pagamento"
    
    def __str__(self): 
        return self.nome