from django.http import JsonResponse
from fichatecnica_app.data_service import get_weather_data


def weather_api_endpoint(request):
    """
    Endpoint da API local para retornar dados de clima em JSON.
    Chama a função de serviço centralizada em data_service.py.
    """
    # Tenta pegar o nome da cidade do parâmetro de URL (Ex: /clima/?city=Bauru)
    city_name = request.GET.get('city')

    if not city_name:
        return JsonResponse({'error': 'Parâmetro "city" faltando. Use: ?city=NomeDaCidade'}, status=400)

    # 1. Chama a função de serviço centralizada (agora funcionando)
    clima_data = get_weather_data(city_name)

    # 2. Retorna a resposta JSON
    if clima_data:
        # Se os dados vierem, retorna 200 OK com os dados
        return JsonResponse(clima_data)
    else:
        # Se a função retornar None (falha na API ou cidade não encontrada)
        return JsonResponse({'error': f'Dados de clima indisponíveis para {city_name}. Verifique o nome da cidade.'},
                            status=500)