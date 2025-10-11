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
    Adiciona a lógica para salvar os IDs de pais, estado e cidade.
    """
    if request.method == 'POST':
        form = TerrenoForm(request.POST)
        if form.is_valid():
            terreno = form.save(commit=False)
            terreno.proprietario = request.user  # CORRIGIDO: O Terreno usa 'proprietario', não 'user'

            # CORREÇÃO CRÍTICA: Garante que os IDs de pais, estado e cidade
            # (selecionados dinamicamente via JavaScript/AJAX no frontend) sejam salvos manualmente.
            # Os nomes dos campos no modelo são 'pais', 'estado' e 'cidade'.
            terreno.pais = request.POST.get('pais', None)
            terreno.estado = request.POST.get('estado', None)
            terreno.cidade = request.POST.get('cidade', None)

            terreno.save()
            messages.success(request, f"Terreno '{terreno.nome}' cadastrado com sucesso!") # Usa 'nome', não 'name'
            # Redireciona de volta para o dashboard principal
            return redirect('agro_app:dashboard')
        else:
            # Em caso de falha, é melhor renderizar o dashboard novamente, injetando o form inválido.
            # Como a criação é feita via include (bloco5), voltamos ao dashboard com erro.
            messages.error(request, "Erro ao cadastrar terreno. Verifique os campos.")
            return redirect('agro_app:dashboard')

    # Acesso via GET deve redirecionar
    return redirect('agro_app:dashboard')


@login_required
def edit_terreno(request, pk):
    """
    Edita um terreno existente do usuário logado.
    Adiciona a lógica para salvar os IDs de pais, estado e cidade.
    """
    # Garante que só o usuário dono do terreno possa editá-lo
    # CORRIGIDO: O Terreno usa 'proprietario', não 'user'
    terreno = get_object_or_404(Terreno, pk=pk, proprietario=request.user)

    if request.method == 'POST':
        form = TerrenoForm(request.POST, instance=terreno)
        if form.is_valid():
            # CORREÇÃO CRÍTICA: Garante que os IDs de pais, estado e cidade sejam atualizados
            # a partir do request.POST antes de salvar.
            form.instance.pais = request.POST.get('pais', None)
            form.instance.estado = request.POST.get('estado', None)
            form.instance.cidade = request.POST.get('cidade', None)

            form.save()
            messages.success(request, f"Terreno '{terreno.nome}' atualizado com sucesso!") # Usa 'nome', não 'name'
            return redirect('agro_app:dashboard')
        else:
            messages.error(request, f"Erro ao editar terreno '{terreno.nome}'. Verifique os campos.") # Usa 'nome', não 'name'
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
    # CORRIGIDO: O Terreno usa 'proprietario', não 'user'
    terreno = get_object_or_404(Terreno, pk=pk, proprietario=request.user)

    if request.method == 'POST':
        terreno_name = terreno.nome # Usa 'nome', não 'name'
        terreno.delete()
        messages.success(request, f"Terreno '{terreno_name}' excluído com sucesso.")
        return redirect('agro_app:dashboard')

    # Acesso via GET deve redirecionar
    return redirect('agro_app:dashboard')