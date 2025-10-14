from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib import messages
# Importa Terreno, PlanoPlantio, e Produto (necessário para api_salvar_etapa1)
from agro_app.models import Terreno, PlanoPlantio, Produto 
# Importa as funções do serviço de dados
from fichatecnica_app.data_service import get_products_for_city, get_ficha_tecnica
from django.db import IntegrityError
import json
from datetime import date
from decimal import Decimal

# >>>>>>>>>>>>>>>>>> CORREÇÃO CRÍTICA: IMPORTAÇÃO DA LÓGICA DE TRADUÇÃO <<<<<<<<<<<<<<<<<<
# ESTA LINHA É CRÍTICA para que as funções de tradução sejam acessíveis
from agro_app.views import get_city_name_from_id, get_state_name_from_id


# --- API DE TERRENOS ---

@login_required
@require_http_methods(["GET"])
def api_terrenos(request):
    """
    API endpoint que retorna a lista de Terrenos do usuário,
    com os campos de Localização traduzidos (sem IDs IBGE).
    """
    try:
        user_terrenos = Terreno.objects.filter(proprietario=request.user).order_by('nome')

        terrenos_list = []
        for terreno in user_terrenos:
            # 1. TRADUZ OS IDs PARA NOMES LEGÍVEIS
            cidade_nome = get_city_name_from_id(terreno.cidade)
            estado_sigla = get_state_name_from_id(terreno.estado)

            terrenos_list.append({
                'id': terreno.id,
                'nome': terreno.nome,
                # Garante que Decimal seja serializável
                'area_total': str(terreno.area_total),
                'unidade_area': terreno.unidade_area,

                # Campos de ID (para o JS usar nas API's futuras, se necessário)
                'cidade_id': terreno.cidade,
                'estado_id': terreno.estado,

                # Campos para Exibição no JS (sem os códigos do IBGE)
                'cidade_nome': cidade_nome or 'N/A',
                'estado_sigla': estado_sigla or 'N/A',
                # CHAVE CRÍTICA: O JavaScript (bloco7.js) ESPERA ESTE NOME.
                'localizacao_display': f"{cidade_nome or 'N/A'} / {estado_sigla or 'N/A'}"
            })

        return JsonResponse({'terrenos': terrenos_list}, status=200)

    except Exception as e:
        return JsonResponse({'error': f'Erro interno ao listar terrenos: {str(e)}'}, status=500)


# --- WIZARD DE PLANO DE PLANTIO - PONTO DE INÍCIO (CORRIGIDO PARA GET) ---

@login_required
@require_http_methods(["GET"])
def iniciar_wizard(request):
    """
    Inicia um novo Plano de Plantio, associando-o ao Terreno selecionado,
    recebendo o ID via Query Parameter (GET). Cria um RASCUNHO e redireciona para a Etapa 1.
    """
    try:
        terreno_id = request.GET.get('terreno_id')

        if not terreno_id:
            messages.error(request, "Nenhum terreno selecionado para iniciar o plano.")
            return redirect('core:dashboard')

        terreno_selecionado = get_object_or_404(
            Terreno,
            pk=terreno_id,
            proprietario=request.user
        )

        # Cria um novo Plano de Plantio (RASCUNHO)
        novo_plano = PlanoPlantio.objects.create(
            proprietario=request.user,
            terreno=terreno_selecionado,
            nome=f"Plano em Rascunho para {terreno_selecionado.nome} ({date.today().strftime('%Y-%m')})",
            data_inicio=date.today(),
            status='RASCUNHO'
        )

        # Redireciona para a Etapa 1
        messages.success(request, f"Plano '{novo_plano.nome}' iniciado. Comece pela Etapa 1.")
        return redirect(reverse('plano:etapa1_plano', kwargs={'plano_id': novo_plano.pk}))

    except Terreno.DoesNotExist:
        messages.error(request, "Terreno inválido ou não encontrado.")
        return redirect('core:dashboard')
    except Exception as e:
        messages.error(request, f'Erro interno ao iniciar o Plano: {str(e)}')
        return redirect('core:dashboard')


# ----------------------------------------------------------------------
# VIEWS NOVAS PARA A ETAPA 1 DO WIZARD
# ----------------------------------------------------------------------

