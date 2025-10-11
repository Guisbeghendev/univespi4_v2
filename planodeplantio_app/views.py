import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Prefetch
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST

# Importa modelos de Terreno e Plano
from agro_app.models import Terreno, Produto
from agro_app.models import PlanoPlantio, EtapaPlantio, Terreno, Produto

# Importa Formulários
from .forms import PlanoPlantioForm, EtapaPlantioForm

# Importa serviços do data_service (fichatecnica_app)
# Assumindo que Terreno e Produto podem ser importados aqui se não estiverem no .models
# Se Terreno/Produto estiverem no agro_app.models, a importação no topo está correta.
from fichatecnica_app.data_service import get_city_name_by_id, get_products_for_city, get_ficha_tecnica


@login_required
def listar_planos(request):
    """
    Lista todos os planos de plantio criados pelo usuário, com otimização
    para carregar terrenos e etapas em uma única consulta.
    """
    # Usamos Prefetch para buscar as etapas de cada plano de forma eficiente
    planos = PlanoPlantio.objects.filter(
        terreno__proprietario=request.user
    ).select_related('terreno').prefetch_related(
        Prefetch('etapas', queryset=EtapaPlantio.objects.order_by('data_prevista'))
    ).order_by('-data_inicio')  # Ordenando por data de início, para manter a ordem cronológica de criação

    planos_processados = []
    for plano in planos:
        # A localização da cidade agora é buscada via IBGE, se o código estiver disponível
        try:
            full_name, _ = get_city_name_by_id(plano.terreno.cidade)
            localizacao = full_name if full_name else plano.terreno.cidade
        except Exception:
            localizacao = f"Cód. IBGE: {plano.terreno.cidade}"

        # Determina o status do plano
        hoje = datetime.date.today()
        proxima_etapa = None
        status = 'Planejado'

        etapas_do_plano = plano.etapas.all()

        etapas_concluidas = 0
        etapas_totais = len(etapas_do_plano)

        for etapa in etapas_do_plano:
            # Os campos no modelo são data_conclusao e data_prevista
            if etapa.concluida:  # Usando o campo concluida (boolean)
                etapas_concluidas += 1
            # Se não está concluída, verificamos a próxima etapa agendada
            elif etapa.data_prevista >= hoje and not proxima_etapa:
                proxima_etapa = etapa
                status = 'Agendado'
                if etapa.data_prevista == hoje:
                    status = f"Em Andamento ({etapa.nome})"
                    break  # Encontramos a etapa de hoje, podemos parar

        # Ajuste de status após a iteração
        if etapas_totais > 0 and etapas_concluidas == etapas_totais:
            status = 'Concluído'
        # Se for rascunho (status inicial do modelo), refletimos isso
        elif plano.status == 'RASCUNHO':
            status = 'Rascunho (Não Iniciado)'
        elif plano.status == 'CANCELADO':
            status = 'Cancelado'

        progresso = f"{etapas_concluidas}/{etapas_totais}" if etapas_totais > 0 else "0/0"

        planos_processados.append({
            'id': str(plano.id),  # Converte UUID para string para ser usado em URLs
            'nome': plano.nome,
            'terreno_nome': plano.terreno.nome,
            'terreno_localizacao': localizacao,
            'produto': plano.produto.nome if plano.produto else 'A definir',
            'status': status,
            'progresso': progresso,
            'proxima_etapa': proxima_etapa.nome if proxima_etapa else 'N/A',
            'proxima_data': proxima_etapa.data_prevista if proxima_etapa else None
        })

    context = {
        'planos': planos_processados,
        'title': 'Meus Planos de Plantio'
    }
    return render(request, 'planodeplantio_app/listar_planos.html', context)


@login_required
def criar_plano(request):
    """
    Permite ao usuário criar um novo Plano de Plantio.
    CORRIGIDO: O nome da função está alinhado com o urls.py
    """
    # Filtra terrenos que pertencem ao usuário logado
    terrenos_do_usuario = Terreno.objects.filter(proprietario=request.user)

    if request.method == 'POST':
        # Passa o queryset filtrado para o formulário
        form = PlanoPlantioForm(request.POST, terrenos_queryset=terrenos_do_usuario)
        if form.is_valid():
            plano = form.save(commit=False)
            plano.proprietario = request.user
            plano.save()
            messages.success(request, f"Plano '{plano.nome}' criado com sucesso!")
            # Redireciona para o detalhe ou lista
            return redirect('plano:detalhe_plano', plano_id=plano.pk)  # CORRIGIDO: Usando 'plano_id'
        else:
            messages.error(request, "Erro ao criar plano. Verifique o formulário.")
    else:
        form = PlanoPlantioForm(terrenos_queryset=terrenos_do_usuario)

    context = {
        'form': form,
        'terrenos': terrenos_do_usuario,
        'title': 'Criar Novo Plano de Plantio'
    }
    return render(request, 'planodeplantio_app/criar_plano.html', context)


