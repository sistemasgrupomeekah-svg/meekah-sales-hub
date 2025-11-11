import os
import uuid 
from django.db import models
from django.contrib.auth.models import User 
from decimal import Decimal
from django.db.models import Sum # Para calcular a soma
from django.utils import timezone # <-- Importado para o MetaVenda
from django.contrib.auth.models import Group # <-- Importar Grupo
from django.core.exceptions import ValidationError # <-- Importar

# --- Funções de Upload ---

def get_anexo_upload_path(instance, filename):
    """
    Cria um caminho padronizado para o anexo da venda:
    media/vendas/venda_<id_venda>/<tipo_anexo>/<uuid>.<ext>
    """
    ext = os.path.splitext(filename)[1]
    unique_filename = f"{uuid.uuid4()}{ext}"
    return os.path.join(
        'vendas', 
        f'venda_{instance.venda.id}', 
        instance.tipo, 
        unique_filename
    )

def get_anexo_transacao_path(instance, filename):
    """
    Cria um caminho padronizado para o anexo do lote:
    media/comissoes/lote_<id_lote>/<uuid>.<ext>
    """
    ext = os.path.splitext(filename)[1]
    unique_filename = f"{uuid.uuid4()}{ext}"
    return os.path.join('comissoes', f'lote_{instance.lote.id}', unique_filename)


# --- Modelos Principais ---

class Produto(models.Model):
    nome = models.CharField(max_length=255, verbose_name="Nome do Produto")
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição")
    valor = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor Base (Honorários Iniciais)")
    
    # Comissão Padrão
    TIPO_COMISSAO_CHOICES = (('P', 'Percentual'), ('F', 'Valor Fixo'),)
    tipo_comissao = models.CharField(max_length=1, choices=TIPO_COMISSAO_CHOICES, default='P', verbose_name="Tipo de Comissão")
    valor_comissao = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor da Comissão")

    # Valores Sugeridos (para o form 'Nova Venda')
    valor_entrada_sugerido = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Entrada Sugerida")
    num_parcelas_sugerido = models.IntegerField(null=True, blank=True, verbose_name="Nº de Parcelas Sugerido")
    valor_parcela_sugerido = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Valor da Parcela Sugerido")
    valor_exito_sugerido = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Êxito Sugerido")
    valor_aporte_sugerido = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Aporte Sugerido")

    def __str__(self): 
        return self.nome

class Cliente(models.Model):
    # Dados Principais
    nome_completo = models.CharField(max_length=255, verbose_name="Nome Completo / Razão Social")
    email = models.EmailField(max_length=255, unique=True, verbose_name="E-mail")
    cpf_cnpj = models.CharField(max_length=18, unique=True, verbose_name="CPF/CNPJ")
    telefone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefone")
    
    # Endereço
    endereco = models.CharField(max_length=255, blank=True, null=True, verbose_name="Endereço")
    numero = models.CharField(max_length=20, blank=True, null=True, verbose_name="Número")
    complemento = models.CharField(max_length=100, blank=True, null=True, verbose_name="Complemento")
    bairro = models.CharField(max_length=100, blank=True, null=True, verbose_name="Bairro")
    cidade = models.CharField(max_length=100, blank=True, null=True, verbose_name="Cidade")
    estado = models.CharField(max_length=2, blank=True, null=True, verbose_name="UF")
    cep = models.CharField(max_length=10, blank=True, null=True, verbose_name="CEP")

    # Responsável (para PJ)
    responsavel_nome = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nome do Responsável")
    responsavel_cpf = models.CharField(max_length=14, blank=True, null=True, verbose_name="CPF do Responsável")
    responsavel_email = models.EmailField(max_length=255, blank=True, null=True, verbose_name="E-mail do Responsável")
    
    def __str__(self): 
        return f"{self.nome_completo} ({self.cpf_cnpj})"

class FormaPagamento(models.Model):
    nome = models.CharField(max_length=100, unique=True, verbose_name="Nome da Forma de Pagamento")
    
    class Meta: 
        verbose_name = "Forma de Pagamento"
        verbose_name_plural = "Formas de Pagamento"
    
    def __str__(self): 
        return self.nome