@login_required
@require_http_methods(["GET"])
def etapa1_plano(request, plano_id):
    """
    Renderiza a primeira (e única) etapa do Plano: Seleção de Produto e Datas.
    """
    # 1. Busca o Plano (Rascunho) e verifica a posse
    plano = get_object_or_404(
        PlanoPlantio,
        pk=plano_id,
        proprietario=request.user
    )

    # 2. Busca a lista de produtos disponíveis para a cidade do Terreno
    # O ID da cidade é o que será passado para o data_service
    cidade_ibge_id = plano.terreno.cidade
    produtos_disponiveis = get_products_for_city(cidade_ibge_id)

    context = {
        'plano': plano,
        'terreno': plano.terreno,
        'produtos_disponiveis': produtos_disponiveis,
        # Adiciona o ID da cidade ao contexto, para o JS poder usá-lo nas chamadas API
        'cidade_ibge_id': cidade_ibge_id,
        'app_name': 'plano'  # Útil para referenciar URLs no template
    }

    # Renderiza o template 'planoplantio.html'
    return render(request, 'planoplantio_app/planoplantio.html', context)
    # A ÚLTIMA VERSÃO DE ETAPA1_PLANO.HTML FOI RENOMEADA PARA planoplantio.html


@login_required
@require_http_methods(["GET"])
def api_buscar_ficha(request):
    """
    API para buscar os dados da Ficha Técnica (data_service) para um produto/terreno.
    Esperado: ?produto_nome=<nome>&cidade_id=<ibge_id>
    """
    produto_nome = request.GET.get('produto_nome')
    cidade_id = request.GET.get('cidade_id')

    if not produto_nome or not cidade_id:
        return JsonResponse({'error': 'Parâmetros produto_nome e cidade_id são obrigatórios.'}, status=400)

    # 1. Busca os dados da ficha técnica
    ficha_data = get_ficha_tecnica(produto_nome, cidade_id)

    if ficha_data is None:
        return JsonResponse({'error': 'Ficha Técnica não encontrada para o produto/cidade ou erro interno.'},
                            status=404)

    # 2. CORREÇÃO DE SERIALIZAÇÃO: Converte qualquer Decimal para string, garantindo JSON válido
    def convert_decimal(obj):
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, dict):
            return {k: convert_decimal(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [convert_decimal(i) for i in obj]
        return obj

    ficha_data = convert_decimal(ficha_data)

    return JsonResponse(ficha_data, status=200)


@login_required
@require_http_methods(["POST"])
def api_salvar_etapa1(request, plano_id):
    """
    API para salvar a Etapa 1 (Seleção de Produto e Datas) no PlanoPlantio.
    """
    plano = get_object_or_404(
        PlanoPlantio,
        pk=plano_id,
        proprietario=request.user
    )

    try:
        data = json.loads(request.body)
        produto_nome = data.get('produto_nome')
        data_inicio = data.get('data_inicio')
        data_colheita_prevista = data.get('data_colheita_prevista')

        if not produto_nome or not data_inicio:
            return JsonResponse({'error': 'Produto e Data de Início são obrigatórios.'}, status=400)

        # 1. Busca o objeto Produto (do banco de dados) a partir do nome
        # O nome normalizado precisa ser mapeado de volta para o objeto Produto
        try:
            # Usa '__iexact' para busca case-insensitive
            produto_obj = Produto.objects.get(nome__iexact=produto_nome)
        except Produto.DoesNotExist:
            return JsonResponse({'error': f"Produto '{produto_nome}' não encontrado no banco de dados."}, status=400)

        # 2. Atualiza o Plano
        plano.produto = produto_obj
        plano.data_inicio = data_inicio
        plano.data_colheita_prevista = data_colheita_prevista if data_colheita_prevista else None
        plano.status = 'ANDAMENTO'  # Define como Andamento após a primeira etapa

        plano.save()

        return JsonResponse({
            'message': 'Etapa 1 salva com sucesso.',
            'plano_id': plano.pk,
            # CORRIGIDO: Redireciona para o dashboard, eliminando a chamada à rota inexistente 'plano:etapa2_plano'.
            'next_url': reverse('core:dashboard')
        }, status=200)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Payload JSON inválido.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Erro ao salvar Etapa 1: {str(e)}'}, status=500)
