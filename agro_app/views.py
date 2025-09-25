import requests
import json
import os
import pandas as pd
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from .models import Profile
from .forms import ProfileForm
from .api_service import get_weather_data
import unicodedata
import re
from django.db import IntegrityError

# Dicionário global para armazenar os DataFrames, evitando o carregamento a cada requisição.
# A chave será o nome simplificado do arquivo.
AGRO_DATA_CACHE = {}


# Função para normalizar o texto (remover acentos, converter para maiúsculas e remover sigla do estado)
def normalize_text(text):
    if not isinstance(text, str):
        return ""
    # Remove a sigla do estado (ex: " (RO)")
    text = re.sub(r'\s*\([^)]*\)', '', text)
    # Remove acentos e caracteres especiais
    normalized = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
    return normalized.upper().strip()


# Função de carregamento dos arquivos CSV
def get_agro_data():
    global AGRO_DATA_CACHE
    if AGRO_DATA_CACHE:
        return AGRO_DATA_CACHE, "Sucesso"

    file_names = {
        'Quantidade produzida': 'Quantidade produzida (Toneladas).csv',
        'Rendimento médio': 'Rendimento médio da produção (Quilogramas por Hectare).csv',
        'Valor da produção': 'Valor da produção (Reais).csv',
        'Área colhida': 'Área colhida (Hectares).csv',
        'Área destinada': 'Área destinada à colheita.csv'
    }

    try:
        dados_dir = os.path.join(settings.BASE_DIR, 'agro_app', 'dados')

        data_frames = {}
        for key, file_name in file_names.items():
            caminho_arquivo = os.path.join(dados_dir, file_name)
            if not os.path.exists(caminho_arquivo):
                return None, f"Arquivo '{file_name}' não encontrado."

            try:
                df = pd.read_csv(caminho_arquivo, sep=';', encoding='utf-8', skiprows=5)
                product_names_header = pd.read_csv(caminho_arquivo, sep=';', encoding='utf-8', skiprows=4,
                                                   nrows=1).columns.tolist()
            except UnicodeDecodeError:
                df = pd.read_csv(caminho_arquivo, sep=';', encoding='latin1', skiprows=5)
                product_names_header = pd.read_csv(caminho_arquivo, sep=';', encoding='latin1', skiprows=4,
                                                   nrows=1).columns.tolist()

            municipio_col = df.columns[0]

            if not municipio_col:
                return None, f"Coluna de município não encontrada em '{file_name}'."

            column_map = {}
            for i, normalized_col in enumerate(df.columns):
                if i < len(product_names_header):
                    original_name = product_names_header[i]
                    column_map[normalized_col] = original_name

            data_frames[f'{key}_header_map'] = column_map

            df = df.rename(columns={municipio_col: 'CIDADE'})
            df['CIDADE'] = df['CIDADE'].apply(normalize_text)

            df.columns = [normalize_text(col) for col in df.columns]

            data_frames[key] = df
            print(f"DEBUG: Colunas do arquivo '{file_name}' após processamento: {df.columns.tolist()}")

        AGRO_DATA_CACHE = data_frames
        return AGRO_DATA_CACHE, "Sucesso"

    except FileNotFoundError:
        return None, "Erro: Um ou mais arquivos não foram encontrados."
    except Exception as e:
        return None, f"Ocorreu um erro: {str(e)}"


# Funções de autenticação e view
def home(request):
    return render(request, 'home.html')


def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                login(request, user)
                return redirect('agro_app:dashboard')
            except IntegrityError:
                form.add_error('username', "Nome de usuário já existe.")
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('agro_app:dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('agro_app:home')


@login_required
def dashboard(request):
    user_profile, created = Profile.objects.get_or_create(user=request.user)

    # Obtém o nome do estado a partir do ID
    state_name = user_profile.state
    if user_profile.state and user_profile.state.isdigit():
        try:
            url = f"https://servicodados.ibge.gov.br/api/v1/localidades/estados/{user_profile.state}"
            response = requests.get(url)
            state_data = response.json()
            if isinstance(state_data, dict):
                state_name = state_data.get('nome', user_profile.state)
            else:
                state_name = user_profile.state
        except requests.exceptions.RequestException:
            state_name = user_profile.state

    # Obtém o nome da cidade a partir do ID para exibir nos cards
    city_name = user_profile.city
    if user_profile.city and user_profile.city.isdigit():
        try:
            url = f"https://servicodados.ibge.gov.br/api/v1/localidades/municipios/{user_profile.city}"
            response = requests.get(url)
            city_data = response.json()
            city_name = city_data.get('nome', user_profile.city)
        except requests.exceptions.RequestException:
            city_name = user_profile.city

    weather_data = None
    # Passa o nome da cidade para a função get_weather_data
    if city_name and not city_name.isdigit():  # Garante que só envia o nome da cidade para a API
        weather_data = get_weather_data(city_name)

    context = {
        'profile': user_profile,
        'state_name': state_name,
        'city_name': city_name,  # Adiciona o nome da cidade ao contexto
        'weather_data': weather_data
    }
    return render(request, 'dashboard.html', context)


@login_required
def profile(request):
    user_profile, created = Profile.objects.get_or_create(user=request.user)

    # Adicionando o nome do estado
    state_name = user_profile.state
    if user_profile.state and user_profile.state.isdigit():
        try:
            url = f"https://servicodados.ibge.gov.br/api/v1/localidades/estados/{user_profile.state}"
            response = requests.get(url)
            state_data = response.json()
            if isinstance(state_data, dict):
                state_name = state_data.get('nome', user_profile.state)
            else:
                state_name = user_profile.state
        except requests.exceptions.RequestException:
            state_name = user_profile.state

    # Adicionando o nome da cidade a partir do ID
    city_name = None
    if user_profile.city:
        try:
            city_url = f"https://servicodados.ibge.gov.br/api/v1/localidades/municipios/{user_profile.city}"
            city_response = requests.get(city_url)
            city_data = city_response.json()
            city_name = city_data.get('nome', user_profile.city)
        except requests.exceptions.RequestException:
            city_name = user_profile.city

    # Adicionando o nome do cultivo a partir do ID
    cultivo_principal_name = None
    if user_profile.cultivo_principal:
        agro_data, status = get_agro_data()
        if agro_data:
            # Assumindo que o mapa de produtos está na chave 'Quantidade produzida_header_map'
            product_map = agro_data.get('Quantidade produzida_header_map', {})
            # Buscando o nome original do cultivo pelo ID (chave normalizada)
            original_name = product_map.get(user_profile.cultivo_principal)
            cultivo_principal_name = original_name if original_name else user_profile.cultivo_principal

    context = {
        'profile': user_profile,
        'state_name': state_name,
        'city_name': city_name,  # Adicionando o nome da cidade ao contexto
        'cultivo_principal_name': cultivo_principal_name,  # Adicionando o nome do cultivo ao contexto
    }
    return render(request, 'profile.html', context)


@login_required
def profile_edit(request):
    user_profile, created = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=user_profile)
        if form.is_valid():
            form.save()
            return redirect('agro_app:profile')
    else:
        form = ProfileForm(instance=user_profile)
    context = {
        'form': form,
    }
    return render(request, 'profile_edit.html', context)


