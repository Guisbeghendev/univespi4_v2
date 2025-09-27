import requests
import json
import os
import pandas as pd
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings
# Importa o novo modelo Terreno e o novo formulário TerrenoForm
from .models import Profile, Terreno
from .forms import ProfileForm, TerrenoForm
from .api_service import get_weather_data
import unicodedata
import re
from django.db import IntegrityError
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

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
                # Tentativa com UTF-8
                df = pd.read_csv(caminho_arquivo, sep=';', encoding='utf-8', skiprows=5)
                product_names_header = pd.read_csv(caminho_arquivo, sep=';', encoding='utf-8', skiprows=4,
                                                   nrows=1).columns.tolist()
            except UnicodeDecodeError:
                # Tentativa com Latin-1
                df = pd.read_csv(caminho_arquivo, sep=';', encoding='latin1', skiprows=5)
                product_names_header = pd.read_csv(caminho_arquivo, sep=';', encoding='latin1', skiprows=4,
                                                   nrows=1).columns.tolist()

            # Lógica para identificar a coluna de município
            municipio_col = df.columns[0]

            if not municipio_col:
                return None, f"Coluna de município não encontrada em '{file_name}'."

            # Mapeamento para nomes originais dos produtos (headers)
            column_map = {}
            for i, normalized_col in enumerate(df.columns):
                # A primeira coluna é a CIDADE, ignoramos no map de produtos
                if i > 0 and i < len(product_names_header):
                    original_name = product_names_header[i]
                    column_map[normalized_col] = original_name

            # O mapa é armazenado com o nome do arquivo (ex: Quantidade produzida_header_map)
            data_frames[f'{key}_header_map'] = column_map

            # Renomeia a coluna principal para facilitar o filtro
            df = df.rename(columns={municipio_col: 'CIDADE'})
            # Normaliza o nome da cidade para comparação
            df['CIDADE'] = df['CIDADE'].apply(normalize_text)

            # Normaliza todas as colunas para o cache
            df.columns = [normalize_text(col) for col in df.columns]

            data_frames[key] = df
            # print(f"DEBUG: Colunas do arquivo '{file_name}' após processamento: {df.columns.tolist()}")

        AGRO_DATA_CACHE = data_frames
        return AGRO_DATA_CACHE, "Sucesso"

    except FileNotFoundError:
        return None, "Erro: Um ou mais arquivos não foram encontrados."
    except Exception as e:
        return None, f"Ocorreu um erro: {str(e)}"