@login_required
def detalhe_plano(request, plano_id):
    """
    Exibe os detalhes de um Plano de Plantio específico, incluindo etapas e ficha técnica.
    CORRIGIDO: Parâmetro pk alterado para plano_id (UUID)
    """
    plano = get_object_or_404(
        PlanoPlantio.objects.select_related('terreno'),
        pk=plano_id,  # Usamos pk para buscar pelo UUID
        terreno__proprietario=request.user
    )

    etapas = plano.etapas.all().order_by('data_prevista')

    # Busca a Ficha Técnica e Clima
    city_id = plano.terreno.cidade

    ficha_tecnica = {}
    produto_alvo = plano.produto.nome if plano.produto else None

    if produto_alvo:
        try:
            ficha_tecnica = get_ficha_tecnica(produto_alvo, city_id)
        except Exception as e:
            print(f"Erro ao buscar Ficha Técnica/Clima: {e}")
            messages.warning(request,
                             "Não foi possível carregar a Ficha Técnica e os dados de Clima. Tente novamente mais tarde.")
    else:
        messages.info(request, "O Plano de Plantio não possui um produto alvo definido para buscar a Ficha Técnica.")

    context = {
        'plano': plano,
        'etapas': etapas,
        'ficha_tecnica': ficha_tecnica or {
            'erro': 'Dados da Ficha Técnica e Clima Indisponíveis ou Produto não definido.'},
        'title': f'Detalhes do Plano: {plano.nome}',
        'form_etapa': EtapaPlantioForm(initial={'plano': plano}),
    }
    return render(request, 'planodeplantio_app/detalhe_plano.html', context)


@login_required
def editar_plano(request, plano_id):
    """
    Permite a edição de um Plano de Plantio.
    CORRIGIDO: Parâmetro pk alterado para plano_id (UUID)
    """
    plano = get_object_or_404(
        PlanoPlantio.objects.select_related('terreno'),
        pk=plano_id,  # Usamos pk para buscar pelo UUID
        terreno__proprietario=request.user
    )
    terrenos_do_usuario = Terreno.objects.filter(proprietario=request.user)

    if request.method == 'POST':
        form = PlanoPlantioForm(request.POST, instance=plano, terrenos_queryset=terrenos_do_usuario)
        if form.is_valid():
            form.save()
            messages.success(request, f"Plano '{plano.nome}' atualizado.")
            return redirect('plano:detalhe_plano', plano_id=plano.pk)  # CORRIGIDO: Usando 'plano_id'
        else:
            messages.error(request, "Erro ao editar plano. Verifique o formulário.")
    else:
        form = PlanoPlantioForm(instance=plano, terrenos_queryset=terrenos_do_usuario)

    context = {
        'form': form,
        'plano': plano,
        'title': f'Editar Plano: {plano.nome}'
    }
    return render(request, 'planodeplantio_app/editar_plano.html', context)


@login_required
@require_POST
def deletar_plano(request, plano_id):
    """
    Deleta um Plano de Plantio.
    CORRIGIDO: Parâmetro pk alterado para plano_id (UUID)
    CORRIGIDO: Alinhado com o nome de rota 'deletar_plano'
    """
    plano = get_object_or_404(PlanoPlantio, pk=plano_id,
                              terreno__proprietario=request.user)  # Usamos pk para buscar pelo UUID

    plano_nome = plano.nome
    plano.delete()
    messages.success(request, f"Plano '{plano_nome}' excluído com sucesso.")
    return redirect('plano:listar_planos')


# --- Funções de Etapas ---

@login_required
def adicionar_etapa(request, plano_id):
    """
    Adiciona uma nova etapa a um plano de plantio.
    CORRIGIDO: Parâmetro plano_pk alterado para plano_id (UUID)
    """
    plano = get_object_or_404(PlanoPlantio, pk=plano_id, proprietario=request.user)

    if request.method == 'POST':
        form = EtapaPlantioForm(request.POST)
        if form.is_valid():
            etapa = form.save(commit=False)
            etapa.plano = plano
            etapa.save()
            messages.success(request, f"Etapa '{etapa.nome}' adicionada ao plano.")
            return redirect('plano:detalhe_plano', plano_id=plano_id)  # CORRIGIDO: Usando 'plano_id'
        else:
            messages.error(request, "Erro ao adicionar etapa. Verifique os dados.")

    return redirect('plano:detalhe_plano', plano_id=plano_id)  # CORRIGIDO: Usando 'plano_id'


