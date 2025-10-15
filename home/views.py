from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from .forms import CustomUserCreationForm
from django.db import IntegrityError  # Importa exceção de DB


@require_http_methods(["GET", "POST"])
def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                # 1. Tenta salvar o usuário (isso dispara o signal do models.py)
                user = form.save()

                # 2. Se o salvamento for bem-sucedido, redireciona
                print(f"USUÁRIO '{user.username}' CADASTRADO COM SUCESSO. Redirecionando...")
                return redirect(reverse('login'))

            except IntegrityError as e:
                # 3. SE FALHAR (Erro de banco de dados/Integridade)
                print(f"ERRO CRÍTICO (IntegrityError): {e}")

            except Exception as e:
                # 4. SE FALHAR (Qualquer outro erro, como falha no signal)
                print(f"ERRO CRÍTICO (Geral) DURANTE SALVAMENTO: {e}")

            # Se ocorrer um erro no try/except, a página é recarregada
            print("Tentativa de cadastro falhou. Exibindo formulário novamente.")

    else:
        form = CustomUserCreationForm()

    return render(request, 'registration/signup.html', {'form': form})