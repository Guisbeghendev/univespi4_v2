import requests
import pandas as pd
import unicodedata
import re
from .views import get_agro_data  # Importa a função que carrega os dados
from .views import normalize_text  # Importa a função de normalização


# --- Funções de Ranqueamento e Análise ---

def calculate_best_crops_ranking(city_id):
    """
    Calcula um ranking de sugestões de cultivo para uma cidade específica,
    baseado no desempenho histórico (Rendimento e Valor da Produção).

    Args:
        city_id (str): O ID da cidade (IBGE code) para a análise.

    Returns:
        list: Uma lista dos 5 principais cultivos sugeridos com seus scores.
    """
    if not city_id:
        return []

    # 1. Obter o nome normalizado da cidade
    try:
        # Busca o nome real da cidade usando a API do IBGE
        city_url = f"https://servicodados.ibge.gov.br/api/v1/localidades/municipios/{city_id}"
        city_response = requests.get(city_url)
        city_response.raise_for_status()  # Lança exceção para status de erro (4xx ou 5xx)
        city_data = city_response.json()
        city_name = city_data.get('nome', '')
        if not city_name:
            print(f"ERRO: Nome da cidade não encontrado para o ID {city_id}")
            return []
    except requests.exceptions.RequestException as e:
        print(f"ERRO: Falha ao buscar nome da cidade no IBGE: {e}")
        return []

    normalized_city_name = normalize_text(city_name)

    # 2. Carregar os DataFrames
    data_frames, status = get_agro_data()
    if data_frames is None:
        print(f"ERRO: Falha ao carregar dados agrícolas: {status}")
        return []

    try:
        # Pega os DataFrames de Rendimento e Valor
        df_rendimento = data_frames['Rendimento médio']
        df_valor = data_frames['Valor da produção']
        # Pega o mapa para traduzir o nome normalizado de volta para o original
        product_map = data_frames['Quantidade produzida_header_map']
    except KeyError:
        print("ERRO: DataFrames essenciais não encontrados no cache.")
        return []

    # 3. Filtrar dados da cidade
    # Localiza a linha da cidade pelo nome normalizado
    city_rows_rendimento = df_rendimento[df_rendimento['CIDADE'] == normalized_city_name]
    city_rows_valor = df_valor[df_valor['CIDADE'] == normalized_city_name]

    if city_rows_rendimento.empty or city_rows_valor.empty:
        print(f"AVISO: Dados históricos não encontrados para {normalized_city_name}")
        return []

    row_rendimento = city_rows_rendimento.iloc[0]
    row_valor = city_rows_valor.iloc[0]

    # 4. Criar a estrutura de ranqueamento
    ranking = []

    # Colunas de produtos a serem ranqueados (excluindo colunas de metadados)
    product_cols = [col for col in df_rendimento.columns if
                    col not in ['CIDADE', 'ANO X PRODUTO DAS LAVOURAS PERMANENTES', 'MUNICIPIO']]

    # Obter valores máximos globais para normalização
    # Isso garante que a normalização seja consistente em relação ao melhor desempenho global nos dados
    max_rendimento = df_rendimento[product_cols].replace(['-', '...'], [0, 0]).astype(float).max().max()
    max_valor = df_valor[product_cols].replace(['-', '...'], [0, 0]).astype(float).max().max()

    # Garantir que não haja divisão por zero
    if max_rendimento == 0 or max_valor == 0:
        return []

    for col_key in product_cols:
        original_name = product_map.get(col_key)

        if not original_name:
            continue

        try:
            # Limpar e converter valores, tratando ausência de dados como 0
            rendimento = float(str(row_rendimento.get(col_key, 0)).replace('-', '0').replace('...', '0'))
            valor = float(str(row_valor.get(col_key, 0)).replace('-', '0').replace('...', '0'))
        except ValueError:
            continue

        # Ranqueamos apenas produtos com produção positiva
        if rendimento > 0 and valor > 0:
            # Normalização (Min-Max Scaling) para transformar em scores de 0 a 100
            # Isso permite somar diferentes métricas (Rendimento + Valor)
            normalized_rendimento = (rendimento / max_rendimento) * 100
            normalized_valor = (valor / max_valor) * 100

            # Score de Oportunidade: 50% Rentabilidade + 50% Eficiência (peso igual)
            opportunity_score = (normalized_rendimento * 0.5) + (normalized_valor * 0.5)

            ranking.append({
                'name': original_name,
                'score': round(opportunity_score, 2),  # Score final em porcentagem
                'rendimento': rendimento,
                'valor': valor
            })

    # 5. Ordenar por score e retornar os 5 melhores
    ranking.sort(key=lambda x: x['score'], reverse=True)

    return ranking[:5]

# --- Fim das Funções de Ranqueamento e Análise ---