# --- Lógica de Ranking de Sugestões de Cultivo ---
def _calculate_best_crops_ranking(agro_data_cache, city_name):
    """
    Calcula o ranking dos melhores cultivos para a cidade fornecida,
    baseado na pontuação combinada de Rendimento Médio e Valor da Produção.
    """
    if not agro_data_cache:
        return []

    normalized_city_name = normalize_text(city_name)
    results = []

    # 1. Carregar DataFrames e Mapas
    df_rendimento = agro_data_cache.get('Rendimento médio')
    df_valor = agro_data_cache.get('Valor da produção')
    product_map = agro_data_cache.get('Quantidade produzida_header_map', {})

    if df_rendimento is None or df_valor is None:
        # print("DEBUG: DataFrames de rendimento ou valor não encontrados no cache.")
        return []

    # 2. Filtrar dados para a cidade
    city_rendimento_row = df_rendimento[df_rendimento['CIDADE'] == normalized_city_name]
    city_valor_row = df_valor[df_valor['CIDADE'] == normalized_city_name]

    if city_rendimento_row.empty or city_valor_row.empty:
        # print(f"DEBUG: Dados não encontrados para a cidade: {city_name}")
        return []

    # Linhas de dados filtradas (como Series)
    rendimento_series = city_rendimento_row.iloc[0]
    valor_series = city_valor_row.iloc[0]

    # 3. Preparar a lista de todos os produtos para iteração
    # O 'CIDADE' e colunas auxiliares (se existirem) são ignorados
    product_cols = [col for col in df_rendimento.columns if
                    col not in ['CIDADE', 'ANO X PRODUTO DAS LAVOURAS PERMANENTES', 'MUNICIPIO', 'UF']]

    # Coleta de métricas
    data_points = []

    for col in product_cols:
        rendimento = rendimento_series.get(col, None)
        valor = valor_series.get(col, None)

        rendimento_val = 0
        valor_val = 0

        # Reforça o tratamento de valores nulos, zero ou marcadores de ausência ('...', '-')
        r_str = str(rendimento)
        v_str = str(valor)

        if not pd.isna(rendimento) and normalize_text(r_str) not in ['-', '...', '0']:
            try:
                # Converte o formato Brasileiro (ponto como milhar, vírgula como decimal)
                rendimento_val = float(r_str.replace('.', '').replace(',', '.'))
            except (ValueError, TypeError):
                rendimento_val = 0

        if not pd.isna(valor) and normalize_text(v_str) not in ['-', '...', '0']:
            try:
                # Converte o formato Brasileiro (ponto como milhar, vírgula como decimal)
                valor_val = float(v_str.replace('.', '').replace(',', '.'))
            except (ValueError, TypeError):
                valor_val = 0

        # Só considera produtos com dados válidos em ambas as métricas para a pontuação
        if rendimento_val > 0 and valor_val > 0:
            # Busca o nome original do produto, caindo no nome normalizado se não encontrar
            product_name = product_map.get(col)
            if product_name:
                data_points.append({
                    'id': col,
                    'name': product_name,  # Nome original
                    'rendimento': rendimento_val,
                    'valor': valor_val,
                })

    if not data_points:
        return []

    # 4. Normalização (Min-Max) e Pontuação
    all_rendimentos = [p['rendimento'] for p in data_points]
    all_valores = [p['valor'] for p in data_points]

    # Se houver apenas 1 produto, max será o próprio valor, resultando em score 100
    max_rendimento = max(all_rendimentos) if all_rendimentos else 1
    max_valor = max(all_valores) if all_valores else 1

    if max_rendimento == 0: max_rendimento = 1
    if max_valor == 0: max_valor = 1

    # Calcular a pontuação
    for p in data_points:
        # Pontuação de 0 a 1
        score_rendimento = p['rendimento'] / max_rendimento
        score_valor = p['valor'] / max_valor

        # Combina as pontuações (média simples)
        combined_score = (score_rendimento + score_valor) / 2

        # O resultado final deve ser um número inteiro de 0 a 100
        p['score'] = round(combined_score * 100)

    # 5. Classificação (Rank)
    # Classifica por score em ordem decrescente, depois por rendimento
    ranked_crops = sorted(data_points, key=lambda x: (x['score'], x['rendimento']), reverse=True)

    # Limita aos top 20, para exibir o máximo de sugestões disponíveis de forma dinâmica.
    return ranked_crops[:20]


# Funções de autenticação e view (EXISTENTES)
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

    # 1. Obter dados do AGRO e Cache
    agro_data_cache, agro_status = get_agro_data()

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

    # 2. Executar Lógica de Sugestões de Cultivo
    suggestions = []
    # Verifica se a cidade foi configurada no perfil e se os dados do agro estão disponíveis
    if city_name and not city_name.isdigit() and agro_data_cache:
        # Chama a função de ranking.
        suggestions = _calculate_best_crops_ranking(agro_data_cache, city_name)

    # 3. NOVO: Obter a lista de terrenos do usuário
    terrenos = Terreno.objects.filter(user=request.user)
    terreno_form = TerrenoForm()  # Formulário vazio para o modal/criação

    context = {
        'profile': user_profile,
        'state_name': state_name,
        'city_name': city_name,
        'weather_data': weather_data,
        'suggestions': suggestions,  # Adiciona as sugestões ao contexto
        'agro_status': agro_status,  # Adiciona o status do carregamento do agro para debug
        # NOVO: Adiciona a lista de terrenos e o formulário
        'terrenos': terrenos,
        'terreno_form': terreno_form,
    }
    return render(request, 'dashboard.html', context)


