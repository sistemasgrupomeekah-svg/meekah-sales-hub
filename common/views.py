from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Produto, Cliente

@login_required
def get_produto_data(request, produto_id):
    """ API que retorna os dados de um produto para o JS """
    try:
        produto = Produto.objects.get(id=produto_id)
        data = { 
            'honorarios': produto.valor, 
            'valor_entrada': produto.valor_entrada_sugerido,
            'num_parcelas': produto.num_parcelas_sugerido, 
            'valor_parcela': produto.valor_parcela_sugerido,
            'valor_exito': produto.valor_exito_sugerido, 
            'valor_aporte': produto.valor_aporte_sugerido, 
        }
        return JsonResponse(data)
    except Produto.DoesNotExist: 
        return JsonResponse({'error': 'Produto não encontrado'}, status=404)

@login_required
def check_cliente(request):
    """ API que verifica se um Cliente (por CPF/CNPJ) já existe """
    cpf_cnpj = request.GET.get('cpf_cnpj', None)
    if not cpf_cnpj: 
        return JsonResponse({'error': 'CPF/CNPJ não fornecido'}, status=400)
    
    cliente = Cliente.objects.filter(cpf_cnpj=cpf_cnpj).first()
    
    if cliente:
        data = { 
            'status': 'found', 
            'nome_completo': cliente.nome_completo, 
            'email': cliente.email, 
            'telefone': cliente.telefone, 
            'cep': cliente.cep, 
            'endereco': cliente.endereco, 
            'numero': cliente.numero, 
            'complemento': cliente.complemento, 
            'bairro': cliente.bairro, 
            'cidade': cliente.cidade, 
            'estado': cliente.estado, 
            'responsavel_nome': cliente.responsavel_nome, 
            'responsavel_cpf': cliente.responsavel_cpf, 
            'responsavel_email': cliente.responsavel_email, 
        }
        return JsonResponse(data)
    else: 
        return JsonResponse({'status': 'not_found'})