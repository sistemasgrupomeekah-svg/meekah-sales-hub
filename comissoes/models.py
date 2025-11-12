# Em: comissoes/models.py

import os
import uuid 
from django.db import models
from decimal import Decimal
from django.db.models import Sum
from django.utils import timezone
from django.core.exceptions import ValidationError

# (Função de upload de anexo do Lote)
def get_anexo_transacao_path(instance, filename):
    """
    Cria um caminho padronizado para o anexo do lote:
    media/comissoes/lote_<id_lote>/<uuid>.<ext>
    """
    ext = os.path.splitext(filename)[1]
    unique_filename = f"{uuid.uuid4()}{ext}"
    return os.path.join('comissoes', f'lote_{instance.lote.id}', unique_filename)


class RegraComissaoVendedor(models.Model):
    # (Usamos a "string notation" para evitar erros de importação circular)
    vendedor = models.ForeignKey(
        'auth.User', 
        on_delete=models.CASCADE, 
        related_name="regras_comissao", 
        verbose_name="Vendedor Específico"
    )
    produto = models.ForeignKey(
        'common.Produto', 
        on_delete=models.CASCADE, 
        related_name="regras_comissao_excecao",
        verbose_name="Produto Específico"
    )
    
    TIPO_COMISSAO_CHOICES = (('P', 'Percentual'), ('F', 'Valor Fixo'),)
    tipo_comissao = models.CharField(max_length=1, choices=TIPO_COMISSAO_CHOICES, default='P', 
                                     verbose_name="Tipo de Comissão (Exceção)")
    valor_comissao = models.DecimalField(max_digits=10, decimal_places=2, 
                                         verbose_name="Valor da Comissão (Exceção)")

    class Meta:
        db_table = 'vendas_regracomissaovendedor' # <-- Tabela antiga
        verbose_name = "Regra de Exceção de Comissão"
        verbose_name_plural = "Regras de Exceção de Comissão"
        unique_together = ('vendedor', 'produto') 

    def __str__(self):
        return f"Exceção: {self.vendedor.username} no {self.produto.nome}"

class LotePagamentoComissao(models.Model):
    STATUS_CHOICES = (
        ('pendente', 'Pendente'),
        ('pago_parcialmente', 'Pago Parcialmente'),
        ('pago_integralmente', 'Pago Integralmente'),
    )
    vendedor = models.ForeignKey(
        'auth.User', 
        on_delete=models.PROTECT, 
        related_name="lotes_pagos",
        verbose_name="Vendedor a Pagar"
    )
    periodo_inicio = models.DateField(verbose_name="Início do Período")
    periodo_fim = models.DateField(verbose_name="Fim do Período")
    responsavel_fechamento = models.ForeignKey(
        'auth.User', 
        on_delete=models.PROTECT, 
        related_name="lotes_fechados",
        verbose_name="Responsável pelo Fechamento"
    )
    data_fechamento = models.DateTimeField(auto_now_add=True, verbose_name="Data de Fechamento")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    total_comissoes = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Total Devido (R$)")
    total_pago_efetivamente = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Total Pago (R$)")

    class Meta:
        db_table = 'vendas_lotepagamentocomissao' # <-- Tabela antiga
        verbose_name = "Lote de Pagamento de Comissão"
        verbose_name_plural = "Lotes de Pagamento de Comissão"
        ordering = ['-data_fechamento']

    def __str__(self):
        return f"Lote #{self.id} ({self.vendedor.username}) - R$ {self.total_comissoes}"

class TransacaoPagamentoComissao(models.Model):
    lote = models.ForeignKey(LotePagamentoComissao, on_delete=models.CASCADE, related_name="transacoes_pagamento")
    responsavel_pagamento = models.ForeignKey(
        'auth.User', 
        on_delete=models.PROTECT, 
        related_name="pagamentos_realizados", 
        verbose_name="Responsável pelo Pagamento"
    )
    data_pagamento = models.DateTimeField(auto_now_add=True, verbose_name="Data do Pagamento")
    valor_pago = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor Pago (R$)")
    anexo_comprovativo_pagamento = models.FileField(
        upload_to=get_anexo_transacao_path, 
        verbose_name="Anexo (Comprovativo de Pagamento)",
        null=True, blank=True
    )
    descricao = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nome Original/Descrição")

    class Meta:
        db_table = 'vendas_transacaopagamentocomissao' # <-- Tabela antiga

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

    class Meta:
        db_table = 'vendas_anexolotecomissao' # <-- Tabela antiga
    
    def __str__(self):
        return f"Anexo (NF) do Lote #{self.lote.id}"

class MetaVenda(models.Model):
    data_inicio = models.DateField(verbose_name="Data de Início")
    data_fim = models.DateField(verbose_name="Data de Fim")
    valor_meta = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor da Meta (R$)")
    vendedor = models.ForeignKey(
        'auth.User', 
        on_delete=models.CASCADE, 
        related_name="metas",
        null=True, 
        blank=True, 
        verbose_name="Vendedor (Individual)",
        help_text="Selecione um vendedor para uma meta individual."
    )
    grupo = models.ForeignKey(
        'auth.Group', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        verbose_name="Equipa (Grupo)",
        help_text="Selecione um grupo para uma meta de equipa."
    )

    class Meta:
        db_table = 'vendas_metavenda' # <-- Tabela antiga
        verbose_name = "Meta de Venda"
        verbose_name_plural = "Metas de Venda"
        ordering = ['data_inicio', 'vendedor', 'grupo']
        unique_together = ('data_inicio', 'data_fim', 'vendedor', 'grupo')

    def clean(self):
        """ Regra de Negócio: Uma meta não pode ser Individual E de Equipa ao mesmo tempo. """
        if self.vendedor and self.grupo:
            raise ValidationError("Uma meta não pode ser definida para um Vendedor individual E uma Equipa ao mesmo tempo. Escolha apenas um.")

    def __str__(self):
        if self.vendedor:
            tipo = f"Individual ({self.vendedor.get_full_name() or self.vendedor.username})"
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