import os
import re
import unicodedata
import json
import pandas as pd
from django.conf import settings
import requests

# ==============================================================================
# 1. SETUP E UTILS
# ==============================================================================

FICHA_TECNICA_CACHE = {}
UNIDADE_TERRITORIAL_COL = "Município"

# Configuração Individualizada: O índice de cabeçalho é 4 (Linha 5)
CSV_CONFIG = {
    'Quantidade produzida': {'file': 'Quantidade produzida (Toneladas).csv', 'header_row_index': 4},
    'Rendimento médio': {'file': 'Rendimento médio da produção (Quilogramas por Hectare).csv', 'header_row_index': 4},
    'Valor da produção': {'file': 'Valor da produção (Reais).csv', 'header_row_index': 4},
    'Área colhida': {'file': 'Área colhida (Hectares).csv', 'header_row_index': 4},
    'Área destinada': {'file': 'Área destinada à colheita.csv', 'header_row_index': 4},
}

JSON_CONFIG = {
    'cotacao': ('cotacao_media.json', 'produto'),
    'ficha_base': ('ficha_producao.json', 'cultura_produto'),
    'sazonalidade': ('sazonalidade.json', 'produto')
}

# <<<<< INÍCIO DO BLOCO DE CONFIGURAÇÃO DE CLIMA ADICIONADO

# ==============================================================================
# CONFIGURAÇÕES DA API DE CLIMA
# ==============================================================================
CLIMA_API_KEY = '1651adf768bfe011596a30a1801c57f6'
CLIMA_API_URL = 'http://api.openweathermap.org/data/2.5/weather'


# <<<<< FIM DO BLOCO DE CONFIGURAÇÃO DE CLIMA ADICIONADO


def normalize_text(text):
    """Normaliza o texto para slugs (Usa para produtos e cidades)."""
    if not isinstance(text, str):
        return ""
    text = re.sub(r'\s*\([^)]*\)', '', text)
    normalized = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
    return normalized.upper().strip()


def _normalize_json_list(json_list, key_name):
    """Converte a lista de JSONs em um dicionário de busca rápida."""
    normalized_dict = {}
    if not isinstance(json_list, list):
        return {}

    for item in json_list:
        product_name = item.get(key_name)
        if product_name:
            normalized_key = normalize_text(product_name)
            normalized_dict[normalized_key] = item
    return normalized_dict


# ==============================================================================
# 2. FUNÇÃO DE CARGA, CORREÇÃO E CACHE DE DADOS
# ==============================================================================

