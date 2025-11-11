from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter
@stringfilter
def status_to_color(status_value):
    mapping = {
        # Status Pagamento Venda
        'pendente': 'secondary',
        'aguardando_validacao': 'warning',
        'aprovado': 'success',
        'reprovado': 'danger',
        
        # Status Contrato
        'nao_gerado': 'secondary', 'gerado': 'info',
        'assinado': 'primary', 'finalizado': 'success',
        
        # Status Venda
        'iniciada': 'secondary', 'em_negociacao': 'info',
        'aguardando_pagamento': 'warning', 'em_contrato': 'primary',
        'concluida': 'success', 'perdida': 'danger',
        
        # ATUALIZADO (Req 2): Status do Lote
        # 'pago' antigo removido
        'pago_parcialmente': 'warning',
        'pago_integralmente': 'success',
    }
    return mapping.get(status_value, 'light')


@register.simple_tag
def user_can_create_vendas(user):
    if not user.is_authenticated: return False
    if user.is_superuser: return True
    if user.groups.filter(name__in=['Gestor', 'Vendedor']).exists(): return True
    return False

@register.simple_tag
def user_can_manage_comissoes(user):
    if not user.is_authenticated: return False
    if user.is_superuser: return True
    if user.groups.filter(name__in=['Gestor', 'Financeiro']).exists(): return True
    return False

@register.simple_tag
def user_can_manage_metas(user):
    """ Verifica se o user é Admin ou Gestor para gerir metas """
    if not user.is_authenticated: return False
    if user.is_superuser: return True
    if user.groups.filter(name='Gestor').exists(): return True
    return False