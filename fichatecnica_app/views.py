import requests
from django.http import JsonResponse
from . import data_service  # Importa o serviço de dados
from django.views.decorators.http import require_http_methods


def get_ficha_api(request, product_slug, city_id):
    """
    API que retorna a Ficha Técnica consolidada de um produto para uma cidade.
    Usa o serviço de dados (data_service) e consulta a API do IBGE.
    """
    if not product_slug:
        return JsonResponse({"error": "O slug do produto é obrigatório."}, status=400)

    # 1. Busca o nome da cidade no IBGE
    city_name = None
    try:
        # Usando a API IBGE, conforme definido no projeto AgroData
        city_url = f"https://servicodados.ibge.gov.br/api/v1/localidades/municipios/{city_id}"
        city_response = requests.get(city_url, timeout=10)
        city_response.raise_for_status() # Lança exceção para 4xx/5xx erros
        city_data = city_response.json()
        city_name = city_data.get('nome', None)

        if not city_name:
            return JsonResponse({"error": f"Cidade com ID {city_id} não encontrada no IBGE."}, status=404)

    except requests.exceptions.Timeout:
        return JsonResponse({"error": "Tempo limite excedido ao consultar o IBGE."}, status=504)
    except requests.exceptions.RequestException as e:
        return JsonResponse({"error": f"Erro de conexão ao buscar dados da cidade no IBGE: {e}"}, status=500)
    except Exception as e:
        return JsonResponse({"error": f"Erro inesperado na busca de cidade: {str(e)}"}, status=500)

    # 2. Prepara os nomes normalizados
    normalized_product_name = data_service.normalize_text(product_slug)
    normalized_city_name = data_service.normalize_text(city_name)

    # 3. Gera a ficha técnica usando o serviço de dados corrigido
    ficha = data_service.generate_product_sheet(normalized_product_name, normalized_city_name)

    # 4. Retorna a ficha
    if "error" in ficha:
        return JsonResponse(ficha, status=500)

    return JsonResponse(ficha)