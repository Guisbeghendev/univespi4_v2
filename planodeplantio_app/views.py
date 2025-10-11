from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db.models import Sum
from django.utils import timezone  # Importado para a função concluir_etapa

# Importa modelos e formulários
from agro_app.models import Terreno, PlanoPlantio, EtapaPlantio, Produto
from .forms import PlanoPlantioForm, EtapaPlantioForm


# --- VISTAS AUXILIARES / API ---

@login_required
def api_terrenos(request):
    """
    API: Retorna a lista de terrenos pertencentes ao usuário logado em formato JSON.
    CORREÇÃO CRÍTICA: Sincroniza os nomes dos campos com o modelo Terreno (area_total, unidade_area).
    Remove o campo inexistente 'cultura_atual'.
    """
    try:
        # 1. Busca todos os terrenos onde o proprietário é o usuário logado.
        terrenos = Terreno.objects.filter(proprietario=request.user).order_by('nome')

        # 2. Serializa os dados.
        terrenos_data = []
        for terreno in terrenos:
            terrenos_data.append({
                'id': str(terreno.id),  # Converte o ID (geralmente UUID) para string para JSON
                'nome': terreno.nome,
                # CORRIGIDO: Substitui 'area_hectares' pelos campos atuais do modelo Terreno
                'area_total': str(terreno.area_total),
                'unidade_area': terreno.unidade_area,
                'cidade': terreno.cidade,
                # REMOVIDO: 'cultura_atual' não existe mais no modelo Terreno
            })

        # 3. Retorna a resposta JSON.
        return JsonResponse({'success': True, 'terrenos': terrenos_data})

    except Exception as e:
        # Tratamento de erro robusto.
        print(f"ERRO CRÍTICO na api_terrenos: {e}")
        # Retorna um 500, mas com uma mensagem JSON clara para o frontend
        return JsonResponse({'success': False, 'error': f"Erro no servidor: {str(e)}"}, status=500)


# --- VISTAS DO CRUD DE PLANO DE PLANTIO ---

@login_required
def listar_planos(request):
    """
    Exibe a lista de todos os planos de plantio criados pelo usuário logado.
    """
    planos = PlanoPlantio.objects.filter(proprietario=request.user).order_by('-data_inicio')
    context = {
        'planos': planos
    }
    return render(request, 'planodeplantio_app/listar_planos.html', context)


@login_required
def criar_plano_plantio(request):
    """
    Cria um novo Plano de Plantio. O campo proprietario é preenchido automaticamente.
    """
    if request.method == 'POST':
        # Instancia o formulário, passando o usuário para o __init__ para filtrar terrenos
        form = PlanoPlantioForm(request.POST, user=request.user)
        if form.is_valid():
            plano = form.save(commit=False)
            plano.proprietario = request.user
            plano.status = 'RASCUNHO'  # Status inicial
            plano.save()
            messages.success(request, f"Plano '{plano.nome}' criado com sucesso! Adicione as etapas agora.")
            # Redireciona para a página de detalhes para que o usuário adicione etapas
            return redirect('plano:detalhe_plano', plano_id=plano.id)
        else:
            messages.error(request, "Houve um erro no preenchimento do formulário.")
    else:
        # GET: Instancia o formulário, passando o usuário para filtragem de terrenos
        form = PlanoPlantioForm(user=request.user)

    context = {
        'form': form,
        'title': 'Criar Novo Plano de Plantio'
    }
    # Renderiza o formulário de criação
    return render(request, 'planodeplantio_app/criar_plano.html', context)


@login_required
def detalhe_plano(request, plano_id):
    """
    Exibe os detalhes de um plano específico, incluindo suas etapas.
    Permite visualizar e gerenciar as etapas.
    """
    # Garante que o plano pertence ao usuário logado
    plano = get_object_or_404(PlanoPlantio, id=plano_id, proprietario=request.user)

    # Busca todas as etapas relacionadas ao plano
    etapas = EtapaPlantio.objects.filter(plano=plano).order_by('data_prevista')

    # Calcula o custo total estimado do plano
    custo_total = etapas.aggregate(Sum('custo_total'))['custo_total__sum'] or 0

    context = {
        'plano': plano,
        'etapas': etapas,
        'custo_total': custo_total,
        'title': f"Detalhes do Plano: {plano.nome}"
    }
    return render(request, 'planodeplantio_app/detalhe_plano.html', context)