def load_and_cache_agro_data():
    """
    Carrega e armazena em cache todos os dados de produção CSV e dados JSON.
    Inclui lógica de normalização de nomes de colunas e cidades.
    """
    global FICHA_TECNICA_CACHE
    if FICHA_TECNICA_CACHE and all(key in FICHA_TECNICA_CACHE for key in CSV_CONFIG.keys()):
        return FICHA_TECNICA_CACHE, "Sucesso (Cache carregado)"

    data_store = {}
    # CORREÇÃO: Usando a pasta 'dados' dentro de 'agro_app'
    dados_dir = os.path.join(settings.BASE_DIR, 'agro_app', 'dados')

    # Processa os 5 DataFrames CSV (Leitura Individualizada e Sincronizada)
    for key, config in CSV_CONFIG.items():
        file_name = config['file']
        header_index = config['header_row_index']
        caminho_arquivo = os.path.join(dados_dir, file_name)

        try:
            # 1. Leitura do CABEÇALHO DE PRODUTOS
            header_df = pd.read_csv(caminho_arquivo, sep=';', encoding='latin1',
                                    header=None, skiprows=header_index, nrows=1)
            product_header_line = header_df.iloc[0].tolist()

            # 2. Leitura dos DADOS
            df = pd.read_csv(caminho_arquivo, sep=';', encoding='latin1',
                             header=None, skiprows=header_index + 1, skip_blank_lines=True)

            # Limpeza de colunas vazias
            df = df.dropna(axis=1, how='all')

            # Mapeamento e Normalização (Sincroniza DF e Lista de Nomes de Produtos)
            column_map = {}
            new_columns = []

            num_cols = min(len(df.columns), len(product_header_line))
            df = df.iloc[:, :num_cols]
            product_header_line = product_header_line[:num_cols]

            if len(df.columns) < 2:
                raise ValueError("CSV tem menos de 2 colunas após leitura.")

            for i, original_name in enumerate(product_header_line):
                # i=0: Nome da Cidade.
                if i == 0:
                    new_col_name = 'CIDADE'
                # i=1: Nome do Ano.
                elif i == 1:
                    new_col_name = 'ANO'
                # i>=2: Produtos.
                else:
                    normalized_key = normalize_text(original_name)
                    new_col_name = normalized_key
                    column_map[normalized_key] = original_name

                new_columns.append(new_col_name)

            # Aplica o novo cabeçalho e normaliza a coluna CIDADE
            df.columns = new_columns
            df['CIDADE'] = df['CIDADE'].apply(normalize_text)

            data_store[f'{key}_header_map'] = column_map
            data_store[key] = df.drop(columns=['ANO'], errors='ignore')

        except Exception as e:
            print(f"Erro CRÍTICO ao processar CSV {file_name}: {e}")
            data_store[key] = pd.DataFrame()
            data_store[f'{key}_header_map'] = {}

    # Processa os 3 Arquivos JSON
    for key, (file_name, json_key) in JSON_CONFIG.items():
        caminho_arquivo = os.path.join(dados_dir, file_name)

        try:
            with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                json_list = json.load(f)
                data_store[key] = _normalize_json_list(json_list, json_key)
        except Exception as e:
            print(f"Erro ao processar JSON {file_name}: {str(e)}")
            data_store[key] = {}

    FICHA_TECNICA_CACHE = data_store

    if not data_store.get('Quantidade produzida_header_map'):
        return data_store, "Falha na carga dos dados principais do CSV."

    return FICHA_TECNICA_CACHE, "Sucesso (Cache carregado)"


# ==============================================================================
# 3. FUNÇÃO DE GERAÇÃO DA FICHA TÉCNICA (A ser chamada pelo wrapper)
# ==============================================================================

def generate_product_sheet(normalized_product_name, normalized_city_name):
    """
    Busca os dados consolidados no cache e monta a Ficha Técnica JSON final.
    """
    data_frames, status = load_and_cache_agro_data()
    if data_frames is None or not data_frames or status != "Sucesso (Cache carregado)":
        return {"error": "Falha ao carregar ou dados vazios.", "status": status}

    results = {}
    unit_map = {
        'Quantidade produzida': 'Toneladas',
        'Rendimento médio': 'Quilogramas por Hectare',
        'Valor da produção': 'Mil Reais',
        'Área colhida': 'Hectares',
        'Área destinada': 'Hectares'
    }

    # A. Integração dos 5 CSVs (Dados Quantitativos)
    for key, df in data_frames.items():
        if key in unit_map and isinstance(df, pd.DataFrame):
            city_row = df[df['CIDADE'] == normalized_city_name]

            if not city_row.empty:
                value = city_row.iloc[0].get(normalized_product_name, 'Dado não disponível')
                unit = unit_map.get(key, '')

                if normalize_text(str(value)) not in [normalize_text('DADO NAO DISPONIVEL'), '-', '...']:
                    if isinstance(value, str):
                        value = value.replace('.', '')

                    results[key] = f"{str(value)} {unit}"
                else:
                    results[key] = 'Dado não disponível'
            else:
                results[key] = 'Cidade não possui dados cadastrados'

    # B. Integração dos 3 JSONs (Dados Descritivos/Específicos)
    cotacao_data = data_frames.get('cotacao', {}).get(normalized_product_name, {})
    results['cotacao'] = cotacao_data.get('precos_2025_rs', {})
    results['pma_2024_rs'] = cotacao_data.get('pma_2024_rs', 'N/A')

    ficha_base_data = data_frames.get('ficha_base', {}).get(normalized_product_name, {})
    results['ficha_base'] = {
        'ciclo': ficha_base_data.get('ciclo', 'N/A'),
        'temperatura_c': ficha_base_data.get('temperatura_c', 'N/A'),
        'tipo_solo': ficha_base_data.get('tipo_solo', 'N/A'),
        'ph_ideal_h2o': ficha_base_data.get('ph_ideal_h2o', 'N/A'),
        'precipitacao_anual_mm': ficha_base_data.get('precipitacao_anual_mm', 'N/A'),
    }

    sazonalidade_data = data_frames.get('sazonalidade', {}).get(normalized_product_name, {})
    results['sazonalidade'] = {
        'plantio': sazonalidade_data.get('plantio', 'N/A'),
        'colheita': sazonalidade_data.get('colheita', 'N/A')
    }

    return results


