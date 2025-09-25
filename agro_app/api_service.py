import requests

# Sua chave de API do OpenWeatherMap
API_KEY = "1651adf768bfe011596a30a1801c57f6"

# Endereço da API para dados de clima em tempo real
BASE_URL = "http://api.openweathermap.org/data/2.5/weather"

def get_weather_data(city_name):
    """
    Busca dados de clima para uma cidade específica.

    Args:
        city_name (str): O nome da cidade (ex: "Bauru, br").

    Returns:
        dict: Um dicionário com os dados de clima, ou None em caso de erro.
    """
    params = {
        'q': city_name,
        'appid': API_KEY,
        'units': 'metric',  # Para receber a temperatura em Celsius
        'lang': 'pt_br'     # Para receber a descrição em português
    }

    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status() # Lança um erro se a requisição falhar
        data = response.json()
        return data

    except requests.exceptions.RequestException as e:
        print(f"Erro ao conectar com a API: {e}")
        return None
    except Exception as e:
        print(f"Ocorreu um erro ao processar os dados: {e}")
        return None
