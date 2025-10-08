from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
# CORRIGIDO: Importa o modelo Terreno do aplicativo principal (agro_app)
from agro_app.models import Terreno
from .forms import TerrenoForm

@login_required
def create_terreno(request):
    """
    Cria um novo terreno associado ao usuário logado.
    """
    if request.method == 'POST':
        form = TerrenoForm(request.POST)
        if form.is_valid():
            terreno = form.save(commit=False)
            terreno.user = request.user
            terreno.save()
            messages.success(request, f"Terreno '{terreno.name}' cadastrado com sucesso!")
            # Redireciona de volta para o dashboard principal (onde o card é exibido)
            return redirect('agro_app:dashboard')
        else:
            # Se o form for inválido, redireciona de volta com uma mensagem de erro
            messages.error(request, "Erro ao cadastrar terreno. Verifique os campos.")
            # Note: Para mostrar erros de formulário em um redirect, você precisaria armazenar
            # os erros na sessão ou passar via query parameter. Por simplicidade, apenas redirecionamos.
            return redirect('agro_app:dashboard')

    # Acesso via GET deve redirecionar
    return redirect('agro_app:dashboard')


@login_required
def edit_terreno(request, pk):
    """
    Edita um terreno existente do usuário logado.
    """
    # Garante que só o usuário dono do terreno possa editá-lo
    terreno = get_object_or_404(Terreno, pk=pk, user=request.user)

    if request.method == 'POST':
        form = TerrenoForm(request.POST, instance=terreno)
        if form.is_valid():
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