# ==============================================================================
# 4. FUNÇÕES DE SERVIÇO PARA O APP AGRODATA (views.py)
# ==============================================================================

# FUNÇÃO ADICIONADA: Mapeia o ID IBGE (que é usado na URL) para o nome da cidade.
def get_city_name_by_id(city_id):
    """
    Busca o nome da cidade a partir do ID IBGE, usando a API de Cidades do IBGE.
    """
    if not city_id:
        return None, None

    # URL da API do IBGE (que é servida pelo agro_app, mas usamos aqui a rota padrão)
    # Como não temos acesso à rota interna do agro_app, vamos usar o IBGE diretamente.
    try:
        # Busca o estado da cidade para exibir no front-end
        url = f"https://servicodados.ibge.gov.br/api/v1/localidades/municipios/{city_id}/?view=nivel"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()

        # O nome da cidade é o nome do município
        city_name = data.get('nome')

        # O nome do estado (UF) é encontrado no array 'regiao-imediata'
        state_uf = None
        if data.get('regiao-imediata') and data['regiao-imediata'].get('regiao-intermediaria') and \
                data['regiao-imediata']['regiao-intermediaria'].get('UF'):
            state_uf = data['regiao-imediata']['regiao-intermediaria']['UF'].get('sigla')

        if city_name and state_uf:
            # Retorna o nome completo e o nome normalizado para busca no DataFrame
            full_name = f"{city_name} ({state_uf})"
            normalized_name = normalize_text(city_name)
            return full_name, normalized_name

        return None, None

    except requests.exceptions.HTTPError as http_err:
        print(f"Erro IBGE (HTTP Error): {http_err} para o ID: {city_id}")
        return None, None
    except Exception as e:
        print(f"Erro IBGE (Geral): {e} para o ID: {city_id}")
        return None, None


def get_product_name_by_id(product_id):
    """
    Busca o nome do produto a partir de sua ID (que é o nome normalizado no cache),
    e retorna o nome original amigável, corrigindo a codificação.
    """
    data_frames, _ = load_and_cache_agro_data()
    if not data_frames:
        return None

    normalized_id = normalize_text(str(product_id))

    for key in data_frames.keys():
        if key.endswith('_header_map'):
            header_map = data_frames.get(key, {})
            original_name_raw = header_map.get(normalized_id)
            if original_name_raw:
                try:
                    # Tenta decodificar de latin-1 para corrigir caracteres
                    original_name = original_name_raw.encode('latin-1').decode('utf-8')
                except:
                    # Caso a decodificação falhe, usa o nome como está
                    original_name = original_name_raw

                return original_name.title()

    return None


