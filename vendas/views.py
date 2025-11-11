from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages 
from .models import (
    Venda, Cliente, Produto, FormaPagamento, AnexoVenda, User, 
    RegraComissaoVendedor, LotePagamentoComissao, TransacaoPagamentoComissao
)
from .forms import (
    VendaForm, ClienteForm, AnexoForm,
    VendaStatusAdminForm, VendaStatusVendedorForm, 
    VendaStatusFinanceiroForm, VendaStatusAdvogadoForm, 
    VendaEditForm, ClienteEditForm,
    TransacaoPagamentoForm, AnexoLoteForm
)
from django.db import transaction 
from django.http import JsonResponse, HttpResponseForbidden, HttpResponse
from django.db.models import Q, Sum, Avg, Count
from django.db.models.functions import TruncMonth
import json, csv, openpyxl
from datetime import datetime, timedelta
from decimal import Decimal
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm

# ---
# SEÇÃO 1: FUNÇÕES AUXILIARES (LÓGICA INTERNA)
# ---

def _get_user_permissions(user):
    """
    Verifica os grupos do utilizador e retorna um dicionário de flags.
    """
    return {
        'is_admin': user.is_superuser,
        'is_gestor': user.groups.filter(name='Gestor').exists(),
        'is_financeiro': user.groups.filter(name='Financeiro').exists(),
        'is_advogado': user.groups.filter(name='Advogado').exists(),
        'is_vendedor': user.groups.filter(name='Vendedor').exists(),
    }

def _calcular_e_salvar_comissao(venda):
    """
    Executa a cascata de lógica de cálculo de comissão (Regras 1, 2, 3)
    e salva o resultado na venda.
    """
    
    # Regra 1: Comissão Personalizada (Req 3)
    if venda.comissao_personalizada_valor is not None:
        venda.comissao_calculada_final = venda.comissao_personalizada_valor
        venda.save()
        return

    # Regra 2: Exceção por Vendedor (Req 2)
    regra = RegraComissaoVendedor.objects.filter(vendedor=venda.vendedor, produto=venda.produto).first()
    if regra:
        if regra.tipo_comissao == 'F': # Fixo
            venda.comissao_calculada_final = regra.valor_comissao
        else: # Percentual
            venda.comissao_calculada_final = venda.honorarios * (regra.valor_comissao / Decimal(100))
        venda.save()
        return

    # Regra 3: Padrão do Produto (Req 1, 7)
    produto = venda.produto
    if produto.tipo_comissao == 'F': # Fixo
        venda.comissao_calculada_final = produto.valor_comissao
    else: # Percentual
        venda.comissao_calculada_final = venda.honorarios * (produto.valor_comissao / Decimal(100))
    venda.save()
    return

def _get_vendas_filtradas(request):
    """
    Função auxiliar que lê os filtros do request (GET) e retorna
    o queryset de Vendas já filtrado e com as permissões corretas.
    """
    perms = _get_user_permissions(request.user)
    
    query_cliente = request.GET.get('cliente', '')
    query_vendedor = request.GET.get('vendedor', '')
    query_data_inicio = request.GET.get('data_inicio', '')
    query_data_fim = request.GET.get('data_fim', '')
    query_produto = request.GET.get('produto', '')
    query_status_venda = request.GET.get('status_venda', '')
    query_status_pagamento = request.GET.get('status_pagamento', '')
    query_status_contrato = request.GET.get('status_contrato', '')

    # Query Base
    if perms['is_admin'] or perms['is_gestor'] or perms['is_financeiro'] or perms['is_advogado']:
        vendas = Venda.objects.all()
    else: 
        vendas = Venda.objects.filter(vendedor=request.user)

    # Aplicar filtros
    if query_cliente:
        vendas = vendas.filter(cliente__nome_completo__icontains=query_cliente)
    if (perms['is_admin'] or perms['is_gestor'] or perms['is_financeiro'] or perms['is_advogado']) and query_vendedor:
        vendas = vendas.filter(vendedor_id=query_vendedor)
    if query_data_inicio:
        vendas = vendas.filter(data_venda__gte=query_data_inicio)
    if query_data_fim:
        try:
            # CORREÇÃO: Adiciona 1 dia ao data_fim para incluir o dia inteiro
            data_fim_plus_one = datetime.strptime(query_data_fim, '%Y-%m-%d').date() + timedelta(days=1)
            vendas = vendas.filter(data_venda__lt=data_fim_plus_one)
        except (ValueError, TypeError): 
            pass # Ignora filtro de data fim inválido
    if query_produto:
        vendas = vendas.filter(produto_id=query_produto)
    if query_status_venda:
        vendas = vendas.filter(status_venda=query_status_venda)
    if query_status_pagamento:
        vendas = vendas.filter(status_pagamento=query_status_pagamento)
    if query_status_contrato:
        vendas = vendas.filter(status_contrato=query_status_contrato)
        
    # Otimiza a query
    return vendas.select_related('cliente', 'produto', 'vendedor').order_by('-data_venda')