class Venda(models.Model):
    # Status
    STATUS_PAGAMENTO_CHOICES = (
        ('pendente', 'Pendente (Sem comprovante)'), 
        ('aguardando_validacao', 'Aguardando Validação'),
        ('aprovado', 'Aprovado'), 
        ('reprovado', 'Reprovado'),
    )
    STATUS_CONTRATO_CHOICES = (
        ('nao_gerado', 'Não Gerado'), 
        ('gerado', 'Gerado (Pendente Assinatura)'),
        ('assinado', 'Assinado'), 
        ('finalizado', 'Finalizado'),
    )
    STATUS_VENDA_CHOICES = (
        ('iniciada', 'Iniciada'), 
        ('em_negociacao', 'Em Negociação'),
        ('aguardando_pagamento', 'Aguardando Pagamento'), 
        ('em_contrato', 'Em Contrato'),
        ('concluida', 'Concluída'), 
        ('perdida', 'Perdida'),
    )
    
    # Relações
    vendedor = models.ForeignKey(User, on_delete=models.PROTECT, related_name="vendas", verbose_name="Vendedor")
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name="compras", verbose_name="Cliente")
    produto = models.ForeignKey(Produto, on_delete=models.PROTECT, related_name="vendas", verbose_name="Produto")
    forma_pagamento = models.ForeignKey(FormaPagamento, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Forma de Pagamento")
    
    # Valores (Negociados)
    honorarios = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Honorários Totais (Calculado)")
    valor_entrada = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Valor da Entrada (Negociado)")
    num_parcelas = models.IntegerField(null=True, blank=True, verbose_name="Nº de Parcelas (Negociado)")
    valor_parcela = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Valor da Parcela (Negociado)")
    valor_exito = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Honorários no Êxito (Negociado)")
    valor_aporte = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Valor de Aporte (Negociado)")
    
    # Status e Dados
    data_venda = models.DateTimeField(auto_now_add=True, verbose_name="Data da Venda")
    status_venda = models.CharField(max_length=30, choices=STATUS_VENDA_CHOICES, default='iniciada')
    status_pagamento = models.CharField(max_length=30, choices=STATUS_PAGAMENTO_CHOICES, default='pendente')
    status_contrato = models.CharField(max_length=30, choices=STATUS_CONTRATO_CHOICES, default='nao_gerado')
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações Internas")

    # Comissionamento (Fase 1)
    comissao_personalizada_valor = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, 
        verbose_name="Comissão Personalizada (R$)",
        help_text="Se preenchido, este valor substitui todas as outras regras de cálculo."
    )
    comissao_calculada_final = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, 
        verbose_name="Comissão Final Calculada (R$)"
    )

    # Pagamento (Fase 2)
    lote_pagamento = models.ForeignKey(
        'LotePagamentoComissao', 
        on_delete=models.SET_NULL, # Se o lote for apagado, a venda fica "não paga"
        related_name="vendas",
        null=True, blank=True,
        verbose_name="Lote de Pagamento"
    )
    
    def __str__(self): 
        return f"Venda #{self.id} - {self.cliente.nome_completo}"

class AnexoVenda(models.Model):
    TIPO_ANEXO_CHOICES = (
        ('comprovante', 'Comprovante de Pagamento'),
        ('contrato', 'Contrato'),
        ('nota_fiscal', 'Nota Fiscal'),
    )
    venda = models.ForeignKey(Venda, on_delete=models.CASCADE, related_name="anexos", verbose_name="Venda")
    tipo = models.CharField(max_length=20, choices=TIPO_ANEXO_CHOICES, default='comprovante')
    arquivo = models.FileField(upload_to=get_anexo_upload_path, verbose_name="Arquivo")
    descricao = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nome Original")
    data_upload = models.DateTimeField(auto_now_add=True, verbose_name="Data do Upload")
    
    class Meta: 
        verbose_name = "Anexo da Venda"
        verbose_name_plural = "Anexos da Venda"
    
    def __str__(self): 
        return f"{self.get_tipo_display()} da Venda #{self.venda.id}"

# --- Modelos de Comissionamento ---

class RegraComissaoVendedor(models.Model):
    vendedor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="regras_comissao", 
                                 verbose_name="Vendedor Específico")
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name="regras_comissao_excecao",
                                verbose_name="Produto Específico")
    
    TIPO_COMISSAO_CHOICES = (('P', 'Percentual'), ('F', 'Valor Fixo'),)
    tipo_comissao = models.CharField(max_length=1, choices=TIPO_COMISSAO_CHOICES, default='P', 
                                     verbose_name="Tipo de Comissão (Exceção)")
    valor_comissao = models.DecimalField(max_digits=10, decimal_places=2, 
                                         verbose_name="Valor da Comissão (Exceção)")

    class Meta:
        verbose_name = "Regra de Exceção de Comissão"
        verbose_name_plural = "Regras de Exceção de Comissão"
        unique_together = ('vendedor', 'produto') 

    def __str__(self):
        return f"Exceção: {self.vendedor.username} no {self.produto.nome}"

