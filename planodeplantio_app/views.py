import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Prefetch
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST

# Importa modelos de Terreno e Plano
from agro_app.models import Terreno, Produto
from agro_app.models import PlanoPlantio, EtapaPlantio

# Importa Formulários (Garantindo que a importação venha do próprio app)
from .forms import PlanoPlantioForm, EtapaPlantioForm

# Importa serviços do data_service (fichatecnica_app)
from fichatecnica_app.data_service import get_city_name_by_id, get_products_for_city, get_ficha_tecnica


@login_required
def listar_planos(request):
    """
    Lista todos os planos de plantio criados pelo usuário, com otimização
    para carregar terrenos e etapas em uma única consulta.
    """
    # Usamos Prefetch para buscar as etapas de cada plano de forma eficiente
    planos = PlanoPlantio.objects.filter(
        proprietario=request.user
    ).select_related('terreno', 'produto').prefetch_related(  # Adicionado 'produto' no select_related
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

        # O status inicial é o do modelo, a menos que as etapas provem o contrário
        status_display = plano.get_status_display()

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
                # Verifica se há uma etapa agendada para hoje
                if etapa.data_prevista == hoje and plano.status == 'EM_ANDAMENTO':
                    status_display = f"Em Andamento (Hoje: {etapa.nome})"
                    break  # Encontramos a etapa de hoje, podemos parar
                elif plano.status == 'PLANEJADO':
                    status_display = 'Planejado'

        # Ajuste de status após a iteração
        if etapas_totais > 0 and etapas_concluidas == etapas_totais and plano.status == 'EM_ANDAMENTO':
            status_display = 'Concluído'

        # Priorização de status do modelo para rascunho/cancelado
        if plano.status == 'RASCUNHO':
            status_display = 'Rascunho'
        elif plano.status == 'CANCELADO':
            status_display = 'Cancelado'
        elif plano.status == 'PLANEJADO' and proxima_etapa:
            status_display = f'Planejado (Próx: {proxima_etapa.data_prevista})'
        elif plano.status == 'EM_ANDAMENTO' and not proxima_etapa:
            status_display = 'Em Andamento (Sem próxima etapa)'

        progresso = f"{etapas_concluidas}/{etapas_totais}" if etapas_totais > 0 else "0/0"

        planos_processados.append({
            'id': str(plano.id),  # Converte UUID para string para ser usado em URLs
            'nome': plano.nome,
            'terreno_nome': plano.terreno.nome,
            'terreno_localizacao': localizacao,
            'produto': plano.produto.nome if plano.produto else 'A definir',
            'status': status_display,  # Usa o status dinâmico calculado
            'progresso': progresso,
            'proxima_etapa': proxima_etapa.nome if proxima_etapa else 'N/A',
            'proxima_data': proxima_etapa.data_prevista if proxima_etapa else None
        })

    context = {
        'planos': planos_processados,
        'title': 'Meus Planos de Plantio'
    }
    return render(request, 'planodeplantio_app/listar_planos.html', context)


# --- Funções do Wizard de Criação (3 Etapas) ---

@login_required
def iniciar_wizard(request):
    """
    Etapa 1 do Wizard (Ponto de Entrada):
    Recebe o terreno_id via GET (do dashboard) e redireciona para a seleção de produto.
    Se não houver ID, redireciona para o dashboard ou lista.
    """
    terreno_id = request.GET.get('terreno_id')
    if terreno_id:
        try:
            # Garante que o terreno existe e pertence ao usuário
            Terreno.objects.get(pk=terreno_id, proprietario=request.user)
            return redirect('plano:selecao_produto', terreno_id=terreno_id)
        except Terreno.DoesNotExist:
            messages.error(request, "Terreno inválido ou não pertence ao usuário.")

    # Se o fluxo for interrompido ou não houver ID, volta para o dashboard
    messages.info(request, "Selecione um terreno para iniciar o plano de plantio.")
    return redirect('agro_app:dashboard')


@login_required
def selecao_produto(request, terreno_id):
    """
    Etapa 2 do Wizard: Seleção de produto.
    Permite a escolha da cultura com base na localização do terreno.
    """
    terreno_obj = get_object_or_404(Terreno, pk=terreno_id, proprietario=request.user)

    if request.method == 'POST':
        produto_id = request.POST.get('produto_id')
        if produto_id:
            try:
                # O Produto não precisa ser filtrado por proprietário, pois é um catálogo global
                Produto.objects.get(pk=produto_id)

                # Redireciona para a etapa final, passando ambos os IDs via GET
                return redirect('plano:criar_plano_plantio',
                                terreno_id=terreno_obj.pk, produto_id=produto_id)
            except Produto.DoesNotExist:
                messages.error(request, "Produto selecionado inválido.")
        else:
            messages.error(request, "Por favor, selecione um produto.")

    # GET: Prepara a lista de produtos disponíveis para a cidade do terreno
    produtos_disponiveis = []
    try:
        produtos_disponiveis = get_products_for_city(terreno_obj.cidade)
    except Exception as e:
        print(f"Erro ao carregar produtos para {terreno_obj.cidade}: {e}")
        messages.warning(request, "Não foi possível carregar a lista de produtos baseada na localização.")

    context = {
        'terreno_obj': terreno_obj,
        'produtos_disponiveis': produtos_disponiveis,
        'title': 'Seleção de Cultura'
    }
    # Assumindo que o template `selecao_produto.html` existe para esta etapa
    return render(request, 'planodeplantio_app/selecao_produto.html', context)


@login_required
def criar_plano_plantio(request):
    """
    Etapa 3 do Wizard (Finalização e Criação Definitiva):
    Renderiza o formulário final (GET) ou salva o plano (POST).
    """
    if request.method == 'POST':
        # 1. POST (Submissão final do formulário)

        # O formulário é inicializado com o usuário para filtrar Terreno/Produto
        form = PlanoPlantioForm(request.POST, user=request.user)

        if form.is_valid():
            plano = form.save(commit=False)
            plano.proprietario = request.user
            plano.save()
            messages.success(request, f"Plano '{plano.nome}' criado com sucesso!")
            return redirect('plano:detalhe_plano', plano_id=plano.pk)
        else:
            messages.error(request, "Erro ao finalizar plano. Verifique os campos.")

            # Se o POST falhar, precisamos remontar o contexto para re-renderizar o template
            terreno_id = request.POST.get('terreno')
            produto_id = request.POST.get('produto')

            try:
                terreno_obj = Terreno.objects.get(pk=terreno_id, proprietario=request.user)
                produto_obj = Produto.objects.get(pk=produto_id)
            except (Terreno.DoesNotExist, Produto.DoesNotExist, TypeError):
                messages.error(request, "Terreno ou Produto inválido na submissão.")
                return redirect('agro_app:dashboard')

            context = {
                'form': form,
                'terreno_obj': terreno_obj,
                'produto_obj': produto_obj,
                'title': 'Finalizar Novo Plano',
            }
            return render(request, 'planodeplantio_app/plano_plantio_form.html', context)

    else:
        # 2. GET (Renderiza o formulário de finalização)
        terreno_id = request.GET.get('terreno_id')
        produto_id = request.GET.get('produto_id')

        if not terreno_id or not produto_id:
            messages.error(request, "Dados iniciais do plano ausentes. Inicie o wizard novamente.")
            return redirect('agro_app:dashboard')

        try:
            terreno_obj = get_object_or_404(Terreno, pk=terreno_id, proprietario=request.user)
            produto_obj = get_object_or_404(Produto, pk=produto_id)
        except Exception:
            messages.error(request, "Terreno ou Produto inválido.")
            return redirect('agro_app:dashboard')

        # Inicializa o form com os valores já conhecidos
        initial_data = {
            'terreno': terreno_obj,
            'produto': produto_obj,
            # Pode inicializar o nome automaticamente, se desejado, ex: f"Plano {produto_obj.nome} em {terreno_obj.nome}"
        }

        form = PlanoPlantioForm(initial=initial_data, user=request.user)

        context = {
            'form': form,
            'terreno_obj': terreno_obj,
            'produto_obj': produto_obj,
            'title': 'Finalizar Novo Plano',
        }
        # Renderiza o template que está em planodeplantio_app/plano_plantio_form.html
        return render(request, 'planodeplantio_app/plano_plantio_form.html', context)


# --- Funções de CRUD e Detalhes ---

@login_required
def detalhe_plano(request, plano_id):
    """
    Exibe os detalhes de um Plano de Plantio específico, incluindo etapas e ficha técnica.
    """
    plano = get_object_or_404(
        PlanoPlantio.objects.select_related('terreno', 'produto'),
        pk=plano_id,  # Usamos pk para buscar pelo UUID
        proprietario=request.user  # Garante que o plano pertence ao usuário
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
            # Print para debug no servidor
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
    """
    plano = get_object_or_404(
        PlanoPlantio.objects.select_related('terreno'),
        pk=plano_id,  # Usamos pk para buscar pelo UUID
        proprietario=request.user
    )

    if request.method == 'POST':
        # Passa o usuário para filtrar os Terrenos disponíveis
        form = PlanoPlantioForm(request.POST, instance=plano, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f"Plano '{plano.nome}' atualizado.")
            return redirect('plano:detalhe_plano', plano_id=plano.pk)
        else:
            messages.error(request, "Erro ao editar plano. Verifique o formulário.")
    else:
        # Passa o usuário para filtrar os Terrenos disponíveis
        form = PlanoPlantioForm(instance=plano, user=request.user)

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
    """
    plano = get_object_or_404(PlanoPlantio, pk=plano_id,
                              proprietario=request.user)  # Usamos pk para buscar pelo UUID

    plano_nome = plano.nome
    plano.delete()
    messages.success(request, f"Plano '{plano_nome}' excluído com sucesso.")
    return redirect('plano:listar_planos')


# --- Funções de Etapas ---

@login_required
def adicionar_etapa(request, plano_id):
    """
    Adiciona uma nova etapa a um plano de plantio.
    """
    # Garante que o usuário é o proprietário do plano
    plano = get_object_or_404(
        PlanoPlantio.objects.select_related('terreno'),
        pk=plano_id,
        proprietario=request.user
    )

    if request.method == 'POST':
        form = EtapaPlantioForm(request.POST)
        if form.is_valid():
            etapa = form.save(commit=False)
            etapa.plano = plano
            etapa.save()
            messages.success(request, f"Etapa '{etapa.nome}' adicionada ao plano.")
            return redirect('plano:detalhe_plano', plano_id=plano_id)
        else:
            # Repassa a mensagem de erro específica do formulário
            messages.error(request, "Erro ao adicionar etapa. Verifique os dados.")

    # Redireciona de volta para a página de detalhes em caso de GET ou erro no POST
    return redirect('plano:detalhe_plano', plano_id=plano_id)


@login_required
def editar_etapa(request, plano_id, etapa_id):
    """
    Edita uma etapa específica.
    """
    etapa = get_object_or_404(
        EtapaPlantio.objects.select_related('plano'),
        pk=etapa_id,  # Usamos pk para buscar pelo UUID
        plano__pk=plano_id,  # Garante que a etapa pertença ao plano correto
        plano__proprietario=request.user
    )

    if request.method == 'POST':
        form = EtapaPlantioForm(request.POST, instance=etapa)
        if form.is_valid():
            form.save()
            messages.success(request, f"Etapa '{etapa.nome}' atualizada.")
            return redirect('plano:detalhe_plano', plano_id=plano_id)
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
    # Renderiza um template específico para edição da etapa (será criado depois)
    return render(request, 'planodeplantio_app/editar_etapa.html', context)


@login_required
@require_POST
def deletar_etapa(request, plano_id, etapa_id):
    """
    Deleta uma etapa específica.
    """
    etapa = get_object_or_404(
        EtapaPlantio.objects.select_related('plano'),
        pk=etapa_id,  # Usamos pk para buscar pelo UUID
        plano__pk=plano_id,  # Garante que a etapa pertença ao plano correto
        plano__proprietario=request.user
    )

    etapa_nome = etapa.nome
    etapa.delete()
    messages.success(request, f"Etapa '{etapa_nome}' excluída.")
    return redirect('plano:detalhe_plano', plano_id=plano_id)


@login_required
@require_POST
def concluir_etapa(request, plano_id, etapa_id):
    """
    Marca uma etapa como concluída.
    """
    etapa = get_object_or_404(
        EtapaPlantio.objects.select_related('plano'),
        pk=etapa_id,
        plano__pk=plano_id,
        plano__proprietario=request.user
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
        # O serviço deve retornar uma lista de dicionários com 'id' (nome normalizado) e 'nome' (nome amigável)
    except Exception as e:
        print(f"Erro ao buscar produtos para cidade {cidade_id}: {e}")
        products = []

    return JsonResponse({'products': products})


@login_required
def api_terrenos(request):
    """
    Endpoint AJAX para listar os terrenos do usuário, usado na dashboard (bloco7.html).
    Retorna JSON.
    """
    try:
        # Otimiza a consulta inicial
        terrenos = Terreno.objects.filter(proprietario=request.user).order_by('nome')

        terrenos_data = []
        for terreno in terrenos:
            # Váriavel padrão em caso de falha da API
            localizacao = f"Cód. IBGE: {terreno.cidade}"

            try:
                # Tenta buscar o nome completo da cidade via API
                full_name, _ = get_city_name_by_id(terreno.cidade)
                if full_name:
                    localizacao = full_name
            except Exception as e:
                # Em caso de falha da API, imprime no console do servidor e usa o valor padrão
                print(f"Erro ao buscar nome da cidade {terreno.cidade} via IBGE: {e}")

            terrenos_data.append({
                'id': str(terreno.pk),
                'nome': terreno.nome,
                # CORREÇÃO CRÍTICA: Usando 'area_total' conforme a nossa conversa anterior (o modelo tem esse campo)
                # O campo 'area_hectares' estava causando o AttributeError.
                'area_total': str(terreno.area_total),
                'unidade_area': 'ha',
                # Usando o valor formatado ou do modelo, conforme a ficha técnica (era 'unidade_area')
                'localizacao': localizacao,
                'cidade_id': terreno.cidade,
            })

        # Retorna a lista de terrenos formatada
        return JsonResponse({'terrenos': terrenos_data}, status=200)

    except Exception as e:
        # Se falhar em qualquer etapa, retorna um erro 500 para o frontend.
        print(f"Erro CRÍTICO no endpoint api_terrenos: {e}")
        return JsonResponse({'error': 'Erro crítico na API ao listar terrenos.'}, status=500)
