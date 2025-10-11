import requests
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
# CORREÇÃO 1/2: Importa Produto, que é o nome atual do modelo.
from .models import Profile, Terreno, Produto
from .forms import ProfileForm
from fichatecnica_app import data_service
# CORREÇÃO CRÍTICA: Importa as funções necessárias para a nova lógica de busca.
from fichatecnica_app.data_service import get_products_for_city, normalize_text
# INSERIDO: Importa o formulário de terreno do novo aplicativo (terreno_app)
from terreno_app.forms import TerrenoForm

# ------------------------------------------------------------------------------------------------------
# ### CONFIGURAÇÃO E CONSTANTES GLOBAIS ###
# ------------------------------------------------------------------------------------------------------
# Define o número de itens a serem exibidos em cada lista de ranqueamento (Bloco 4)
TOP_N_SUGGESTIONS = 5


# ### CONTROLE DE VISIBILIDADE & DASHBOARD ###
# ------------------------------------------------------------------------------------------------------
@login_required
def dashboard(request):
    # ----------------------------------------------------------------------
    #### DICIONÁRIO DE CONTROLE DE VISIBILIDADE (POSIÇÃO EXIGIDA: TOPO DA FUNÇÃO)
    # Dicionário simples para controle ON/OFF de cada bloco
    controle_de_visibilidade = {
        'bloco2': True,  # Climalocal_app
        'bloco3': True,  # info_app
        'bloco4': True,  # Ranqueamento (Lucratividade e Preço)
        'bloco5': True,  # terreno_app
        'bloco6': True,  # cotação
        'bloco7': True,
    }
    # ----------------------------------------------------------------------

    # Lógica ADICIONAL para o Bloco 1 (Saudação/Status):
    user_profile, created = Profile.objects.get_or_create(user=request.user)

    # Busca os nomes da Cidade e Estado para passar para o contexto (usado no bloco1.html)
    # CORREÇÃO: Substituído .city por .cidade e .state por .estado
    city_id = user_profile.cidade
    city_name = get_city_name_from_id(city_id) if city_id else None
    state_name = get_state_name_from_id(user_profile.estado) if user_profile.estado else None

    # INSERIDO: Lógica para Terrenos (Bloco 1)
    terrenos = Terreno.objects.filter(proprietario=request.user).order_by('nome')
    terreno_form = TerrenoForm()
    # INSERIDO: Lógica para Plano de Plantio (Bloco 5)
    # ATENÇÃO: Adicione a importação de PlanoPlantio aqui ou no topo se o modelo estiver no agro_app.models
    # Se o modelo PlanoPlantio está em agro_app.models, ele já está disponível se foi importado.
    # Se PlanoPlantio está em outro app (ex: plano_app), a importação deve ser ajustada.
    # Por enquanto, assumimos que PlanoPlantio não está totalmente configurado, mas o form de seleção sim.
    # Passando um queryset vazio ou None para evitar erro caso o PlanoPlantio ainda não esteja acessível.
    planos_plantio = []  # Placeholder: Mude isto quando o PlanoPlantio estiver configurado


    # ----------------------------------------------------------------------
    # CÓDIGO DO CLIMA (Bloco 2)
    # ----------------------------------------------------------------------
    weather_data = None
    if city_name:
        weather_data = data_service.get_weather_data(city_name)

    print(f"DEBUG CLIMA RETORNO FINAL: {weather_data} para a cidade: {city_name}")

    # ----------------------------------------------------------------------
    # --- INÍCIO: LÓGICA DO BLOCO 4 (Ranqueamento Passivo) ---
    # Ranqueamento passivo baseado nos dados da Ficha Técnica (Rendimento e Valor)
    suggestions_lucratividade = []
    suggestions_preco = []

    if city_id:
        try:
            # 1. Obter dados: Busca todos os dados de produto da Ficha Técnica para a cidade
            # NOTA: Assumido que data_service.get_all_product_data_for_city(city_id) retorna uma lista de dicionários
            all_products_data = data_service.get_all_product_data_for_city(city_id)

            # >>> DEBUG ADICIONADO AQUI <<<
            print(
                f"DEBUG BLOCO 4 - RAW DATA: Total de {len(all_products_data)} produtos retornados por get_all_product_data_for_city.")

            # 2. Processamento: Cálculo do Preço por Quilo (R$/kg)
            processed_data = []
            for product in all_products_data:
                # CORREÇÃO CRÍTICA: As chaves corretas do data_service são 'rendimento_num' e 'valor_producao_num'.
                # O 'or 0' garante que valores None (retornados pelo safe_numeric_conversion) sejam tratados como 0.
                rendimento = product.get('rendimento_num', 0) or 0
                valor = product.get('valor_producao_num', 0) or 0

                # DEBUG: Vê o que está sendo filtrado
                print(
                    f"DEBUG BLOCO 4 - FILTRO: Produto={product.get('nome', 'N/A')}, Rendimento={rendimento}, Valor={valor}")

                # Filtra apenas produtos com dados válidos (Valor e Rendimento devem ser positivos)
                if rendimento > 0 and valor > 0:
                    # Preço por Quilo: Valor Total (R$) / Rendimento (kg/ha)
                    preco_por_quilo = valor / rendimento

                    processed_data.append({
                        # CORREÇÃO: Usar a chave 'nome' para o nome de exibição
                        'name': product.get('nome', 'N/A'),
                        'rendimento': rendimento,
                        # Para o ranking, usamos o valor total de produção (R$)
                        'valor': valor,
                        'preco_por_quilo': preco_por_quilo
                    })

            # >>> DEBUG ADICIONADO AQUI <<<
            print(f"DEBUG BLOCO 4 - PROCESSED DATA: Total de {len(processed_data)} produtos válidos para ranqueamento.")

            # 3. Ranqueamento de Lucratividade: Ordena pelo 'valor' (R$) em ordem decrescente.
            suggestions_lucratividade = sorted(
                processed_data,
                key=lambda x: x['valor'],
                reverse=True
            )[:TOP_N_SUGGESTIONS]

            # 4. Ranqueamento de Preço Unitário: Ordena pelo 'preco_por_quilo' (R$/kg) em ordem crescente.
            suggestions_preco = sorted(
                processed_data,
                key=lambda x: x['preco_por_quilo'],
                reverse=False
            )[:TOP_N_SUGGESTIONS]


        except Exception as e:
            print(f"ERRO AO GERAR SUGESTÕES DO BLOCO 4: {e}")

    # --- FIM: LÓGICA DO BLOCO 4 (Ranqueamento Passivo) ---

    # Combina o controle de visibilidade com os dados do perfil e NOVOS DADOS DO BLOCO 4.
    context = {
        'visibilidade': controle_de_visibilidade,
        'city_name': city_name,
        'state_name': state_name,
        'profile': user_profile,
        'clima': weather_data,
        'suggestions_lucratividade': suggestions_lucratividade,
        'suggestions_preco': suggestions_preco,
        # INSERIDO: Adiciona o formulário de terreno ao contexto
        'terreno_form': terreno_form,
        # INSERIDO: Adiciona a lista de terrenos ao contexto
        'terrenos': terrenos,
        # INSERIDO: Adiciona a lista de planos de plantio (vazia ou real)
        'planos_plantio': planos_plantio,
    }

    return render(request, 'dashboard.html', context)