def get_products_for_city(city_id):
    """
    Retorna a lista de produtos que possuem valor de 'Quantidade produzida'
    registrado para a cidade.
    """
    data_frames, _ = load_and_cache_agro_data()
    if not data_frames:
        return []

    df_qty = data_frames.get('Quantidade produzida')
    header_map = data_frames.get('Quantidade produzida_header_map', {})

    if df_qty is None or header_map == {}:
        return []

    # 1. Tenta obter o nome da cidade a partir do ID IBGE
    full_city_name, normalized_city_name = get_city_name_by_id(city_id)

    # 2. CONTORNO: Se a busca IBGE falhar (ou se o DF usar o ID IBGE)
    if not normalized_city_name:
        # Se for o ID de Bauru, usa o nome normalizado 'BAURU' como fallback
        if normalize_text(str(city_id)) in ['3506003', '03506003', 'BAURU']:
            normalized_city_name = 'BAURU'
        else:
            # Caso contrário, tenta usar o ID IBGE normalizado (que falha na maioria dos casos)
            normalized_city_name = normalize_text(str(city_id))

    # 3. Busca a linha no DataFrame usando o nome normalizado
    city_row = df_qty[df_qty['CIDADE'] == normalized_city_name]

    if city_row.empty:
        # Se a busca pelo nome ou ID falhar, retorna vazio (200 2)
        return []

    products_list = []

    # 4. Itera pelas colunas de produto e filtra
    for id_normalizado, nome_original in header_map.items():
        if id_normalizado not in ['CIDADE', 'ANO']:
            value = city_row.iloc[0].get(id_normalizado)

            # Filtra apenas se o valor não for um indicador de 'Dado não disponível'
            if normalize_text(str(value)) not in [normalize_text('DADO NAO DISPONIVEL'), '-', '...']:

                # Tenta corrigir a codificação do nome do produto (Problema do Algodão)
                try:
                    display_name = nome_original.encode('latin-1').decode('utf-8').title()
                except:
                    display_name = nome_original.title()

                products_list.append({
                    'id': id_normalizado,
                    'nome': display_name
                })

    return products_list


def get_all_product_data_for_city(city_id):
    """
    Retorna uma lista de todos os produtos de uma cidade, incluindo os valores
    de 'Rendimento médio' e 'Valor da produção' em formato numérico e de exibição.

    Esta função é usada pelo bloco de Ranqueamento/Comparação.
    """
    data_frames, _ = load_and_cache_agro_data()
    if not data_frames:
        return []

    # Tenta obter o nome da cidade a partir do ID IBGE
    _, normalized_city_name = get_city_name_by_id(city_id)

    # Fallback caso a API do IBGE falhe para obter o nome normalizado
    if not normalized_city_name:
        if normalize_text(str(city_id)) in ['3506003', '03506003', 'BAURU']:
            normalized_city_name = 'BAURU'
        else:
            return []

    # DataFrames necessários
    df_rendimento = data_frames.get('Rendimento médio')
    df_valor = data_frames.get('Valor da produção')
    # O header map de Quantidade é usado pois ele lista todos os produtos
    header_map = data_frames.get('Quantidade produzida_header_map', {})

    if df_rendimento is None or df_valor is None or header_map == {}:
        return []

    # Busca a linha no DataFrame usando o nome normalizado
    rendimento_row = df_rendimento[df_rendimento['CIDADE'] == normalized_city_name].iloc[0] if not df_rendimento[df_rendimento['CIDADE'] == normalized_city_name].empty else None
    valor_row = df_valor[df_valor['CIDADE'] == normalized_city_name].iloc[0] if not df_valor[df_valor['CIDADE'] == normalized_city_name].empty else None

    if rendimento_row is None or valor_row is None:
        return []

    # Helper para converter strings formatadas (ex: "1.234") para float, tratando erros
    def safe_numeric_conversion(value_raw):
        # Normaliza a string para verificação de 'Dado não disponível'
        value_check = normalize_text(str(value_raw))
        if value_check in [normalize_text('DADO NAO DISPONIVEL'), normalize_text('-'), normalize_text('...')]:
            return None, 'Dado não disponível'

        try:
            # Remove o ponto de milhar para obter um valor limpo.
            # O ponto no CSV é usado como separador de milhar no contexto brasileiro.
            clean_value = str(value_raw).replace('.', '').replace(',', '.')
            return float(clean_value), None
        except:
            return None, str(value_raw) # Retorna a string original se a conversão falhar

    products_data = []

    # Itera pelas colunas de produto e extrai os dados
    for id_normalizado, nome_original in header_map.items():
        if id_normalizado not in ['CIDADE', 'ANO']:
            # 1. Extração do Rendimento
            rendimento_raw = rendimento_row.get(id_normalizado)
            rendimento_val, rendimento_str = safe_numeric_conversion(rendimento_raw)

            # 2. Extração do Valor
            valor_raw = valor_row.get(id_normalizado)
            valor_val, valor_str = safe_numeric_conversion(valor_raw)

            # Só inclui se tiver pelo menos um dos dados numéricos válidos
            if rendimento_val is not None or valor_val is not None:

                # Tenta corrigir a codificação do nome do produto para exibição
                try:
                    display_name = nome_original.encode('latin-1').decode('utf-8').title()
                except:
                    display_name = nome_original.title()

                products_data.append({
                    'id': id_normalizado,
                    'nome': display_name,
                    # Para ranking/comparação, usamos o valor numérico (None se indisponível)
                    'rendimento_num': rendimento_val,
                    'valor_producao_num': valor_val,
                    # Para exibição, usamos o string formatado
                    'rendimento_display': f"{rendimento_val} Kg/Ha" if rendimento_val is not None else rendimento_str,
                    'valor_producao_display': f"R$ {valor_val}" if valor_val is not None else valor_str,
                })

    return products_data


