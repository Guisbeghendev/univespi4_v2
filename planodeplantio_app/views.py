from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib import messages
# IMPORTAÇÃO CORRETA DOS MODELOS DO SEU PROJETO (agro_app)
from agro_app.models import Terreno, PlanoPlantio, Produto
# Importa as funções do serviço de dados
from fichatecnica_app.data_service import get_products_for_city, get_ficha_tecnica
from django.db import IntegrityError
import json
from datetime import date
from decimal import Decimal

# IMPORTAÇÃO DA LÓGICA DE TRADUÇÃO (que está em agro_app.views)
# IMPORTANTE: Garanta que essas funções existam em agro_app.views
from agro_app.views import get_city_name_from_id, get_state_name_from_id


# ======================================================================
# FUNÇÃO AUXILIAR GLOBAL
# MOVIDA DO API_BUSCAR_FICHA PARA O TOPO
# ======================================================================
def convert_decimal_and_clean(obj):
    """Converte Decimal para str, None para string vazia, e limpa recursivamente."""
    if isinstance(obj, Decimal):
        return str(obj)
    if obj is None:
        return ""
    if isinstance(obj, dict):
        return {k: convert_decimal_and_clean(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [convert_decimal_and_clean(i) for i in obj]
    return obj


# ======================================================================


# ----------------------------------------------------------------------
# API DE TERRENOS
# ----------------------------------------------------------------------

@login_required
@require_http_methods(["GET"])
def api_terrenos(request):
    """
    API endpoint que retorna a lista de Terrenos do usuário,
    com os campos de Localização traduzidos (sem IDs IBGE).
    """
    try:
        user_terrenos = Terreno.objects.filter(proprietario=request.user).order_by('nome')

        terrenos_list = []
        for terreno in user_terrenos:
            # 1. TRADUZ OS IDs PARA NOMES LEGÍVEIS
            cidade_nome = get_city_name_from_id(terreno.cidade)
            estado_sigla = get_state_name_from_id(terreno.estado)

            terrenos_list.append({
                'id': terreno.id,
                'nome': terreno.nome,
                'area_total': str(terreno.area_total),
                'unidade_area': terreno.unidade_area,
                'cidade_id': terreno.cidade,
                'estado_id': terreno.estado,
                'cidade_nome': cidade_nome or 'N/A',
                'estado_sigla': estado_sigla or 'N/A',
                'localizacao_display': f"{cidade_nome or 'N/A'} / {estado_sigla or 'N/A'}"
            })

        return JsonResponse({'terrenos': terrenos_list}, status=200)

    except Exception as e:
        return JsonResponse({'error': f'Erro interno ao listar terrenos: {str(e)}'}, status=500)


# ----------------------------------------------------------------------
# WIZARD DE PLANO DE PLANTIO - PONTO DE INÍCIO
# ----------------------------------------------------------------------

@login_required
@require_http_methods(["GET"])
def iniciar_wizard(request):
    """
    Inicia um novo Plano de Plantio (RASCUNHO) e redireciona para a Etapa 1.
    """
    try:
        terreno_id = request.GET.get('terreno_id')

        if not terreno_id:
            messages.error(request, "Nenhum terreno selecionado para iniciar o plano.")
            # Redirecionamento corrigido
            return redirect('dashboard')

        terreno_selecionado = get_object_or_404(
            Terreno,
            pk=terreno_id,
            proprietario=request.user
        )

        # Cria um novo Plano de Plantio (RASCUNHO)
        novo_plano = PlanoPlantio.objects.create(
            proprietario=request.user,
            terreno=terreno_selecionado,
            nome=f"Plano em Rascunho para {terreno_selecionado.nome} ({date.today().strftime('%Y-%m')})",
            data_inicio=date.today(),
            status='RASCUNHO'
        )

        # Redireciona para a Etapa 1
        messages.success(request, f"Plano '{novo_plano.nome}' iniciado. Comece pela Etapa 1.")
        return redirect(reverse('plano:etapa1_plano', kwargs={'plano_id': novo_plano.pk}))

    except Terreno.DoesNotExist:
        messages.error(request, "Terreno inválido ou não encontrado.")
        # Redirecionamento corrigido
        return redirect('dashboard')
    except Exception as e:
        messages.error(request, f'Erro interno ao iniciar o Plano: {str(e)}')
        # Redirecionamento corrigido
        return redirect('dashboard')


# ----------------------------------------------------------------------
# WIZARD - ETAPA 1: SELEÇÃO DE CULTIVO (planoplantio.html)
# ----------------------------------------------------------------------

@login_required
@require_http_methods(["GET"])
def etapa1_plano(request, plano_id):
    """
    Renderiza o template para a Seleção de Produto.
    """
    plano = get_object_or_404(
        PlanoPlantio,
        pk=plano_id,
        proprietario=request.user
    )

    terreno = plano.terreno

    # --- INÍCIO DO DEBUG CRÍTICO ---
    cidade_id = terreno.cidade
    estado_id = terreno.estado

    # ESTA LINHA VAI PRO SEU CONSOLE/TERMINAL
    print(f"DEBUG: Terreno ID {terreno.pk} | Cidade ID: {cidade_id} | Estado ID: {estado_id}")

    # 1. TRADUÇÃO DOS IDS PARA NOMES LEGÍVEIS
    cidade_nome = get_city_name_from_id(cidade_id)
    estado_sigla = get_state_name_from_id(estado_id)
    # Usando N/A_CIDADE e N/A_ESTADO para facilitar o DEBUG no console:
    localizacao_display = f"{cidade_nome or 'N/A_CIDADE'} / {estado_sigla or 'N/A_ESTADO'}"

    # ESTA LINHA VAI PRO SEU CONSOLE/TERMINAL
    print(f"DEBUG: Localização Display (Resultado): {localizacao_display}")
    # --- FIM DO DEBUG CRÍTICO (Localização) ---

    cidade_ibge_id = terreno.cidade

    # =======================================================================
    # GARANTIR QUE A ID É UMA STRING
    # =======================================================================
    cidade_ibge_id_str = str(cidade_ibge_id)

    # Usa a ID convertida para string
    produtos_disponiveis = get_products_for_city(cidade_ibge_id_str)

    # PRECISO VER O CONTEÚDO DESTA LINHA!
    print(f"DEBUG: Produtos disponíveis: {produtos_disponiveis}")
    # =======================================================================

    context = {
        'plano': plano,
        'terreno': terreno,
        'produtos_disponiveis': produtos_disponiveis,
        # Mantém a ID original (terreno.cidade) para o JavaScript usar na busca da Ficha Técnica
        'cidade_ibge_id': terreno.cidade,
        'app_name': 'plano',
        # NOVO CAMPO DE CONTEXTO CORRIGIDO:
        'localizacao_display': localizacao_display
    }

    # CORREÇÃO: Usando o nome simples do arquivo
    return render(request, 'planoplantio.html', context)


@login_required
@require_http_methods(["GET"])
def api_buscar_ficha(request):
    """
    API para buscar os dados da Ficha Técnica (usada no planoplantio.html).
    CORREÇÃO: Estrutura o resultado plano do data_service em seções para o frontend.
    """
    produto_nome = request.GET.get('produto_nome')
    cidade_id = request.GET.get('cidade_id')

    if not produto_nome or not cidade_id:
        return JsonResponse({'error': 'Parâmetros produto_nome e cidade_id são obrigatórios.'}, status=400)

    # Lógica de fallback/conversão para garantir que a ID passada seja compatível
    cidade_id_para_busca = str(cidade_id)

    # O get_ficha_tecnica retorna um dicionário plano (ex: {'produto': 'Uva', 'tipo_solo': 'Drenado', ...})
    ficha_data_plana = get_ficha_tecnica(produto_nome, cidade_id_para_busca)

    if ficha_data_plana is None:
        return JsonResponse({'error': 'Ficha Técnica não encontrada para o produto/cidade ou erro interno.'},
                            status=404)

    # ====================================================================
    # CORREÇÃO CRÍTICA: ESTRUTURAR O DICIONÁRIO PLANO EM SEÇÕES
    # ====================================================================

    # Cria a estrutura aninhada que o JS espera
    ficha_data_estruturada = {
        "Informações Básicas": {
            "Produto": ficha_data_plana.get('produto'),
            "Localização": ficha_data_plana.get('city_name'),
            "Ciclo de Vida (dias)": ficha_data_plana.get('ciclo_vida_dias'),
            "Tipo de Solo": ficha_data_plana.get('tipo_solo'),
            "pH do Solo Ideal": ficha_data_plana.get('ph_solo_ideal'),
            "Status Sustentabilidade": ficha_data_plana.get('status_sustentabilidade'),
        },
        "Dados Climáticos": {
            "Temperatura Ideal (°C)": ficha_data_plana.get('temperatura_ideal_c'),
            "Precipitação Mínima (mm)": ficha_data_plana.get('precipitacao_min_mm'),
            "Plantio Sugerido": ficha_data_plana.get('periodo_plantio_sugerido'),
            "Colheita Prevista": ficha_data_plana.get('tempo_colheita_meses'),
            "Condição Ideal Colheita": ficha_data_plana.get('condicao_ideal_colheita'),
            "Necessidade Hídrica Total (mm)": ficha_data_plana.get('necessidade_hidrica_total_mm'),
        },
        "Produtividade e Riscos": {
            "Produtividade Média Local": ficha_data_plana.get('produtividade_media_kg_ha'),
            "Vulnerabilidade a Pragas": ficha_data_plana.get('vulnerabilidade_pragas'),
            "Fertilizante Essencial": ficha_data_plana.get('fertilizante_essencial'),
            "Cotação (PMA - R$)": ficha_data_plana.get('cotacao_pma_rs'),
        },
        "Clima Local Atual": {
            "Temperatura Atual": ficha_data_plana.get('clima_atual_temperatura'),
            "Condição Atual": ficha_data_plana.get('clima_atual_condicao'),
            "Umidade Atual": ficha_data_plana.get('clima_atual_umidade'),
            "Vento Atual": ficha_data_plana.get('clima_atual_vento'),
        }
    }

    # --------------------------------------------------------------------

    # Aplica a conversão/limpeza na estrutura FINAL
    ficha_data_final = convert_decimal_and_clean(ficha_data_estruturada)

    # CORREÇÃO CRÍTICA: Adicionar json_dumps_params={'ensure_ascii': False} para resolver a codificação (acentos)
    return JsonResponse(ficha_data_final, status=200, safe=False, json_dumps_params={'ensure_ascii': False})


@login_required
@require_http_methods(["POST"])
def api_salvar_etapa1(request, plano_id):
    """
    API para salvar a Etapa 1 (Seleção de Produto APENAS) e redirecionar para a página final.
    """
    plano = get_object_or_404(
        PlanoPlantio,
        pk=plano_id,
        proprietario=request.user
    )

    try:
        data = json.loads(request.body)
        produto_nome = data.get('produto_nome')

        if not produto_nome:
            return JsonResponse({'error': 'A seleção do Produto é obrigatória.'}, status=400)

        # 1. Tenta buscar (case-insensitive) e CRIA o objeto Produto se ele não existir
        try:
            produto_obj, created = Produto.objects.get_or_create(
                nome__iexact=produto_nome,
                defaults={'nome': produto_nome}
            )
        except Exception as e:
            return JsonResponse({'error': f"Erro ao processar o Produto no catálogo: {str(e)}"}, status=500)

        # 2. Atualiza o Plano
        plano.produto = produto_obj

        if plano.data_inicio is None:
            plano.data_inicio = date.today()

        plano.data_colheita_prevista = None
        plano.status = 'ANDAMENTO'

        plano.save()

        return JsonResponse({
            'message': 'Cultivo salvo com sucesso.',
            'plano_id': plano.pk,
            # Redireciona para a View de visualização final
            'next_url': reverse('plano:planofinal_plano', kwargs={'plano_id': plano.pk})
        }, status=200)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Payload JSON inválido.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Erro ao salvar Etapa 1: {str(e)}'}, status=500)


# ----------------------------------------------------------------------
# FASE 2: VIEW FINAL DE VISUALIZAÇÃO (planofinal.html)
# CORRIGIDO: Agora estrutura a ficha_data
# ----------------------------------------------------------------------

@login_required
@require_http_methods(["GET"])
def planofinal_plano(request, plano_id):
    """
    Renderiza a página final de visualização do plano salvo (planofinal.html).
    CORRIGIDO: Estrutura os dados da Ficha Técnica e garante que a localização seja passada.
    """
    # 1. Busca o Plano e verifica a posse
    plano = get_object_or_404(
        PlanoPlantio,
        pk=plano_id,
        proprietario=request.user
    )

    if not plano.produto:
        messages.error(request, "Plano incompleto. Retorne à Etapa 1 para selecionar o produto.")
        return redirect(reverse('plano:etapa1_plano', kwargs={'plano_id': plano.pk}))

    # 2. Busca os dados da Ficha Técnica para exibição
    cidade_ibge_id = plano.terreno.cidade
    produto_nome = plano.produto.nome

    # Lógica de conversão para garantir que a ID seja string para o serviço
    cidade_id_para_busca = str(cidade_ibge_id)

    # Obtém o dicionário PLANO
    ficha_data_plana = get_ficha_tecnica(produto_nome, cidade_id_para_busca)

    # 3. TRADUÇÃO DOS IDS PARA NOMES LEGÍVEIS PARA EXIBIÇÃO NO TEMPLATE
    cidade_nome = get_city_name_from_id(plano.terreno.cidade)
    estado_sigla = get_state_name_from_id(plano.terreno.estado)
    localizacao_display = f"{cidade_nome or 'N/A'} / {estado_sigla or 'N/A'}"

    # ====================================================================
    # CORREÇÃO CRÍTICA AQUI: ESTRUTURAR A FICHA TÉCNICA
    # ====================================================================
    if ficha_data_plana is None:
        ficha_data_final = {}
        messages.warning(request, "Ficha Técnica não encontrada para o produto/cidade.")
    else:
        # Cria a estrutura aninhada (COPIADA DA api_buscar_ficha)
        ficha_data_estruturada = {
            "Informações Básicas": {
                "Produto": ficha_data_plana.get('produto'),
                "Localização": ficha_data_plana.get('city_name'),
                "Ciclo de Vida (dias)": ficha_data_plana.get('ciclo_vida_dias'),
                "Tipo de Solo": ficha_data_plana.get('tipo_solo'),
                "pH do Solo Ideal": ficha_data_plana.get('ph_solo_ideal'),
                "Status Sustentabilidade": ficha_data_plana.get('status_sustentabilidade'),
            },
            "Dados Climáticos": {
                "Temperatura Ideal (°C)": ficha_data_plana.get('temperatura_ideal_c'),
                "Precipitação Mínima (mm)": ficha_data_plana.get('precipitacao_min_mm'),
                "Plantio Sugerido": ficha_data_plana.get('periodo_plantio_sugerido'),
                "Colheita Prevista": ficha_data_plana.get('tempo_colheita_meses'),
                "Condição Ideal Colheita": ficha_data_plana.get('condicao_ideal_colheita'),
                "Necessidade Hídrica Total (mm)": ficha_data_plana.get('necessidade_hidrica_total_mm'),
            },
            "Produtividade e Riscos": {
                "Produtividade Média Local": ficha_data_plana.get('produtividade_media_kg_ha'),
                "Vulnerabilidade a Pragas": ficha_data_plana.get('vulnerabilidade_pragas'),
                "Fertilizante Essencial": ficha_data_plana.get('fertilizante_essencial'),
                "Cotação (PMA - R$)": ficha_data_plana.get('cotacao_pma_rs'),
            },
            "Clima Local Atual": {
                "Temperatura Atual": ficha_data_plana.get('clima_atual_temperatura'),
                "Condição Atual": ficha_data_plana.get('clima_atual_condicao'),
                "Umidade Atual": ficha_data_plana.get('clima_atual_umidade'),
                "Vento Atual": ficha_data_plana.get('clima_atual_vento'),
            }
        }

        # Garante a serialização (Decimal para str)
        ficha_data_final = convert_decimal_and_clean(ficha_data_estruturada)
    # ====================================================================

    context = {
        'plano': plano,
        'terreno': plano.terreno,
        'ficha_data': ficha_data_final,  # PASSA O DICIONÁRIO ESTRUTURADO
        'app_name': 'plano',
        'localizacao_display': localizacao_display
    }

    return render(request, 'planofinal.html', context)