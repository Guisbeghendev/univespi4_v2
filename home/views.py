from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from .forms import CustomUserCreationForm
from django.db import IntegrityError  # Necessário para debug de erro de DB/Signal


def index(request):
    """
    Renderiza a página inicial do site.
    """
    # Usando 'index.html' conforme a sua nota
    return render(request, 'index.html')


@require_http_methods(["GET", "POST"])
def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():

            # --- BLOCO DE DEBUG PARA SALVAMENTO ---
            try:
                # Tenta salvar o usuário (disparando o signal)
                user = form.save()

                # Se o salvamento for bem-sucedido, redireciona
                # Esta mensagem aparece no console do servidor
                print(f"SUCESSO: Usuário '{user.username}' cadastrado. Redirecionando...")
                return redirect(reverse('login'))

            except IntegrityError as e:
                # Captura erros de banco de dados (ex: NOT NULL constraint falha no Profile)
                print("ERRO CRÍTICO (IntegrityError): Falha ao salvar no banco de dados. Detalhe:", e)

            except Exception as e:
                # Captura qualquer outro erro, geralmente do signal de Profile
                print("ERRO CRÍTICO (Geral): Falha no processo de salvamento. Detalhe:", e)

            # Se o try/except capturar um erro, o código continua e o formulário é reexibido.
            print("Tentativa de cadastro falhou. Favor verificar o log para o erro.")
            # --- FIM DO BLOCO DE DEBUG ---

    else:
        form = CustomUserCreationForm()

    return render(request, 'registration/signup.html', {'form': form})