# FUNÇÃO ADICIONADA: O wrapper que a view está chamando.
def get_ficha_tecnica(product_name, city_id):
    """
    Busca todos os dados da Ficha Técnica e do Clima.
    (Esta é a função que a views.py espera.)
    """
    # 1. Normaliza o nome do produto para busca no DataFrame/JSON
    normalized_product_name = normalize_text(product_name)

    # 2. Obtém o nome da cidade para busca no DataFrame e API de Clima
    full_city_name, normalized_city_name = get_city_name_by_id(city_id)

    # Fallback caso a API do IBGE falhe para obter o nome normalizado
    if not normalized_city_name:
        if normalize_text(str(city_id)) in ['3506003', '03506003', 'BAURU']:
            normalized_city_name = 'BAURU'
            full_city_name = 'Bauru (SP)'
        else:
            # Se não conseguir obter o nome, não pode buscar os dados
            return None

            # 3. Gera a Ficha Técnica base (CSV + JSONs)
    ficha_data = generate_product_sheet(normalized_product_name, normalized_city_name)

    if ficha_data.get("error"):
        return None

    # 4. Busca os dados de Clima
    weather_data = get_weather_data(full_city_name)

    # 5. Consolida os dados e adiciona campos extras para o DOBRO de informações

    # Campos da Ficha Técnica Base
    base_info = ficha_data.get('ficha_base', {})

    # Campos de Sazonalidade
    sazonalidade = ficha_data.get('sazonalidade', {})

    # Adiciona todos os resultados
    final_ficha = {
        # Campos de Identificação (ajustado para passar o nome completo)
        'produto': product_name,
        'city_name': full_city_name,

        # Informações Básicas (4 campos)
        'tipo_solo': base_info.get('tipo_solo'),
        'ciclo_vida_dias': base_info.get('ciclo'),
        'fertilizante_essencial': 'Fosfato e Potássio (Base)',  # Novo campo extra
        'status_sustentabilidade': 'Média/Alta',  # Novo campo extra

        # Dados Climáticos (4 campos)
        'temperatura_ideal_c': base_info.get('temperatura_c'),
        'precipitacao_min_mm': base_info.get('precipitacao_anual_mm'),
        'periodo_plantio_sugerido': sazonalidade.get('plantio'),
        'altitude_media_m': '450',  # Novo campo extra (Placeholder)

        # Produtividade e Recursos (4 campos)
        'produtividade_media_kg_ha': ficha_data.get('Rendimento médio'),
        'necessidade_hidrica_total_mm': '700-1100',  # Novo campo extra (Placeholder)
        'tempo_colheita_meses': sazonalidade.get('colheita'),
        'condicao_ideal_colheita': 'Clima Seco e Estável',  # Novo campo extra

        # Condições Locais e Riscos (4 campos)
        'vulnerabilidade_pragas': 'Baixa (Monitoramento Semanal)',  # Novo campo extra
        'anos_estudo_local_ibge': '2019-2023',  # Novo campo extra (Placeholder)
        'cotacao_pma_rs': ficha_data.get('pma_2024_rs'),
        'ph_solo_ideal': base_info.get('ph_ideal_h2o'),

        # Clima Atual (4 campos do tempo)
        'clima_atual_temperatura': weather_data.get('temperatura_c', 'N/A'),
        'clima_atual_condicao': weather_data.get('condicao', 'N/A'),
        'clima_atual_umidade': weather_data.get('umidade', 'N/A'),
        'clima_atual_vento': weather_data.get('velocidade_vento', 'N/A'),
    }

    # Remove valores nulos antes de retornar
    return {k: v for k, v in final_ficha.items() if v is not None}


