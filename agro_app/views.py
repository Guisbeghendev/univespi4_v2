import requests
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Profile
from .forms import ProfileForm
from fichatecnica_app import data_service


# ### CONTROLE DE VISIBILIDADE ###
### esse deve ficar sempre no topo!
# ------------------------------------------------------------------------------------------------------
@login_required
def dashboard(request):
    # Lógica ADICIONAL para o Bloco 1 (Perfil/Status):
    user_profile, created = Profile.objects.get_or_create(user=request.user)

    # Busca os nomes da Cidade e Estado para passar para o contexto (usado no bloco1.html)
    city_name = get_city_name_from_id(user_profile.city) if user_profile.city else None
    state_name = get_state_name_from_id(user_profile.state) if user_profile.state else None

    # ----------------------------------------------------------------------
    # CÓDIGO DO CLIMA
    # ----------------------------------------------------------------------
    weather_data = None
    if city_name:
        # Chama a função de serviço (agora completa)
        weather_data = data_service.get_weather_data(city_name)

    # DEBUG GARANTIDO: Imprime o que o serviço de dados retornou no terminal
    print(f"DEBUG CLIMA RETORNO FINAL: {weather_data} para a cidade: {city_name}")

    # ----------------------------------------------------------------------

    # Dicionário simples para controle ON/OFF de cada bloco
    # Você pode definir aqui quais cards aparecem ou não.
    controle_de_visibilidade = {
        'bloco2': True,  # Clima
        'bloco3': True,  # filtro_agro
        'bloco4': False,  #
        'bloco5': False,  #
        'bloco6': False,  #
        'bloco7': False,  #
    }

    # Combina o controle de visibilidade com os dados do perfil.
    context = {
        'visibilidade': controle_de_visibilidade,
        'city_name': city_name,
        'state_name': state_name,
        'profile': user_profile,
        'clima': weather_data,  # Passa os dados para o template
    }

    # Renderiza com o novo contexto
    return render(request, 'dashboard.html', context)


# ------------------------------------------------------------------------------------------------------
### OUTROS CONTEUDOS ABAIXO!
# ------------------------------------------------------------------------------------------------------

# Funções Auxiliares de Tradução (Necessárias para o profile.html e bloco1.html)
# ------------------------------------------------------------------------------------------------------
def get_city_name_from_id(city_id):
    """Busca o nome da cidade a partir da ID do IBGE. Usa a API do IBGE."""
    if not city_id:
        return None
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
    if not state_id:
        return None
    try:
        url = f"https://servicodados.ibge.gov.br/api/v1/localidades/estados/{state_id}"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        return data.get('sigla')
    except (requests.RequestException, json.JSONDecodeError):
        return None


def get_product_name_from_id(product_id):
    """Busca o nome do produto a partir da ID, chamando o serviço de dados."""
    if not product_id:
        return None

    # CÓDIGO ATUALIZADO: Busca o nome do produto no serviço de dados real
    # Assume que data_service.get_product_name_by_id(id) retorna o nome do produto ou None
    return data_service.get_product_name_by_id(product_id)


# Views de Perfil
# ------------------------------------------------------------------------------------------------------

@login_required
def profile(request):
    """Exibe o perfil do usuário, buscando nomes de cidade e cultivo por ID."""
    # Garante que o perfil exista (se criado for True, o Profile.objects.get_or_create já salva)
    user_profile, created = Profile.objects.get_or_create(user=request.user)

    # Converte IDs armazenadas no Profile para Nomes para exibição no template
    city_name = get_city_name_from_id(user_profile.city) if user_profile.city else None
    state_name = get_state_name_from_id(user_profile.state) if user_profile.state else None
    cultivo_principal_name = get_product_name_from_id(
        user_profile.cultivo_principal) if user_profile.cultivo_principal else None

    context = {
        'profile': user_profile,
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
        # Instancia o formulário com os dados POST e a instância do perfil
        form = ProfileForm(request.POST, instance=user_profile)
        if form.is_valid():
            # Garante que os valores vindo dos selects (que são IDs) sejam salvos
            form.instance.city = request.POST.get('city', None)
            form.instance.state = request.POST.get('state', None)
            form.instance.cultivo_principal = request.POST.get('cultivo_principal', None)

            form.save()
            messages.success(request, 'Perfil atualizado com sucesso!')
            return redirect('agro_app:profile')
        else:
            messages.error(request, 'Erro ao atualizar o perfil. Verifique os campos.')
    else:
        # GET request: Preenche o formulário com a instância atual
        form = ProfileForm(instance=user_profile)

    # Converte IDs para Nomes para que o JS possa pré-preencher a localização correta na tela
    city_name = get_city_name_from_id(user_profile.city) if user_profile.city else None
    state_name = get_state_name_from_id(user_profile.state) if user_profile.state else None

    context = {
        'form': form,
        'profile': user_profile,  # Passado para o JS usar os valores iniciais
        'city_name': city_name,
        'state_name': state_name,
    }
    return render(request, 'profile_edit.html', context)


# Views de API do IBGE e Produto
# ------------------------------------------------------------------------------------------------------

def get_states(request):
    """Retorna a lista de estados do Brasil (IBGE) via AJAX."""
    try:
        # API do IBGE: Retorna todos os estados
        url = "https://servicodados.ibge.gov.br/api/v1/localidades/estados?orderBy=nome"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        states_data = response.json()

        # Filtra apenas ID e Nome
        states_list = [{'id': state['id'], 'nome': state['nome']} for state in states_data]
        return JsonResponse(states_list, safe=False)
    except requests.RequestException as e:
        return JsonResponse({'error': f'Erro de conexão com IBGE: {e}'}, status=500)
    except Exception as e:
        return JsonResponse({'error': f'Erro inesperado: {e}'}, status=500)


def get_cities(request, state_id):
    """Retorna a lista de cidades de um estado (IBGE) via AJAX."""
    if not state_id:
        return JsonResponse([], safe=False)

    try:
        # API do IBGE: Retorna municípios de um estado específico
        url = f"https://servicodados.ibge.gov.br/api/v1/localidades/estados/{state_id}/municipios?orderBy=nome"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        cities_data = response.json()

        # Filtra apenas ID e Nome
        cities_list = [{'id': city['id'], 'nome': city['nome']} for city in cities_data]
        return JsonResponse(cities_list, safe=False)
    except requests.RequestException as e:
        return JsonResponse({'error': f'Erro de conexão com IBGE: {e}'}, status=500)
    except Exception as e:
        return JsonResponse({'error': f'Erro inesperado: {e}'}, status=500)


def get_products_by_city_by_id(request, city_id):
    """
    Retorna a lista de produtos/cultivos associados a uma cidade, chamando o serviço de dados.
    """
    if not city_id:
        return JsonResponse([], safe=False)

    # ATUALIZADO: Chama a função real para buscar produtos
    try:
        products_data = data_service.get_products_for_city(city_id)

        # Assume-se que a função retorna uma lista de dicionários com 'id' e 'nome'
        return JsonResponse(products_data, safe=False)

    except Exception as e:
        return JsonResponse({'error': f'Erro ao buscar produtos no serviço de dados: {e}'}, status=500)