# ---
# SEÇÃO 2: VIEWS DE AUTENTICAÇÃO
# ---

def login_view(request):
    """ Página de login personalizada (/login/) """
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form, 'next': request.GET.get('next', '/')})

@login_required
def logout_view(request):
    """ Página de logout (/logout/) """
    logout(request)
    return redirect('login') 

# ---
# SEÇÃO 3: VIEWS DAS ABAS PRINCIPAIS
# ---

@login_required
def dashboard_graficos(request):
    """ Aba 1: Dashboard (Gráficos e KPIs) """
    perms = _get_user_permissions(request.user)
    
    # Define datas padrão (últimos 30 dias) se não houver filtro
    today = datetime.now().date()
    default_start_str = (today - timedelta(days=30)).strftime('%Y-%m-%d')
    default_end_str = today.strftime('%Y-%m-%d')
    
    # Usa o helper para pegar os dados já filtrados
    vendas_filtradas = _get_vendas_filtradas(request)
        
    # Cálculo de KPIs
    kpis = vendas_filtradas.aggregate(
        total_vendas=Sum('honorarios'),
        ticket_medio=Avg('honorarios'),
        contagem_vendas=Count('id')
    )
    kpi_variacao_mes_anterior = 0 # (Lógica futura)

    # Dados para Gráficos
    vendas_por_vendedor = vendas_filtradas.values('vendedor__username').annotate(total=Sum('honorarios')).order_by('-total')
    vendas_por_produto = vendas_filtradas.values('produto__nome').annotate(total=Sum('honorarios')).order_by('-total')
    vendas_por_mes = vendas_filtradas.annotate(mes=TruncMonth('data_venda')).values('mes').annotate(total=Sum('honorarios')).order_by('mes')
                           
    # Converte Decimals para Floats (para JSON)
    vendas_por_vendedor_payload = [{'vendedor__username': v['vendedor__username'], 'total': float(v['total'] or 0)} for v in vendas_por_vendedor]
    vendas_por_produto_payload = [{'produto__nome': p['produto__nome'], 'total': float(p['total'] or 0)} for p in vendas_por_produto]
    labels_linha = [v['mes'].strftime('%b/%Y') for v in vendas_por_mes]
    data_linha = [float(v['total'] or 0) for v in vendas_por_mes]
    
    # Dados para os Filtros
    todos_vendedores = User.objects.filter(is_superuser=False, is_active=True).order_by('username')
    todos_produtos = Produto.objects.all().order_by('nome')

    context = {
        'perms': perms,
        'kpi_total_vendas': kpis.get('total_vendas') or 0,
        'kpi_ticket_medio': kpis.get('ticket_medio') or 0,
        'kpi_contagem_vendas': kpis.get('contagem_vendas') or 0,
        'kpi_variacao_mes_anterior': kpi_variacao_mes_anterior,
        'vendas_por_vendedor_json': json.dumps(vendas_por_vendedor_payload),
        'vendas_por_produto_json': json.dumps(vendas_por_produto_payload),
        'vendas_por_mes_labels_json': json.dumps(labels_linha),
        'vendas_por_mes_data_json': json.dumps(data_linha),
        'todos_vendedores': todos_vendedores,
        'todos_produtos': todos_produtos,
        'status_venda_choices': Venda.STATUS_VENDA_CHOICES,
        'status_pagamento_choices': Venda.STATUS_PAGAMENTO_CHOICES,
        'status_contrato_choices': Venda.STATUS_CONTRATO_CHOICES,
        'query_data_inicio': request.GET.get('data_inicio', default_start_str), 
        'query_data_fim': request.GET.get('data_fim', default_end_str),
    }
    return render(request, 'dashboard.html', context)

@login_required
def lista_vendas(request):
    """ Aba 2: Lista de Vendas (com filtros e exportação) """
    perms = _get_user_permissions(request.user)
    vendas_filtradas = _get_vendas_filtradas(request)
    
    # Dados para os Filtros
    todos_vendedores = User.objects.filter(is_superuser=False, is_active=True).order_by('username')
    todos_produtos = Produto.objects.all().order_by('nome')
    context = {
        'vendas': vendas_filtradas, 
        'perms': perms,
        'todos_vendedores': todos_vendedores, 
        'todos_produtos': todos_produtos,
        'status_venda_choices': Venda.STATUS_VENDA_CHOICES,
        'status_pagamento_choices': Venda.STATUS_PAGAMENTO_CHOICES,
        'status_contrato_choices': Venda.STATUS_CONTRATO_CHOICES,
    }
    return render(request, 'vendas/lista_vendas.html', context)