@login_required
def editar_etapa(request, plano_id, etapa_id):
    """
    Edita uma etapa específica.
    CORRIGIDO: Parâmetro etapa_pk alterado para etapa_id (UUID) e adicionado plano_id (UUID)
    """
    etapa = get_object_or_404(
        EtapaPlantio.objects.select_related('plano__terreno'),
        pk=etapa_id,  # Usamos pk para buscar pelo UUID
        plano__pk=plano_id,  # Garante que a etapa pertença ao plano correto
        plano__terreno__proprietario=request.user
    )

    if request.method == 'POST':
        form = EtapaPlantioForm(request.POST, instance=etapa)
        if form.is_valid():
            form.save()
            messages.success(request, f"Etapa '{etapa.nome}' atualizada.")
            return redirect('plano:detalhe_plano', plano_id=plano_id)  # CORRIGIDO: Usando 'plano_id'
        else:
            messages.error(request, "Erro ao editar etapa. Verifique os dados.")
    else:
        form = EtapaPlantioForm(instance=etapa)

    context = {
        'form': form,
        'etapa': etapa,
        'plano': etapa.plano,
        'title': f'Editar Etapa: {etapa.nome}'
    }
    return render(request, 'planodeplantio_app/editar_etapa.html', context)


@login_required
@require_POST
def deletar_etapa(request, plano_id, etapa_id):
    """
    Deleta uma etapa específica.
    CORRIGIDO: Parâmetro etapa_pk alterado para etapa_id (UUID) e adicionado plano_id (UUID)
    CORRIGIDO: Alinhado com o nome de rota 'deletar_etapa'
    """
    etapa = get_object_or_404(
        EtapaPlantio.objects.select_related('plano__terreno'),
        pk=etapa_id,  # Usamos pk para buscar pelo UUID
        plano__pk=plano_id,  # Garante que a etapa pertença ao plano correto
        plano__terreno__proprietario=request.user
    )

    etapa_nome = etapa.nome
    etapa.delete()
    messages.success(request, f"Etapa '{etapa_nome}' excluída.")
    return redirect('plano:detalhe_plano', plano_id=plano_id)  # CORRIGIDO: Usando 'plano_id'


@login_required
@require_POST
def concluir_etapa(request, plano_id, etapa_id):
    """
    Marca uma etapa como concluída. (Nova função)
    """
    etapa = get_object_or_404(
        EtapaPlantio.objects.select_related('plano__terreno'),
        pk=etapa_id,
        plano__pk=plano_id,
        plano__terreno__proprietario=request.user
    )

    if not etapa.concluida:
        etapa.concluida = True
        etapa.data_conclusao = datetime.date.today()
        etapa.save()
        messages.success(request, f"Etapa '{etapa.nome}' marcada como concluída.")
    else:
        messages.info(request, f"Etapa '{etapa.nome}' já estava concluída.")

    return redirect('plano:detalhe_plano', plano_id=plano_id)


# --- ROTAS DE API (AJAX) ---

# Função para buscar lista de produtos por cidade (já existia no views.py anterior)
@login_required
def buscar_produtos_por_cidade(request, cidade_id):
    """
    Endpoint AJAX para buscar a lista de produtos disponíveis para uma cidade.
    Retorna JSON.
    """
    products = []
    try:
        # Busca a lista de produtos usando o serviço correto
        products = get_products_for_city(cidade_id)
        # Retorna uma lista de dicionários com 'id' (nome normalizado) e 'nome' (nome amigável)
    except Exception as e:
        print(f"Erro ao buscar produtos para cidade {cidade_id}: {e}")
        products = []

        # A resposta deve ser um dicionário que contém a lista de produtos
    return JsonResponse({'products': products})


# Função placeholder para API de terrenos (necessária para bloco7.html)
@login_required
def api_terrenos(request):
    """
    Endpoint AJAX para listar os terrenos do usuário, usado na dashboard (bloco7.html).
    Retorna JSON.
    """
    terrenos = Terreno.objects.filter(proprietario=request.user)

    terrenos_data = []
    for terreno in terrenos:
        full_name, _ = get_city_name_by_id(terreno.cidade)
        terrenos_data.append({
            'id': str(terreno.pk),
            'nome': terreno.nome,
            'area_total': str(terreno.area_total),
            'unidade_area': terreno.unidade_area,
            'localizacao': full_name if full_name else terreno.cidade,
            'cidade_id': terreno.cidade,
        })

    return JsonResponse({'terrenos': terrenos_data})
