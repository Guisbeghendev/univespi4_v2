import requests
import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
# Importa o serviço que acessa os dados da Ficha Técnica
from fichatecnica_app import data_service


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
    # O template a ser criado na próxima etapa
    return render(request, 'info_app/info_consulta.html', context)


# ------------------------------------------------------------------------------------------------------
# 2. VIEWS DE API PARA O AJAX DO FILTRO HIERÁRQUICO
#    (Estas APIs são usadas pelo JavaScript para popular os selects no Bloco 3)
# ------------------------------------------------------------------------------------------------------

def get_products_for_filter(request, city_id):
    """
    API: Retorna a lista de produtos (Ficha Técnica) para uma cidade específica via AJAX.
    Esta lógica é duplicada intencionalmente no agro_app/views.py (para o perfil) e
    aqui, para manter a modularidade do 'info_app' para as consultas sem compromisso.
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

    CORREÇÃO: O argumento 'product_id' foi renomeado para 'product_name'
    para corresponder à rota definida em urls.py.
    """
    if not product_name or not city_id:
        return JsonResponse({'error': 'Faltam parâmetros de produto ou cidade'}, status=400)

    try:
        # Chama o serviço de dados para buscar a ficha completa.
        # Passando o product_name (string) em vez de product_id (int).
        ficha_data = data_service.get_ficha_tecnica(product_name, city_id)

        if ficha_data:
            # Retorna o dicionário com todos os dados da Ficha Técnica.
            return JsonResponse(ficha_data, safe=False)
        else:
            return JsonResponse({'message': 'Dados não encontrados para a combinação.'}, status=404)
    except Exception as e:
        print(f"ERRO info_app/views.py [get_ficha_tecnica_data]: {e}")
        return JsonResponse({'error': 'Erro ao acessar o serviço de ficha técnica'}, status=500)
