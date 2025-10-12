import requests
from django.http import JsonResponse
from . import data_service  # Serviço de dados
from django.views.decorators.http import require_GET


@require_GET
def get_ficha_api(request, product_slug, city_id):
    """
    API que retorna a ficha técnica completa de um produto para uma cidade.

    A função data_service.get_ficha_tecnica busca e consolida todos os
    dados (CSV, 4 JSONs, e Clima) em uma única estrutura, incluindo os
    campos brutos (raw data) de todos os JSONs, conforme solicitado.
    """

    # 1. Chamar a função principal de serviço que faz todo o trabalho de
    # normalização, busca IBGE, busca CSV/JSON e busca de Clima.
    # product_slug (nome não normalizado) e city_id são passados diretamente.
    ficha_completa = data_service.get_ficha_tecnica(product_slug, city_id)

    if not ficha_completa:
        # Se retornar None, houve uma falha crítica na busca de dados ou na consolidação.
        return JsonResponse(
            {
                'error': f'Não foi possível gerar a ficha técnica completa para o produto "{product_slug}" na cidade com ID "{city_id}". Verifique se os dados estão disponíveis.'},
            status=404
        )

    # 2. Retorna o resultado completo, que inclui todos os campos formatados (16 campos)
    # e os novos blocos com os dados brutos (raw) dos 4 JSONs.
    return JsonResponse(ficha_completa)