@login_required
@transaction.atomic 
def nova_venda(request):
    """ Aba 3: Formulário de Nova Venda """
    if request.method == 'POST':
        venda_form = VendaForm(request.POST)
        anexo_form = AnexoForm(request.POST, request.FILES)
        anexo_form.fields['arquivo'].required = False 
        
        cpf_cnpj = request.POST.get('cpf_cnpj', '').replace(r'\D', '')
        cliente_existente = Cliente.objects.filter(cpf_cnpj=cpf_cnpj).first()
        
        if cliente_existente:
            cliente_form = ClienteForm(request.POST, instance=cliente_existente)
        else:
            cliente_form = ClienteForm(request.POST)
        
        if cliente_form.is_valid() and venda_form.is_valid() and anexo_form.is_valid():
            cliente = cliente_form.save()
            venda = venda_form.save(commit=False)
            venda.cliente = cliente 
            venda.vendedor = request.user
            venda.save() 
            
            ficheiros_enviados = request.FILES.getlist('arquivo') 
            if ficheiros_enviados:
                for f in ficheiros_enviados:
                    AnexoVenda.objects.create(venda=venda, tipo='comprovante', arquivo=f, descricao=f.name)
                if venda.status_pagamento == 'pendente':
                    venda.status_pagamento = 'aguardando_validacao'
                    venda.save()
            return redirect('dashboard')
    
    else: # GET
        venda_form = VendaForm()
        cliente_form = ClienteForm()
        anexo_form = AnexoForm()
        anexo_form.fields['arquivo'].required = False
        anexo_form.fields['arquivo'].label = "Anexar Comprovante(s) (Opcional)"
        
    context = {
        'venda_form': venda_form,
        'cliente_form': cliente_form,
        'anexo_form': anexo_form, 
    }
    return render(request, 'vendas/nova_venda.html', context)