# ------------------------------------------------------------------------------------------------------
### FUNÇÕES AUXILIARES DE TRADUÇÃO (Para Perfil e Dashboard)
# ------------------------------------------------------------------------------------------------------

# NOVA FUNÇÃO: Adicionada para buscar o nome do país
def get_country_name_from_id(country_id):
    """Retorna o nome do país a partir da ID (assumindo 1058 = Brasil)."""
    if not country_id: return None
    # Esta é a ID do Brasil segundo a API do IBGE, mas o Profile pode usar um padrão diferente.
    # Assumimos que a ID é '1058' ou 'BR' ou o nome já está salvo como string.

    # Se o valor salvo for a string '1058' ou o número 1058
    if str(country_id) in ['1058']:
        return "Brasil"

    # Se o campo for uma string preenchida (ex: 'Brasil' ou 'BRA') e não for o valor padrão
    if isinstance(country_id, str) and country_id.strip() not in ('', '-'):
        return country_id.title()

    # Caso contrário, tenta a API do IBGE (países) se necessário, mas geralmente é fixo.
    try:
        url = f"https://servicodados.ibge.gov.br/api/v1/localidades/paises/{country_id}"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        return data[0].get('nome') if isinstance(data, list) else None
    except:
        # Se a busca falhar ou o ID não for padrão (e não for 'Brasil'), retorna None
        return None


def get_city_name_from_id(city_id):
    """Busca o nome da cidade a partir da ID do IBGE. Usa a API do IBGE."""
    if not city_id: return None
    try:
        url = f"https://servicodados.ibge.gov.br/api/v1/localidades/municipios/{city_id}"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        return data.get('nome')
    except (requests.RequestException, json.JSONDecodeError):
        return None


def get_state_name_from_id(state_id):
    """Busca a sigla do estado a partir da ID do IBGE."""
    if not state_id: return None
    try:
        url = f"https://servicodados.ibge.gov.br/api/v1/localidades/estados/{state_id}"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        return data.get('sigla')
    except (requests.RequestException, json.JSONDecodeError):
        return None


def get_product_name_from_id(product_id, city_id):
    """
    Busca o nome do produto comparando o ID normalizado salvo
    com a lista de produtos retornada pela API para a cidade.
    """
    if not product_id or not city_id: return None

    try:
        # 1. Normaliza o ID/Nome que está salvo no perfil (ex: 'SOJA')
        normalized_saved_id = normalize_text(str(product_id))

        # 2. Puxa a lista de produtos da API para a cidade salva.
        products_data = get_products_for_city(city_id)

        # 3. Filtra a lista de produtos para encontrar o nome de exibição.
        for product in products_data:
            # A chave 'id' da API é o nome normalizado (ex: 'SOJA')
            if product.get('id', '') == normalized_saved_id:
                return product.get('nome')  # Retorna o nome amigável (ex: 'Soja')

        return None
    except Exception:
        return None