@login_required
def editar_plano(request, plano_id):
    """
    Edita os detalhes de um Plano de Plantio existente.
    """
    # Garante que o plano existe e pertence ao usuário
    plano = get_object_or_404(PlanoPlantio, id=plano_id, proprietario=request.user)

    if request.method == 'POST':
        # Passa a instância e o usuário para o formulário
        form = PlanoPlantioForm(request.POST, instance=plano, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f"Plano '{plano.nome}' atualizado com sucesso!")
            return redirect('plano:detalhe_plano', plano_id=plano.id)
        else:
            messages.error(request, "Houve um erro na atualização do plano.")
    else:
        # GET: Popula o formulário com os dados existentes
        form = PlanoPlantioForm(instance=plano, user=request.user)

    context = {
        'form': form,
        'plano': plano,
        'title': f'Editar Plano: {plano.nome}'
    }
    return render(request, 'planodeplantio_app/editar_plano.html', context)


@login_required
@require_POST
def excluir_plano(request, plano_id):
    """
    Exclui um Plano de Plantio. Requer método POST.
    """
    plano = get_object_or_404(PlanoPlantio, id=plano_id, proprietario=request.user)
    plano.delete()
    messages.warning(request, f"Plano '{plano.nome}' e todas as suas etapas foram excluídos.")
    return redirect('plano:listar_planos')


# --- VISTAS DO CRUD DE ETAPAS ---

@login_required
def criar_etapa(request, plano_id):
    """
    Cria uma nova Etapa de Plantio associada a um plano específico.
    """
    # Garante que o plano existe e pertence ao usuário
    plano = get_object_or_404(PlanoPlantio, id=plano_id, proprietario=request.user)

    if request.method == 'POST':
        form = EtapaPlantioForm(request.POST)
        if form.is_valid():
            etapa = form.save(commit=False)
            etapa.plano = plano
            etapa.save()
            messages.success(request, "Etapa adicionada com sucesso!")
            return redirect('plano:detalhe_plano', plano_id=plano.id)
        else:
            messages.error(request, "Houve um erro no preenchimento da etapa.")
    else:
        form = EtapaPlantioForm()

    context = {
        'form': form,
        'plano': plano,
        'title': f'Adicionar Etapa ao Plano: {plano.nome}'
    }
    return render(request, 'planodeplantio_app/criar_etapa.html', context)


@login_required
def editar_etapa(request, etapa_id):
    """
    Edita uma Etapa de Plantio existente.
    """
    # Garante que a etapa e seu plano pertencem ao usuário logado
    etapa = get_object_or_404(EtapaPlantio, id=etapa_id, plano__proprietario=request.user)

    if request.method == 'POST':
        form = EtapaPlantioForm(request.POST, instance=etapa)
        if form.is_valid():
            form.save()
            messages.success(request, f"Etapa '{etapa.nome}' atualizada.")
            return redirect('plano:detalhe_plano', plano_id=etapa.plano.id)
        else:
            messages.error(request, "Houve um erro na atualização da etapa.")
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
def excluir_etapa(request, etapa_id):
    """
    Exclui uma Etapa de Plantio. Requer método POST.
    """
    # Garante que a etapa e seu plano pertencem ao usuário logado
    etapa = get_object_or_404(EtapaPlantio, id=etapa_id, plano__proprietario=request.user)
    plano_id = etapa.plano.id  # Salva o ID do plano para redirecionar
    etapa.delete()
    messages.warning(request, f"Etapa '{etapa.nome}' excluída do plano.")
    return redirect('plano:detalhe_plano', plano_id=plano_id)


@login_required
@require_POST
def concluir_etapa(request, etapa_id):
    """
    Marca uma Etapa de Plantio como concluída. Requer método POST.
    """
    # Garante que a etapa e seu plano pertencem ao usuário logado
    etapa = get_object_or_404(EtapaPlantio, id=etapa_id, plano__proprietario=request.user)

    etapa.concluida = True
    etapa.data_conclusao = timezone.now().date()  # Marca a conclusão com a data atual
    etapa.save()

    messages.success(request, f"Etapa '{etapa.nome}' marcada como CONCLUÍDA.")
    # Redireciona de volta para os detalhes do plano
    return redirect('plano:detalhe_plano', plano_id=etapa.plano.id)