@login_required
@transaction.atomic
def detalhe_venda(request, venda_id):
    """ Página de Detalhes da Venda (Visualização e Edição por permissão) """
    
    perms = _get_user_permissions(request.user)
    
    # 1. Permissão de Acesso
    if perms['is_admin'] or perms['is_gestor'] or perms['is_financeiro'] or perms['is_advogado']:
        venda = get_object_or_404(Venda, id=venda_id)
    else: 
        venda = get_object_or_404(Venda, id=venda_id, vendedor=request.user)
    
    # 2. Definição das Flags de Bloqueio
    is_locked = (venda.status_contrato != 'nao_gerado')
    pagamento_aprovado = (venda.status_pagamento == 'aprovado')
    can_edit_data = (perms['is_admin'] or perms['is_gestor'] or (perms['is_vendedor'] and not is_locked))
    can_delete_comprovante = (perms['is_admin'] or perms['is_gestor'] or (perms['is_financeiro'] and not pagamento_aprovado) or (perms['is_vendedor'] and venda.vendedor == request.user and not pagamento_aprovado))
    can_delete_contrato = (perms['is_admin'] or perms['is_gestor'] or perms['is_advogado'])
    can_delete_nf = (perms['is_admin'] or perms['is_gestor'] or perms['is_financeiro'])

    # 3. Lógica de POST (Submissão dos formulários da página)
    if request.method == 'POST':
        acao = request.POST.get('acao')
        
        # Ação: Upload de Anexo
        if acao in ['add_comprovante', 'add_contrato', 'add_nota_fiscal']:
            tipo_anexo = acao.split('_')[-1]
            ficheiros_enviados = request.FILES.getlist('arquivos')
            pode_enviar = (perms['is_admin'] or perms['is_gestor'] or
                           (perms['is_financeiro'] and tipo_anexo in ['comprovante', 'nota_fiscal']) or
                           (perms['is_advogado'] and tipo_anexo == 'contrato') or
                           (perms['is_vendedor'] and tipo_anexo == 'comprovante'))
            
            if pode_enviar and ficheiros_enviados:
                for f in ficheiros_enviados:
                    AnexoVenda.objects.create(venda=venda, tipo=tipo_anexo, arquivo=f, descricao=f.name)
                if tipo_anexo == 'comprovante' and venda.status_pagamento == 'pendente':
                    venda.status_pagamento = 'aguardando_validacao'
                    venda.save()
                messages.success(request, f"{len(ficheiros_enviados)} ficheiro(s) enviado(s).")
            elif not ficheiros_enviados: messages.error(request, "Nenhum ficheiro selecionado.")
            else: messages.error(request, "Você não tem permissão para enviar este tipo de anexo.")
            return redirect('detalhe_venda', venda_id=venda.id)

        # Ação: Atualizar Status
        elif acao == 'update_status':
            status_pagamento_antigo = venda.status_pagamento 
            form = None
            if perms['is_admin'] or perms['is_gestor']: form = VendaStatusAdminForm(request.POST, instance=venda)
            elif perms['is_financeiro']: form = VendaStatusFinanceiroForm(request.POST, instance=venda)
            elif perms['is_advogado']: form = VendaStatusAdvogadoForm(request.POST, instance=venda)
            elif perms['is_vendedor'] and not is_locked: form = VendaStatusVendedorForm(request.POST, instance=venda)
            
            if form and form.is_valid():
                venda_atualizada = form.save()
                # GATILHO DE COMISSÃO
                if venda_atualizada.status_pagamento == 'aprovado' and status_pagamento_antigo != 'aprovado':
                    _calcular_e_salvar_comissao(venda_atualizada)
                    messages.success(request, "Status atualizado e comissão calculada!")
                else:
                    messages.success(request, "Status da venda atualizado.")
            elif form: messages.error(request, "Erro ao atualizar o status.")
            else: messages.error(request, "Você não tem permissão para esta ação.")
            return redirect('detalhe_venda', venda_id=venda.id)

        # Ação: Atualizar Venda ou Cliente
        elif acao == 'update_venda' or acao == 'update_cliente':
            if can_edit_data:
                if acao == 'update_venda': 
                    form = VendaEditForm(request.POST, instance=venda)
                    msg = "Dados da venda atualizados."
                else: 
                    form = ClienteEditForm(request.POST, instance=venda.cliente)
                    msg = "Dados do cliente atualizados."
                
                if form.is_valid():
                    form.save()
                    # RECÁLCULO DE COMISSÃO
                    if venda.status_pagamento == 'aprovado':
                        _calcular_e_salvar_comissao(venda)
                        msg += " Comissão recalculada."
                    messages.success(request, msg)
                else: messages.error(request, "Erro ao salvar. Verifique os campos.")
            else: messages.error(request, "Você não tem permissão para editar estes dados.")
            return redirect('detalhe_venda', venda_id=venda.id)

    # 4. Lógica GET (Preenche os forms para mostrar na página)
    if perms['is_admin'] or perms['is_gestor']: status_form = VendaStatusAdminForm(instance=venda)
    elif perms['is_financeiro']: status_form = VendaStatusFinanceiroForm(instance=venda)
    elif perms['is_advogado']: status_form = VendaStatusAdvogadoForm(instance=venda)
    else: status_form = VendaStatusVendedorForm(instance=venda)
    venda_form = VendaEditForm(instance=venda)
    cliente_form = ClienteEditForm(instance=venda.cliente)

    context = {
        'venda': venda, 'anexo_form': AnexoForm(), 'status_form': status_form,
        'venda_form': venda_form, 'cliente_form': cliente_form,
        'perms': perms, 'is_locked': is_locked, 'pagamento_aprovado': pagamento_aprovado,
        'can_edit_data': can_edit_data,
        'can_delete_comprovante': can_delete_comprovante,
        'can_delete_contrato': can_delete_contrato,
        'can_delete_nf': can_delete_nf,
    }
    return render(request, 'vendas/detalhe_venda.html', context)

# ---
# SEÇÃO 4: VIEWS DO MÓDULO DE COMISSÕES (Req 4, 6)
# ---

@login_required
def comissoes_dashboard(request):
    """ Aba de 'Gestão de Comissões' (Histórico de Lotes) """
    perms = _get_user_permissions(request.user)
    if not (perms['is_admin'] or perms['is_gestor'] or perms['is_financeiro']):
        messages.error(request, "Você não tem permissão para aceder a esta página.")
        return redirect('dashboard')

    lotes_pagos = LotePagamentoComissao.objects.all().order_by('-data_fechamento')
    
    context = { 'lotes_pagos': lotes_pagos }
    return render(request, 'comissoes/comissoes_dashboard.html', context)