# ==============================================================================
# NOVAS VIEWS PARA GERENCIAMENTO DE TERRENOS (CRUD)
# ==============================================================================

@login_required
def create_terreno(request):
    """
    Cria um novo terreno associado ao usuário logado.
    """
    if request.method == 'POST':
        form = TerrenoForm(request.POST)
        if form.is_valid():
            terreno = form.save(commit=False)
            terreno.user = request.user  # Associa o terreno ao usuário logado
            terreno.save()
            # Redireciona de volta para o dashboard após salvar
            return redirect('agro_app:dashboard')
        # Se o formulário for inválido, ele redirecionará de volta para o dashboard
        # onde o form_terreno com erros será reexibido

    # Se for GET, apenas redireciona para o dashboard, pois o formulário é exibido lá.
    return redirect('agro_app:dashboard')


@login_required
def edit_terreno(request, pk):
    """
    Edita um terreno existente do usuário logado.
    O pk (primary key) identifica qual terreno será editado.
    """
    # Garante que só o usuário dono do terreno possa editá-lo.
    terreno = get_object_or_404(Terreno, pk=pk, user=request.user)

    if request.method == 'POST':
        form = TerrenoForm(request.POST, instance=terreno)
        if form.is_valid():
            form.save()
            # Redireciona de volta para o dashboard após salvar com sucesso
            return redirect('agro_app:dashboard')
    else:
        # Para GET, retorna o formulário preenchido com os dados do terreno
        form = TerrenoForm(instance=terreno)

    # CORREÇÃO: Renderiza o template de edição em vez de redirecionar para a dashboard.
    context = {
        'form': form,
        'terreno': terreno  # Passa o objeto terreno para o título/contexto do template
    }
    # NOTA: O template 'edit_terreno.html' precisa ser criado para exibir este formulário!
    return render(request, 'edit_terreno.html', context)


@login_required
def delete_terreno(request, pk):
    """
    Exclui um terreno existente do usuário logado.
    """
    # Garante que só o usuário dono do terreno possa excluí-lo.
    terreno = get_object_or_404(Terreno, pk=pk, user=request.user)

    if request.method == 'POST':
        terreno.delete()
        # Após a exclusão, retorna para o dashboard.
        return redirect('agro_app:dashboard')

    # Para GET (pedindo confirmação), vamos redirecionar para o dashboard
    return redirect('agro_app:dashboard')


# VIEWS DE PERFIL E AJAX (EXISTENTES)

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
    # print("Nome da cidade recebido:", city_name)

    data_frames, status = get_agro_data()

    if data_frames is None:
        return JsonResponse({"error": status}, status=500)

    normalized_city_name = normalize_text(city_name)
    # print("Nome da cidade normalizado (IBGE):", normalized_city_name)

    products_for_city = []

    df_sample = data_frames['Quantidade produzida']
    product_map = data_frames['Quantidade produzida_header_map']

    # print("Nomes de cidades no DataFrame (CSV):", df_sample['CIDADE'].unique())

    city_row = df_sample[df_sample['CIDADE'] == normalized_city_name]

    if not city_row.empty:
        product_cols = [col for col in df_sample.columns if
                        col not in ['CIDADE', 'ANO X PRODUTO DAS LAVOURAS PERMANENTES', 'MUNICIPIO']]
        for col in product_cols:
            value = city_row.iloc[0].get(col)
            if value is not None and normalize_text(str(value)) not in ['-', '...']:
                original_name = product_map.get(col)
                if original_name:
                    products_for_city.append({'id': col, 'nome': original_name})

    # print("Conteúdo enviado para o dropdown:", products_for_city)

    return JsonResponse(products_for_city, safe=False)


# Nova função para obter o nome da cidade a partir do ID e depois os produtos
def get_products_by_city_by_id(request, city_id):
    # print("ID da cidade recebido:", city_id)

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
                    final_value = f"{str(value).replace('.', '').replace(',', '.')} {unit}"
                else:
                    final_value = 'Dado não disponível'

                results[key] = final_value
            else:
                results[key] = 'Dado não disponível'

    return JsonResponse(results)
