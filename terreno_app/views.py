from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
# Importa o modelo Terreno do aplicativo principal (agro_app)
from agro_app.models import Terreno
from .forms import TerrenoForm
# CORREÇÃO DEFINITIVA: Importa a função do local correto, conforme arquivo data_service.py
from fichatecnica_app.data_service import get_city_name_by_id


@login_required
def listar_terrenos(request):
    """
    Exibe a lista de todos os terrenos do usuário, usando o serviço real para buscar o nome da cidade.
    """
    terrenos = Terreno.objects.filter(proprietario=request.user).order_by('nome')

    terrenos_processados = []
    for terreno in terrenos:
        # Localização - Chama o serviço real para buscar o nome da cidade (IBGE)
        try:
            # A função retorna (nome_completo, nome_normalizado). Pegamos apenas o nome completo.
            full_name, _ = get_city_name_by_id(terreno.cidade)
            # Usa o nome completo retornado pela API. Se a API retornar None, usa o código IBGE como fallback.
            nome_cidade = full_name if full_name else f"Cód. IBGE: {terreno.cidade}"
        except Exception:
            # Em caso de falha de conexão/serviço, exibe o código IBGE como fallback
            nome_cidade = f"Cód. IBGE: {terreno.cidade}"

        # Área - Formata a área para exibição (ex: "10,00 HA")
        area_formatada = f"{terreno.area_total:.2f} {terreno.unidade_area}"

        cultivo_atual_display = 'Não definido'

        terrenos_processados.append({
            'id': terreno.id,
            'nome': terreno.nome,
            'area_display': area_formatada,
            'localizacao_display': nome_cidade,
            'cultivo_display': cultivo_atual_display
        })

    context = {
        'terrenos': terrenos_processados,
        'title': 'Meus Terrenos Cadastrados'
    }
    return render(request, 'terreno_app/listar_terrenos.html', context)


@login_required
def create_terreno(request):
    """
    Cria um novo terreno associado ao usuário logado.
    """
    if request.method == 'POST':
        form = TerrenoForm(request.POST)
        if form.is_valid():
            terreno = form.save(commit=False)
            terreno.proprietario = request.user

            terreno.pais = request.POST.get('pais', None)
            terreno.estado = request.POST.get('estado', None)
            terreno.cidade = request.POST.get('cidade', None)

            terreno.save()
            messages.success(request, f"Terreno '{terreno.nome}' cadastrado com sucesso!")
            return redirect('agro_app:dashboard')
        else:
            messages.error(request, "Erro ao cadastrar terreno. Verifique os campos.")
            return redirect('agro_app:dashboard')

    return redirect('agro_app:dashboard')


@login_required
def edit_terreno(request, pk):
    """
    Edita um terreno existente do usuário logado.
    """
    terreno = get_object_or_404(Terreno, pk=pk, proprietario=request.user)

    if request.method == 'POST':
        form = TerrenoForm(request.POST, instance=terreno)
        if form.is_valid():
            form.instance.pais = request.POST.get('pais', None)
            form.instance.estado = request.POST.get('estado', None)
            form.instance.cidade = request.POST.get('cidade', None)

            form.save()
            messages.success(request, f"Terreno '{terreno.nome}' atualizado com sucesso!")
            return redirect('agro_app:dashboard')
        else:
            messages.error(request, f"Erro ao editar terreno '{terreno.nome}'. Verifique os campos.")
    else:
        form = TerrenoForm(instance=terreno)

    context = {
        'form': form,
        'terreno': terreno,
    }
    return render(request, 'edit_terreno.html', context)


@login_required
def delete_terreno(request, pk):
    """
    Exclui um terreno existente do usuário logado.
    """
    terreno = get_object_or_404(Terreno, pk=pk, proprietario=request.user)

    if request.method == 'POST':
        terreno_name = terreno.nome
        terreno.delete()
        messages.success(request, f"Terreno '{terreno_name}' excluído com sucesso.")
        return redirect('agro_app:dashboard')

    return redirect('agro_app:dashboard')
