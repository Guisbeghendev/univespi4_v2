from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
# Importa o modelo Terreno do aplicativo principal (agro_app)
from agro_app.models import Terreno
from .forms import TerrenoForm

@login_required
def create_terreno(request):
    """
    Cria um novo terreno associado ao usuário logado.
    Adiciona a lógica para salvar os IDs de estado e cidade do IBGE.
    """
    if request.method == 'POST':
        form = TerrenoForm(request.POST)
        if form.is_valid():
            terreno = form.save(commit=False)
            terreno.user = request.user

            # CORREÇÃO CRÍTICA: Garante que os IDs de estado e cidade (selecionados dinamicamente
            # via JavaScript/AJAX no frontend) sejam salvos manualmente.
            terreno.state = request.POST.get('state', None)
            terreno.city = request.POST.get('city', None)

            terreno.save()
            messages.success(request, f"Terreno '{terreno.name}' cadastrado com sucesso!")
            # Redireciona de volta para o dashboard principal (onde o card é exibido)
            return redirect('agro_app:dashboard')
        else:
            # Se o form for inválido, redireciona de volta com uma mensagem de erro
            messages.error(request, "Erro ao cadastrar terreno. Verifique os campos.")
            # Para o POST falho, é melhor manter o redirect para evitar reenvio do formulário.
            return redirect('agro_app:dashboard')

    # Acesso via GET deve redirecionar
    return redirect('agro_app:dashboard')


@login_required
def edit_terreno(request, pk):
    """
    Edita um terreno existente do usuário logado.
    Adiciona a lógica para salvar os IDs de estado e cidade do IBGE.
    """
    # Garante que só o usuário dono do terreno possa editá-lo
    terreno = get_object_or_404(Terreno, pk=pk, user=request.user)

    if request.method == 'POST':
        form = TerrenoForm(request.POST, instance=terreno)
        if form.is_valid():
            # CORREÇÃO CRÍTICA: Garante que os IDs de estado e cidade sejam atualizados
            # a partir do request.POST antes de salvar.
            form.instance.state = request.POST.get('state', None)
            form.instance.city = request.POST.get('city', None)

            form.save()
            messages.success(request, f"Terreno '{terreno.name}' atualizado com sucesso!")
            return redirect('agro_app:dashboard')
        else:
            messages.error(request, f"Erro ao editar terreno '{terreno.name}'. Verifique os campos.")
    else:
        form = TerrenoForm(instance=terreno)

    # Renderiza o template de edição
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
    # Garante que só o usuário dono do terreno possa excluí-lo
    terreno = get_object_or_404(Terreno, pk=pk, user=request.user)

    if request.method == 'POST':
        terreno_name = terreno.name
        terreno.delete()
        messages.success(request, f"Terreno '{terreno_name}' excluído com sucesso.")
        return redirect('agro_app:dashboard')

    # Acesso via GET deve redirecionar
    return redirect('agro_app:dashboard')
