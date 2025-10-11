import requests
from django.http import JsonResponse
from . import data_service  # Serviço de dados
from django.views.decorators.http import require_GET

@require_GET
def get_ficha_api(request, product_slug, city_id):
    """
    API que retorna a ficha técnica de um produto para uma cidade.
    Usa o data_service para buscar dados e API do IBGE.
    """
    # 1. Obter nome da cidade pelo ID IBGE
    city_name, error = data_service.get_city_name_for_id(city_id)
    if error:
        return JsonResponse({'error': error}, status=500)
    if not city_name:
        return JsonResponse({'error': f'Cidade com ID {city_id} não encontrada.'}, status=404)

    # 2. Normaliza nomes
    normalized_product_name = data_service.normalize_text(product_slug)
    normalized_city_name = data_service.normalize_text(city_name)

    # 3. Gerar ficha técnica
    ficha = data_service.generate_product_sheet(normalized_product_name, normalized_city_name)

    if 'error' in ficha:
        return JsonResponse(ficha, status=500)

    return JsonResponse(ficha)