class LotePagamentoComissao(models.Model):
    # A "Fatura" para o Vendedor
    STATUS_CHOICES = (
        ('pendente', 'Pendente'),
        ('pago_parcialmente', 'Pago Parcialmente'),
        ('pago_integralmente', 'Pago Integralmente'),
    )
    
    vendedor = models.ForeignKey(User, on_delete=models.PROTECT, 
                                 related_name="lotes_pagos",
                                 verbose_name="Vendedor a Pagar")
    
    periodo_inicio = models.DateField(verbose_name="Início do Período")
    periodo_fim = models.DateField(verbose_name="Fim do Período")
    
    responsavel_fechamento = models.ForeignKey(User, on_delete=models.PROTECT, 
                                               related_name="lotes_fechados",
                                               verbose_name="Responsável pelo Fechamento")
    
    data_fechamento = models.DateTimeField(auto_now_add=True, verbose_name="Data de Fechamento")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    
    total_comissoes = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Total Devido (R$)")
    total_pago_efetivamente = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Total Pago (R$)")

    class Meta:
        verbose_name = "Lote de Pagamento de Comissão"
        verbose_name_plural = "Lotes de Pagamento de Comissão"
        ordering = ['-data_fechamento']

    def __str__(self):
        return f"Lote #{self.id} ({self.vendedor.username}) - R$ {self.total_comissoes}"

class TransacaoPagamentoComissao(models.Model):
    lote = models.ForeignKey(LotePagamentoComissao, on_delete=models.CASCADE, related_name="transacoes_pagamento")
    responsavel_pagamento = models.ForeignKey(User, on_delete=models.PROTECT, related_name="pagamentos_realizados", verbose_name="Responsável pelo Pagamento")
    data_pagamento = models.DateTimeField(auto_now_add=True, verbose_name="Data do Pagamento")
    valor_pago = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor Pago (R$)")
    
    anexo_comprovativo_pagamento = models.FileField(
        upload_to=get_anexo_transacao_path, 
        verbose_name="Anexo (Comprovativo de Pagamento)",
        null=True, blank=True # Opcional, mas o form vai obrigar
    )
    
    descricao = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nome Original/Descrição")

    def __str__(self):
        return f"Pagamento de R$ {self.valor_pago} para Lote #{self.lote.id}"

    def save(self, *args, **kwargs):
        """ Gatilho para atualizar o Lote """
        super().save(*args, **kwargs)
        lote = self.lote
        novo_total_pago = lote.transacoes_pagamento.aggregate(soma=Sum('valor_pago'))['soma'] or Decimal(0)
        lote.total_pago_efetivamente = novo_total_pago
        if novo_total_pago == 0:
            lote.status = 'pendente'
        elif novo_total_pago < lote.total_comissoes:
            lote.status = 'pago_parcialmente'
        else:
            lote.status = 'pago_integralmente'
        lote.save()

class AnexoLoteComissao(models.Model):
    lote = models.ForeignKey(LotePagamentoComissao, on_delete=models.CASCADE, 
                             related_name="anexos_lote")
    anexo_nf_vendedor = models.FileField(
        upload_to=get_anexo_transacao_path, 
        verbose_name="Anexo (Nota Fiscal do Vendedor)",
        null=True, blank=True
    )
    descricao = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nome Original/Descrição")
    data_upload = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Anexo (NF) do Lote #{self.lote.id}"

# --- NOVO MODELO (Metas) ---

class MetaVenda(models.Model):
    data_inicio = models.DateField(verbose_name="Data de Início")
    data_fim = models.DateField(verbose_name="Data de Fim")
    
    valor_meta = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor da Meta (R$)")
    
    vendedor = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="metas",
        null=True, 
        blank=True, 
        verbose_name="Vendedor (Individual)",
        help_text="Selecione um vendedor para uma meta individual."
    )
    
    # --- NOVO CAMPO ---
    grupo = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Equipa (Grupo)",
        help_text="Selecione um grupo para uma meta de equipa."
    )
    # --- FIM NOVO CAMPO ---

    class Meta:
        verbose_name = "Meta de Venda"
        verbose_name_plural = "Metas de Venda"
        ordering = ['data_inicio', 'vendedor', 'grupo']
        # Garante que não há conflitos
        unique_together = ('data_inicio', 'data_fim', 'vendedor', 'grupo')

    def clean(self):
        """ Regra de Negócio: Uma meta não pode ser Individual E de Equipa ao mesmo tempo. """
        if self.vendedor and self.grupo:
            raise ValidationError("Uma meta não pode ser definida para um Vendedor individual E uma Equipa ao mesmo tempo. Escolha apenas um.")

    def __str__(self):
        if self.vendedor:
            tipo = f"Individual ({self.vendedor.username})"
        elif self.grupo:
            tipo = f"Equipa ({self.grupo.name})"
        else:
            tipo = "GERAL"
        return f"Meta {self.data_inicio.strftime('%d/%m/%Y')} a {self.data_fim.strftime('%d/%m/%Y')} ({tipo})"

    @property
    def is_ativa(self):
        """ Propriedade para verificar se a meta está ativa hoje. """
        today = timezone.now().date()
        return self.data_inicio <= today <= self.data_fim