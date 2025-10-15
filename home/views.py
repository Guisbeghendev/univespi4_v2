from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from .forms import CustomUserCreationForm
from django.db import IntegrityError
import sys  # Importe o módulo sys para forçar a saída de log no WSGI


def index(request):
    """
    Renderiza a página inicial do site.
    """
    return render(request, 'index.html')


@require_http_methods(["GET", "POST"])
def signup_view(request):
    # Função auxiliar para escrever no log do Apache via sys.stderr
    def log_error(message):
        sys.stderr.write(f"[AGRODATA-DEBUG] {message}\n")

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)

        if form.is_valid():
            # 1. VALIDAÇÃO OK. Tenta salvar (BLOCO QUE DEVE EXECUTAR O LOG)
            try:
                # Tenta salvar o usuário (disparando o signal)
                user = form.save()

                # LOG DE SUCESSO
                log_error(f"SUCESSO: Usuário '{user.username}' cadastrado. Redirecionando...")
                return redirect(reverse('login'))

            except IntegrityError as e:
                # LOG DE ERRO CRÍTICO DE BANCO DE DADOS
                log_error(f"ERRO CRÍTICO (IntegrityError): Falha ao salvar no DB. Detalhe: {e}")

            except Exception as e:
                # LOG DE ERRO GERAL (Geralmente no signal de Profile)
                log_error(f"ERRO CRÍTICO (Geral): Falha no processo de salvamento. Detalhe: {e}")

            # Se o try/except capturar um erro
            log_error("Tentativa de cadastro falhou no TRY/EXCEPT. Formulário reexibido.")

        else:
            # 2. SE A VALIDAÇÃO FALHAR (O PONTO DE FALHA MAIS PROVÁVEL)
            # Imprime os erros do formulário diretamente no log do Apache
            log_error("--- ERRO DE VALIDAÇÃO DO FORMULÁRIO ---")
            log_error(str(form.errors))
            log_error("---------------------------------------")

    else:
        form = CustomUserCreationForm()

    return render(request, 'registration/signup.html', {'form': form})