@login_required
@transaction.atomic
def comissoes_fechamento(request):
    """ Página 'Pagar Comissões' (Fecho Manual por Período/Vendedor) """
    perms = _get_user_permissions(request.user)
    if not (perms['is_admin'] or perms['is_gestor'] or perms['is_financeiro']):
        messages.error(request, "Você não tem permissão para aceder a esta página.")
        return redirect('dashboard')
    
    vendas_para_pagar = None
    resumo_por_vendedor = None
    total_geral_comissao = 0
    
    # Busca vendedores que *têm* comissões pendentes (para o filtro)
    vendedores_com_pendencias = User.objects.filter(
        is_superuser=False, is_active=True, 
        vendas__status_pagamento='aprovado', 
        vendas__lote_pagamento__isnull=True
    ).distinct().order_by('username')

    if request.method == 'GET' and 'data_inicio' in request.GET and 'data_fim' in request.GET:
        data_inicio = request.GET.get('data_inicio')
        data_fim = request.GET.get('data_fim')
        query_vendedor = request.GET.get('vendedor', '')
        
        if data_inicio and data_fim: 
            try:
                data_fim_dt = datetime.strptime(data_fim, '%Y-%m-%d').date() + timedelta(days=1)
            except (ValueError, TypeError):
                data_fim_dt = datetime.now().date() + timedelta(days=1)

            vendas_para_pagar = Venda.objects.filter(
                status_pagamento='aprovado',
                lote_pagamento__isnull=True,
                data_venda__gte=data_inicio,
                data_venda__lt=data_fim_dt 
            )
            
            if query_vendedor:
                vendas_para_pagar = vendas_para_pagar.filter(vendedor_id=query_vendedor)
            
            resumo_por_vendedor = vendas_para_pagar.values('vendedor__username') \
                                              .annotate(total_comissao=Sum('comissao_calculada_final'),
                                                        contagem=Count('id')) \
                                              .order_by('vendedor__username')
            total_geral_comissao = resumo_por_vendedor.aggregate(total_geral=Sum('total_comissao'))['total_geral'] or 0

    elif request.method == 'POST':
        data_inicio = request.POST.get('data_inicio')
        data_fim = request.POST.get('data_fim')
        query_vendedor = request.POST.get('vendedor', '')

        try:
            data_fim_dt = datetime.strptime(data_fim, '%Y-%m-%d').date() + timedelta(days=1)
        except (ValueError, TypeError):
            data_fim_dt = datetime.now().date() + timedelta(days=1)

        vendas_para_pagar = Venda.objects.filter(
            status_pagamento='aprovado',
            lote_pagamento__isnull=True,
            data_venda__gte=data_inicio,
            data_venda__lt=data_fim_dt
        )
        
        # Define quais vendedores processar
        vendedores_a_processar_ids = []
        if query_vendedor:
            # Cenário A: Pagar um vendedor específico
            vendedores_a_processar_ids = [query_vendedor]
            vendas_para_pagar = vendas_para_pagar.filter(vendedor_id=query_vendedor)
        else:
            # Cenário B: Pagar todos os vendedores (individuais)
            vendedores_a_processar_ids = vendas_para_pagar.values_list('vendedor_id', flat=True).distinct()

        if not vendas_para_pagar.exists():
            messages.error(request, "Nenhuma venda encontrada para fechar no período selecionado.")
            return redirect('comissoes_fechamento')

        # --- LÓGICA DE MÚLTIPLOS LOTES (Req 1) ---
        lotes_criados_count = 0
        for vendor_id in vendedores_a_processar_ids:
            vendas_do_vendedor = vendas_para_pagar.filter(vendedor_id=vendor_id)
            total_do_vendedor = vendas_do_vendedor.aggregate(total=Sum('comissao_calculada_final'))['total'] or 0
            
            if total_do_vendedor > 0:
                novo_lote = LotePagamentoComissao.objects.create(
                    vendedor_id=vendor_id, 
                    periodo_inicio=data_inicio,
                    periodo_fim=data_fim,
                    responsavel_fechamento=request.user,
                    status='pendente',
                    total_comissoes=total_do_vendedor
                )
                vendas_do_vendedor.update(lote_pagamento=novo_lote)
                lotes_criados_count += 1
        
        if lotes_criados_count > 0:
            messages.success(request, f"{lotes_criados_count} lote(s) de pagamento criado(s) com sucesso.")
            return redirect('comissoes_dashboard')
        else:
            messages.error(request, "Nenhuma comissão a pagar encontrada para os filtros selecionados.")
            return redirect('comissoes_fechamento')

    context = {
        'vendas_para_pagar': vendas_para_pagar,
        'resumo_por_vendedor': resumo_por_vendedor,
        'total_geral_comissao': total_geral_comissao,
        'todos_vendedores': vendedores_com_pendencias, # Passa os vendedores para o filtro
    }
    return render(request, 'comissoes/comissoes_fechamento.html', context)

