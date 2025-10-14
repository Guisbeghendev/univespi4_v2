import requests
import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from urllib.parse import unquote
# Importa o serviço que acessa os dados da Ficha Técnica
from fichatecnica_app import data_service

# ------------------------------------------------------------------------------------------------------
# FUNÇÕES LOCAIS PARA ACESSO À API DO IBGE
# ------------------------------------------------------------------------------------------------------

def get_all_states_from_ibge():
    """
    Busca e retorna a lista de estados (UF) do Brasil (IBGE).
    Retorna uma lista de dicionários no formato: [{'id': id, 'nome': nome}, ...]
    """
    try:
        url = "https://servicodados.ibge.gov.br/api/v1/localidades/estados?orderBy=nome"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        states_data = response.json()
        return [{'id': state['id'], 'nome': state['nome']} for state in states_data]
    except requests.RequestException as e:
        print(f"ERRO DE CONEXÃO IBGE (Estados): {e}")
        return []

def get_cities_by_state(state_id):
    """
    Busca e retorna a lista de municípios de um estado específico (IBGE).
    Retorna uma lista de dicionários no formato: [{'id': id, 'nome': nome}, ...]
    """
    if not state_id:
        return []
    try:
        url = f"https://servicodados.ibge.gov.br/api/v1/localidades/estados/{state_id}/municipios?orderBy=nome"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        cities_data = response.json()
        return [{'id': city['id'], 'nome': city['nome']} for city in cities_data]
    except requests.RequestException as e:
        print(f"ERRO DE CONEXÃO IBGE (Cidades): {e}")
        return []

# ------------------------------------------------------------------------------------------------------
# 1. VIEW PRINCIPAL DE CONSULTA (Renderiza a página com os filtros)
# ------------------------------------------------------------------------------------------------------
@login_required
def info_consulta(request):
    """
    Renderiza a página de consulta e pesquisa da Ficha Técnica (Bloco 3).
    Esta view apenas carrega o template; toda a lógica de filtragem e busca é feita via AJAX.
    """
    context = {
        'titulo_pagina': 'Consulta de Dados Agropecuários',
    }
    return render(request, 'info_app/info_consulta.html', context)


# ------------------------------------------------------------------------------------------------------
# 2. VIEWS DE API PARA O FILTRO HIERÁRQUICO (Localidades)
# ------------------------------------------------------------------------------------------------------

@require_http_methods(["GET"])
def get_all_states(request):
    """
    API: Retorna a lista de todos os estados (UF) do Brasil, obtida do IBGE.
    """
    try:
        # Chama a função de serviço que busca os dados no IBGE (Função Local)
        states_list = get_all_states_from_ibge()

        # CORREÇÃO ANTERIOR (OK): Retorna o array diretamente, conforme esperado pelo JavaScript.
        return JsonResponse(states_list, safe=False, status=200)

    except Exception as e:
        print(f"Erro ao processar a requisição de estados: {e}")
        return JsonResponse({'error': 'Falha ao buscar a lista de estados.', 'details': str(e)}, status=500)


@require_http_methods(["GET"])
def get_cities_for_state(request, state_id):
    """
    API: Retorna a lista de cidades de um estado específico (ID do IBGE).
    """
    try:
        if not state_id:
            return JsonResponse({'error': 'ID do estado não fornecido.'}, status=400)

        # Chama a função de serviço que busca as cidades no IBGE (Função Local)
        cities_list = get_cities_by_state(state_id)

        # CORREÇÃO AGORA: O JavaScript espera o array de cidades (cities_list) diretamente,
        # sem ser encapsulado em um dicionário com a chave 'cities', devido à implementação do .json()
        # no seu bloco3.js e a correção feita em get_all_states.
        return JsonResponse(cities_list, safe=False, status=200)

    except Exception as e:
        print(f"Erro ao processar a requisição de cidades para o estado {state_id}: {e}")
        return JsonResponse({'error': 'Falha ao buscar a lista de cidades.', 'details': str(e)}, status=500)


# ------------------------------------------------------------------------------------------------------
# 3. VIEWS DE API PARA O AJAX DO FILTRO HIERÁRQUICO (Produtos e Dados)
# ------------------------------------------------------------------------------------------------------

def get_products_for_filter(request, city_id):
    """
    API: Retorna a lista de produtos (Ficha Técnica) para uma cidade específica via AJAX.
    """
    if not city_id:
        # Retorna lista vazia se não houver ID de cidade
        return JsonResponse([], safe=False)

    try:
        # Chama o serviço de dados (fichatecnica_app) para buscar os produtos disponíveis na cidade.
        products_data = data_service.get_products_for_city(city_id)

        # O serviço de dados deve retornar uma lista de dicionários no formato:
        # [{'id': id, 'nome': nome}, ...]
        return JsonResponse(products_data, safe=False)
    except Exception as e:
        print(f"ERRO info_app/views.py [get_products_for_filter]: {e}")
        return JsonResponse({'error': 'Erro ao buscar produtos no serviço de dados'}, status=500)


def get_ficha_tecnica_data(request, product_name, city_id):
    """
    API: Retorna os dados completos da Ficha Técnica (o resultado final da pesquisa)
    para um produto (pelo NOME) e cidade específicos. Esta API deve retornar o conjunto COMPLETO de dados.
    """
    if not product_name or not city_id:
        return JsonResponse({'error': 'Faltam parâmetros de produto ou cidade'}, status=400)

    try:
        # CORREÇÃO CRÍTICA: Decodifica o nome do produto da URL.
        # Ex: "Maca%20Verde" deve virar "Maca Verde".
        clean_product_name = unquote(product_name)

        # Chama o serviço de dados para buscar a ficha completa, usando o nome decodificado.
        ficha_data = data_service.get_ficha_tecnica(clean_product_name, city_id)

        if ficha_data:
            # Retorna o dicionário com todos os dados da Ficha Técnica.
            return JsonResponse(ficha_data, safe=False)
        else:
            return JsonResponse({'message': 'Dados não encontrados para a combinação.'}, status=404)
    except Exception as e:
        print(f"ERRO info_app/views.py [get_ficha_tecnica_data]: {e}")
        return JsonResponse({'error': 'Erro ao acessar o serviço de ficha técnica'}, status=500)