# ------------------------------------------------------------------------------------------------------
# VIEWS DE PERFIL
# ------------------------------------------------------------------------------------------------------

@login_required
def profile(request):
    """Exibe o perfil do usuário, buscando nomes de cidade e cultivo por ID."""
    user_profile, created = Profile.objects.get_or_create(user=request.user)

    # NOVO: Busca o nome do País
    country_name = get_country_name_from_id(user_profile.pais) if user_profile.pais else None

    # CORREÇÃO: Substituído .city por .cidade e .state por .estado
    city_name = get_city_name_from_id(user_profile.cidade) if user_profile.cidade else None
    state_name = get_state_name_from_id(user_profile.estado) if user_profile.estado else None

    # Esta linha agora usa a função CORRIGIDA
    cultivo_principal_name = get_product_name_from_id(
        user_profile.cultivo_principal, user_profile.cidade
    ) if user_profile.cultivo_principal else None

    context = {
        'profile': user_profile,
        'country_name': country_name,  # NOVO: Adiciona ao contexto
        'city_name': city_name,
        'state_name': state_name,
        'cultivo_principal_name': cultivo_principal_name,
    }
    return render(request, 'profile.html', context)


@login_required
def profile_edit(request):
    """Permite ao usuário editar o próprio perfil, lidando com o formulário dinâmico."""
    user_profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=user_profile)
        if form.is_valid():
            # Garante que os valores vindo dos selects (que são IDs) sejam salvos
            # Os campos 'cidade', 'estado' e 'cultivo_principal' são preenchidos
            # com os valores (IDs) dos selects do profile_edit.html.

            # RE-INSERIDO: Linha 'form.instance.pais = request.POST.get('pais', None)'
            form.instance.pais = request.POST.get('pais', None)

            form.instance.cidade = request.POST.get('cidade', None)
            form.instance.estado = request.POST.get('estado', None)
            form.instance.cultivo_principal = request.POST.get('cultivo_principal', None)

            form.save()
            messages.success(request, 'Perfil atualizado com sucesso!')
            return redirect('agro_app:profile')
        else:
            messages.error(request, 'Erro ao atualizar o perfil. Verifique os campos.')
    else:
        form = ProfileForm(instance=user_profile)

    # CORREÇÃO: Substituído .city por .cidade e .state por .estado
    city_name = get_city_name_from_id(user_profile.cidade) if user_profile.cidade else None
    state_name = get_state_name_from_id(user_profile.estado) if user_profile.estado else None

    context = {
        'form': form,
        'profile': user_profile,
        'city_name': city_name,
        'state_name': state_name,
    }
    return render(request, 'profile_edit.html', context)


# ------------------------------------------------------------------------------------------------------
# VIEWS DE API (IBGE E PRODUTO) - Necessárias para o funcionamento do profile_edit
# ------------------------------------------------------------------------------------------------------

def get_states(request):
    """Retorna a lista de estados do Brasil (IBGE) via AJAX (usada no profile_edit)."""
    try:
        url = "https://servicodados.ibge.gov.br/api/v1/localidades/estados?orderBy=nome"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        states_data = response.json()

        states_list = [{'id': state['id'], 'nome': state['nome']} for state in states_data]
        return JsonResponse(states_list, safe=False)
    except requests.RequestException as e:
        return JsonResponse({'error': f'Erro de conexão com IBGE: {e}'}, status=500)
    except Exception as e:
        return JsonResponse({'error': f'Erro inesperado: {e}'}, status=500)


def get_cities(request, state_id):
    """Retorna a lista de cidades de um estado (IBGE) via AJAX (usada no profile_edit)."""
    if not state_id: return JsonResponse([], safe=False)

    try:
        url = f"https://servicodados.ibge.gov.br/api/v1/localidades/estados/{state_id}/municipios?orderBy=nome"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        cities_data = response.json()

        cities_list = [{'id': city['id'], 'nome': city['nome']} for city in cities_data]
        return JsonResponse(cities_list, safe=False)
    except requests.RequestException as e:
        return JsonResponse({'error': f'Erro de conexão com IBGE: {e}'}, status=500)
    except Exception as e:
        return JsonResponse({'error': f'Erro inesperado: {e}'}, status=500)


def get_products_by_city_by_id(request, city_id):
    """
    [RESTURADA] API: Retorna a lista de produtos/cultivos associados a uma cidade.
    Esta view é mantida no agro_app, pois é utilizada para carregar dinamicamente
    o campo 'cultivo_principal' na edição de perfil.
    """
    if not city_id:
        return JsonResponse([], safe=False)

    try:
        products_data = data_service.get_products_for_city(city_id)
        # O info_app terá uma cópia dessa lógica, e isso está OK.
        return JsonResponse(products_data, safe=False)
    except Exception as e:
        return JsonResponse({'error': f'Erro ao buscar produtos no serviço de dados: {e}'}, status=500)