@login_required
@transaction.atomic
def comissoes_lote_detalhe(request, lote_id):
    """ Página de Detalhe do Lote (ATUALIZADA) """
    perms = _get_user_permissions(request.user)
    if not (perms['is_admin'] or perms['is_gestor'] or perms['is_financeiro']):
        messages.error(request, "Você não tem permissão para aceder a esta página.")
        return redirect('dashboard')
        
    lote = get_object_or_404(LotePagamentoComissao, id=lote_id)
    
    # Prepara os dois formulários
    transacao_form = TransacaoPagamentoForm(lote=lote)
    anexo_lote_form = AnexoLoteForm() # Novo form

    if request.method == 'POST':
        acao = request.POST.get('acao')

        # AÇÃO 1: Adicionar um Pagamento (Transação)
        if acao == 'add_transacao':
            transacao_form = TransacaoPagamentoForm(request.POST, request.FILES, lote=lote)
            if transacao_form.is_valid():
                transacao = transacao_form.save(commit=False)
                transacao.lote = lote
                transacao.responsavel_pagamento = request.user
                if 'anexo_comprovativo_pagamento' in request.FILES:
                    transacao.descricao = request.FILES['anexo_comprovativo_pagamento'].name
                transacao.save() # O gatilho .save() no modelo irá atualizar o Lote
                messages.success(request, "Pagamento registado com sucesso.")
                return redirect('comissoes_lote_detalhe', lote_id=lote.id)
            # Se inválido, a página recarrega com erros no 'transacao_form'
        
        # AÇÃO 2: Adicionar uma Nota Fiscal (Anexo do Lote)
        elif acao == 'add_anexo_nf':
            anexo_lote_form = AnexoLoteForm(request.POST, request.FILES)
            if anexo_lote_form.is_valid():
                anexo = anexo_lote_form.save(commit=False)
                anexo.lote = lote
                if 'anexo_nf_vendedor' in request.FILES:
                    anexo.descricao = request.FILES['anexo_nf_vendedor'].name
                anexo.save()
                messages.success(request, "Nota Fiscal do Vendedor anexada com sucesso.")
                return redirect('comissoes_lote_detalhe', lote_id=lote.id)
            # Se inválido, recarrega com erros no 'anexo_lote_form'

    # Lógica GET
    vendas_no_lote = lote.vendas.all().order_by('data_venda')
    transacoes_do_lote = lote.transacoes_pagamento.all().order_by('data_pagamento')
    anexos_do_lote = lote.anexos_lote.all().order_by('data_upload') # NFs

    context = {
        'lote': lote,
        'vendas_no_lote': vendas_no_lote,
        'transacoes_do_lote': transacoes_do_lote,
        'anexos_do_lote': anexos_do_lote, # Passa as NFs
        'transacao_form': transacao_form, 
        'anexo_lote_form': anexo_lote_form, # Passa o novo form
    }
    return render(request, 'comissoes/comissoes_lote_detalhe.html', context)


# ---
# SEÇÃO 5: APIs INTERNAS (JSON)
# ---

@login_required
def get_produto_data(request, produto_id):
    try:
        produto = Produto.objects.get(id=produto_id)
        data = { 'honorarios': produto.valor, 'valor_entrada': produto.valor_entrada_sugerido,
                 'num_parcelas': produto.num_parcelas_sugerido, 'valor_parcela': produto.valor_parcela_sugerido,
                 'valor_exito': produto.valor_exito_sugerido, 'valor_aporte': produto.valor_aporte_sugerido, }
        return JsonResponse(data)
    except Produto.DoesNotExist: return JsonResponse({'error': 'Produto não encontrado'}, status=404)

@login_required
def check_cliente(request):
    cpf_cnpj = request.GET.get('cpf_cnpj', None)
    if not cpf_cnpj: return JsonResponse({'error': 'CPF/CNPJ não fornecido'}, status=400)
    cliente = Cliente.objects.filter(cpf_cnpj=cpf_cnpj).first()
    if cliente:
        data = { 'status': 'found', 'nome_completo': cliente.nome_completo, 'email': cliente.email, 'telefone': cliente.telefone, 'cep': cliente.cep, 'endereco': cliente.endereco, 'numero': cliente.numero, 'complemento': cliente.complemento, 'bairro': cliente.bairro, 'cidade': cliente.cidade, 'estado': cliente.estado, 'responsavel_nome': cliente.responsavel_nome, 'responsavel_cpf': cliente.responsavel_cpf, 'responsavel_email': cliente.responsavel_email, }
        return JsonResponse(data)
    else: return JsonResponse({'status': 'not_found'})

@login_required
@transaction.atomic
def delete_anexo(request, anexo_id):
    if request.method != 'POST': return HttpResponseForbidden()
    anexo = get_object_or_404(AnexoVenda, id=anexo_id); venda = anexo.venda; perms = _get_user_permissions(request.user); pagamento_aprovado = (venda.status_pagamento == 'aprovado'); pode_excluir = False
    if perms['is_admin'] or perms['is_gestor']:
        pode_excluir = True
    elif perms['is_financeiro']:
        if anexo.tipo == 'nota_fiscal': pode_excluir = True
        elif anexo.tipo == 'comprovante' and not pagamento_aprovado: pode_excluir = True
    elif perms['is_advogado'] and anexo.tipo == 'contrato':
        pode_excluir = True
    elif perms['is_vendedor'] and venda.vendedor == request.user:
        if anexo.tipo == 'comprovante' and not pagamento_aprovado:
            pode_excluir = True
    if pode_excluir:
        anexo.arquivo.delete(save=False); anexo.delete()
        messages.success(request, f"Anexo '{anexo.descricao or anexo.id}' foi excluído com sucesso.")
    else: messages.error(request, "Você não tem permissão para excluir este anexo.")
    return redirect('detalhe_venda', venda_id=venda.id)