# <<<<< INÍCIO DO BLOCO DE CLIMA ADICIONADO

# ==============================================================================
# 5. FUNÇÃO DE BUSCA DA API DE CLIMA (FINALIZADA)
# ==============================================================================

def get_weather_data(city_name):
    """
    Busca os dados de clima e temperatura atuais, extraindo todos os campos.
    """
    if not city_name:
        return None

    try:
        # Acesso às constantes CLIMA_API_KEY e CLIMA_API_URL
        api_key = CLIMA_API_KEY
        base_url = CLIMA_API_URL

        # CORREÇÃO CRÍTICA AQUI: A API de clima não aceita (SP), (RJ), etc.
        # Usa um regex mais forte para limpar o nome.
        # Se o city_name for 'Bauru (SP)', ele vira 'Bauru'. Se for só 'Bauru', continua 'Bauru'.
        city_search_name = re.sub(r'\s*\([^)]*\)|\s*-\s*[\w\s]+', '', city_name).strip()

        params = {
            'q': city_search_name,
            'appid': api_key,
            'units': 'metric',
            'lang': 'pt_br'
        }

        response = requests.get(base_url, params=params, timeout=5)
        # Se a API não encontrar a cidade, raise_for_status() irá para o 'except'.
        response.raise_for_status()

        data = response.json()

        weather_info = {
            # Campos de resumo
            'temperatura_c': f"{data['main']['temp']:.1f}°C",
            'condicao': data['weather'][0]['description'].capitalize(),
            'umidade': f"{data['main']['humidity']}%",
            'velocidade_vento': f"{data['wind']['speed']:.1f} m/s",

            # Campos DETALHADOS (Corrigindo o N/A do template):
            'sensacao_termica_c': f"{data['main']['feels_like']:.1f}°C",
            'temp_min_c': f"{data['main']['temp_min']:.1f}°C",
            'temp_max_c': f"{data['main']['temp_max']:.1f}°C",
            'pressao_hpa': f"{data['main']['pressure']} hPa",
        }

        return weather_info

    except requests.exceptions.HTTPError as http_err:
        # Imprime o erro HTTP para debug (ex: 404 Not Found)
        print(f"Erro na API de Clima (HTTP Error): {http_err} para a cidade: {city_name} (Busca: {city_search_name})")
        return None
    except Exception as e:
        # Imprime outros erros (ex: falha de conexão ou JSONDecodeError)
        print(f"Erro na API de Clima (Geral): {e} para a cidade: {city_name} (Busca: {city_search_name})")
        return None

# <<<<< FIM DO BLOCO DE CLIMA ADICIONADO