def get_states(request):
    url = "https://servicodados.ibge.gov.br/api/v1/localidades/estados"
    response = requests.get(url)
    states = response.json()
    states_list = [{'id': state['id'], 'nome': state['nome'], 'sigla': state['sigla']} for state in states]
    return JsonResponse(states_list, safe=False)


def get_cities(request, state_id):
    url = f"https://servicodados.ibge.gov.br/api/v1/localidades/estados/{state_id}/municipios"
    response = requests.get(url)
    cities = response.json()
    cities_list = [{'id': city['id'], 'nome': city['nome']} for city in cities]
    return JsonResponse(cities_list, safe=False)


def get_products_by_city(request, city_name):
    print("Nome da cidade recebido:", city_name)

    data_frames, status = get_agro_data()

    if data_frames is None:
        return JsonResponse({"error": status}, status=500)

    normalized_city_name = normalize_text(city_name)
    print("Nome da cidade normalizado (IBGE):", normalized_city_name)

    products_for_city = []

    df_sample = data_frames['Quantidade produzida']
    product_map = data_frames['Quantidade produzida_header_map']

    print("Nomes de cidades no DataFrame (CSV):", df_sample['CIDADE'].unique())

    city_row = df_sample[df_sample['CIDADE'] == normalized_city_name]

    if not city_row.empty:
        product_cols = [col for col in df_sample.columns if
                        col not in ['CIDADE', 'ANO X PRODUTO DAS LAVOURAS PERMANENTES', 'MUNICIPIO']]
        for col in product_cols:
            value = city_row.iloc[0][col]
            if value and normalize_text(str(value)) not in ['-', '...']:
                original_name = product_map.get(col)
                if original_name:
                    products_for_city.append({'id': col, 'nome': original_name})

    print("Conteúdo enviado para o dropdown:", products_for_city)

    return JsonResponse(products_for_city, safe=False)


# Nova função para obter o nome da cidade a partir do ID e depois os produtos
def get_products_by_city_by_id(request, city_id):
    print("ID da cidade recebido:", city_id)

    try:
        city_url = f"https://servicodados.ibge.gov.br/api/v1/localidades/municipios/{city_id}"
        city_response = requests.get(city_url)
        city_data = city_response.json()
        city_name = city_data.get('nome', '')
        if not city_name:
            return JsonResponse({"error": "Nome da cidade não encontrado para o ID fornecido."}, status=404)
    except requests.exceptions.RequestException as e:
        return JsonResponse({"error": f"Erro ao buscar nome da cidade: {e}"}, status=500)

    return get_products_by_city(request, city_name)


# Nova função para obter os dados detalhados para exibição na dashboard
def get_detailed_data_by_product_and_city(request, city_name, product_name):
    data_frames, status = get_agro_data()
    if data_frames is None:
        return JsonResponse({"error": status}, status=500)

    normalized_city_name = normalize_text(city_name)
    normalized_product_name = normalize_text(product_name)

    results = {}

    # NOVO CÓDIGO: Mapa de unidades de medida
    unit_map = {
        'Quantidade produzida': 'Toneladas',
        'Rendimento médio': 'Quilogramas por Hectare',
        'Valor da produção': 'Reais',
        'Área colhida': 'Hectares',
        'Área destinada': 'Hectares'
    }

    # ALTERAÇÃO: Itera sobre as chaves e verifica se a chave não termina com '_header_map' antes de usar.
    for key, df in data_frames.items():
        if not key.endswith('_header_map'):
            city_row = df[df['CIDADE'] == normalized_city_name]

            if not city_row.empty:
                value = city_row.iloc[0].get(normalized_product_name, 'Dado não disponível')

                # ALTERAÇÃO: Adiciona a unidade de medida ao valor
                # Se o valor for "Dado não disponível", a unidade não é adicionada
                unit = unit_map.get(key, '')

                if normalize_text(str(value)) != normalize_text('Dado não disponível'):
                    final_value = f"{normalize_text(str(value))} {unit}"
                else:
                    final_value = 'Dado não disponível'

                results[key] = final_value
            else:
                results[key] = 'Dado não disponível'

    return JsonResponse(results)