# ---
# SEÇÃO 6: VIEWS DE EXPORTAÇÃO (RELATÓRIOS)
# ---

@login_required
def export_vendas_csv(request):
    vendas = _get_vendas_filtradas(request)
    response = HttpResponse(content_type='text/csv'); response['Content-Disposition'] = 'attachment; filename="relatorio_vendas.csv"'
    writer = csv.writer(response, delimiter=';') 
    writer.writerow(['ID Venda', 'Data', 'Vendedor', 'Cliente', 'CPF/CNPJ', 'Produto', 'Honorarios Totais', 'Entrada', 'N Parcelas', 'Valor Parcela', 'Exito', 'Aporte', 'Status Venda', 'Status Pagamento', 'Status Contrato'])
    for venda in vendas: writer.writerow([venda.id, venda.data_venda.strftime('%Y-%m-%d %H:%M'), venda.vendedor.username, venda.cliente.nome_completo, venda.cliente.cpf_cnpj, venda.produto.nome, venda.honorarios, venda.valor_entrada, venda.num_parcelas, venda.valor_parcela, venda.valor_exito, venda.valor_aporte, venda.get_status_venda_display(), venda.get_status_pagamento_display(), venda.get_status_contrato_display()])
    return response

@login_required
def export_vendas_xlsx(request):
    vendas = _get_vendas_filtradas(request)
    wb = openpyxl.Workbook(); ws = wb.active; ws.title = "Relatório de Vendas"
    headers = ['ID Venda', 'Data', 'Vendedor', 'Cliente', 'CPF/CNPJ', 'Produto', 'Honorarios Totais', 'Entrada', 'N Parcelas', 'Valor Parcela', 'Exito', 'Aporte', 'Status Venda', 'Status Pagamento', 'Status Contrato']
    ws.append(headers)
    for venda in vendas: ws.append([venda.id, venda.data_venda.replace(tzinfo=None), venda.vendedor.username, venda.cliente.nome_completo, venda.cliente.cpf_cnpj, venda.produto.nome, float(venda.honorarios or 0), float(venda.valor_entrada or 0), venda.num_parcelas, float(venda.valor_parcela or 0), float(venda.valor_exito or 0), float(venda.valor_aporte or 0), venda.get_status_venda_display(), venda.get_status_pagamento_display(), venda.get_status_contrato_display()])
    for col_num, header in enumerate(headers, 1): ws.column_dimensions[get_column_letter(col_num)].width = 20
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'); response['Content-Disposition'] = 'attachment; filename="relatorio_vendas.xlsx"'
    wb.save(response)
    return response

