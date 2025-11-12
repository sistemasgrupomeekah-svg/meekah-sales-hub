# Em: vendas/models.py

import os
import uuid 
from django.db import models
from django.contrib.auth.models import User 

# (Função de upload de anexo da Venda permanece aqui)
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

class Venda(models.Model):
    # (As definições de CHOICES permanecem as mesmas)
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
    
    # Relações (Usando "string notation" para evitar importações circulares)
    vendedor = models.ForeignKey(
        'auth.User', 
        on_delete=models.PROTECT, 
        related_name="vendas", 
        verbose_name="Vendedor"
    )
    cliente = models.ForeignKey(
        'common.Cliente', 
        on_delete=models.PROTECT, 
        related_name="compras", 
        verbose_name="Cliente"
    )
    produto = models.ForeignKey(
        'common.Produto', 
        on_delete=models.PROTECT, 
        related_name="vendas", 
        verbose_name="Produto"
    )
    forma_pagamento = models.ForeignKey(
        'common.FormaPagamento', 
        on_delete=models.PROTECT, 
        null=True, blank=True, 
        verbose_name="Forma de Pagamento"
    )
    
    # (Valores, Status, Dados e Comissionamento permanecem os mesmos)
    honorarios = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Honorários Totais (Calculado)")
    valor_entrada = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Valor da Entrada (Negociado)")
    num_parcelas = models.IntegerField(null=True, blank=True, verbose_name="Nº de Parcelas (Negociado)")
    valor_parcela = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Valor da Parcela (Negociado)")
    valor_exito = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Honorários no Êxito (Negociado)")
    valor_aporte = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Valor de Aporte (Negociado)")
    
    data_venda = models.DateTimeField(auto_now_add=True, verbose_name="Data da Venda")
    status_venda = models.CharField(max_length=30, choices=STATUS_VENDA_CHOICES, default='iniciada')
    status_pagamento = models.CharField(max_length=30, choices=STATUS_PAGAMENTO_CHOICES, default='pendente')
    status_contrato = models.CharField(max_length=30, choices=STATUS_CONTRATO_CHOICES, default='nao_gerado')
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações Internas")

    comissao_personalizada_valor = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, 
        verbose_name="Comissão Personalizada (R$)",
        help_text="Se preenchido, este valor substitui todas as outras regras de cálculo."
    )
    comissao_calculada_final = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, 
        verbose_name="Comissão Final Calculada (R$)"
    )

    # Relação com Lote (usando string notation)
    lote_pagamento = models.ForeignKey(
        'comissoes.LotePagamentoComissao', 
        on_delete=models.SET_NULL,
        related_name="vendas",
        null=True, blank=True,
        verbose_name="Lote de Pagamento"
    )
    
    # (NÃO adicionamos db_table aqui, pois este modelo não se moveu)
    
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
    
    # (NÃO adicionamos db_table aqui)
    
    class Meta: 
        verbose_name = "Anexo da Venda"
        verbose_name_plural = "Anexos da Venda"
    
    def __str__(self): 
        return f"{self.get_tipo_display()} da Venda #{self.venda.id}"