@login_required
def comissoes_dashboard_graficos(request):
    """ Novo Dashboard Gráfico de Comissões """
    perms = _get_user_permissions(request.user)
    if not (perms['is_admin'] or perms['is_gestor'] or perms['is_financeiro'] or perms['is_vendedor']):
        # Vendedores TAMBÉM podem ver seu próprio dashboard de comissões
        messages.error(request, "Você não tem permissão para aceder a esta página.")
        return redirect('dashboard')

    # 1. Reusa a lógica de filtros base (já lida com permissões de Vendedor vs Outros)
    vendas_filtradas = _get_vendas_filtradas(request)

    # 2. Filtro ADICIONAL: Apenas vendas com pagamento APROVADO geram comissão real
    comissoes_filtradas = vendas_filtradas.filter(status_pagamento='aprovado')

    # 3. Cálculo de KPIs de Comissão
    kpis = comissoes_filtradas.aggregate(
        total_comissoes=Sum('comissao_calculada_final'),
        ticket_medio_comissao=Avg('comissao_calculada_final'),
        contagem_vendas_comissionadas=Count('id')
    )

    # 4. Dados para Gráficos (Adaptado para usar 'comissao_calculada_final')
    # Por Vendedor
    comissoes_por_vendedor = comissoes_filtradas.values('vendedor__username').annotate(total=Sum('comissao_calculada_final')).order_by('-total')
    comissoes_por_vendedor_payload = [{'vendedor__username': c['vendedor__username'], 'total': float(c['total'] or 0)} for c in comissoes_por_vendedor]

    # Por Produto
    comissoes_por_produto = comissoes_filtradas.values('produto__nome').annotate(total=Sum('comissao_calculada_final')).order_by('-total')
    comissoes_por_produto_payload = [{'produto__nome': p['produto__nome'], 'total': float(p['total'] or 0)} for p in comissoes_por_produto]

    # Por Mês (Linha do Tempo)
    comissoes_por_mes = comissoes_filtradas.annotate(mes=TruncMonth('data_venda')).values('mes').annotate(total=Sum('comissao_calculada_final')).order_by('mes')
    labels_linha = [c['mes'].strftime('%b/%Y') for c in comissoes_por_mes]
    data_linha = [float(c['total'] or 0) for c in comissoes_por_mes]

    # 5. Contexto para Filtros (Mesmos do Dashboard de Vendas)
    todos_vendedores = User.objects.filter(is_superuser=False, is_active=True).order_by('username')
    todos_produtos = Produto.objects.all().order_by('nome')

    # Datas padrão para os filtros na tela
    today = datetime.now().date()
    default_start_str = (today - timedelta(days=30)).strftime('%Y-%m-%d')
    default_end_str = today.strftime('%Y-%m-%d')

    context = {
        'perms': perms,
        # KPIs
        'kpi_total_comissoes': kpis.get('total_comissoes') or 0,
        'kpi_media_comissao': kpis.get('ticket_medio_comissao') or 0,
        'kpi_contagem_comissoes': kpis.get('contagem_vendas_comissionadas') or 0,
        # Gráficos JSON
        'comissoes_por_vendedor_json': json.dumps(comissoes_por_vendedor_payload),
        'comissoes_por_produto_json': json.dumps(comissoes_por_produto_payload),
        'comissoes_por_mes_labels_json': json.dumps(labels_linha),
        'comissoes_por_mes_data_json': json.dumps(data_linha),
        # Filtros
        'todos_vendedores': todos_vendedores,
        'todos_produtos': todos_produtos,
        'query_data_inicio': request.GET.get('data_inicio', default_start_str),
        'query_data_fim': request.GET.get('data_fim', default_end_str),
    }
    return render(request, 'comissoes/dashboard_graficos.html', context)

@login_required
def comissoes_historico_lotes(request):
    """ Histórico de Lotes com Filtros """
    perms = _get_user_permissions(request.user)
    if not (perms['is_admin'] or perms['is_gestor'] or perms['is_financeiro'] or perms['is_vendedor']):
         messages.error(request, "Você não tem permissão para aceder a esta página.")
         return redirect('dashboard')

    # 1. Queryset Base (respeitando permissões)
    if perms['is_vendedor'] and not (perms['is_admin'] or perms['is_gestor'] or perms['is_financeiro']):
        lotes_pagos = LotePagamentoComissao.objects.filter(vendedor=request.user)
    else:
        lotes_pagos = LotePagamentoComissao.objects.all()

    # 2. Captura dos Parâmetros de Filtro
    query_vendedor = request.GET.get('vendedor', '')
    query_status = request.GET.get('status', '')
    query_data_inicio = request.GET.get('data_inicio', '')
    query_data_fim = request.GET.get('data_fim', '')

    # 3. Aplicação dos Filtros
    # Filtro de Vendedor (só aplica se o usuário tiver permissão para ver todos)
    if (perms['is_admin'] or perms['is_gestor'] or perms['is_financeiro']) and query_vendedor:
        lotes_pagos = lotes_pagos.filter(vendedor_id=query_vendedor)

    # Filtro de Status
    if query_status:
        lotes_pagos = lotes_pagos.filter(status=query_status)

    # Filtro de Data (pela data de fechamento do lote)
    if query_data_inicio:
        lotes_pagos = lotes_pagos.filter(data_fechamento__gte=query_data_inicio)
    if query_data_fim:
        try:
            # Ajuste para incluir o dia final inteiro
            data_fim_dt = datetime.strptime(query_data_fim, '%Y-%m-%d').date() + timedelta(days=1)
            lotes_pagos = lotes_pagos.filter(data_fechamento__lt=data_fim_dt)
        except (ValueError, TypeError):
            pass

    # 4. Ordenação final
    lotes_pagos = lotes_pagos.order_by('-data_fechamento')

    # 5. Contexto para os Dropdowns
    todos_vendedores = User.objects.filter(is_superuser=False, is_active=True).order_by('username')

    context = {
        'lotes_pagos': lotes_pagos,
        'perms': perms,
        'todos_vendedores': todos_vendedores,
        'status_lote_choices': LotePagamentoComissao.STATUS_CHOICES, # Passamos as opções do model
        # Preserva os valores dos filtros no template
        'query_vendedor': query_vendedor,
        'query_status': query_status,
        'query_data_inicio': query_data_inicio,
        'query_data_fim': query_data_fim,
    }
    return render(request, 'comissoes/historico_lotes.html', context)