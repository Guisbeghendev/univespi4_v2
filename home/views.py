from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from .forms import CustomUserCreationForm


def index(request):
    """
    Renderiza a página inicial do site.
    """
    # Como seu template está em home/templates/index.html sem subpasta 'home',
    # o caminho tem que ser só 'index.html' para evitar TemplateDoesNotExist
    return render(request, 'index.html')


@require_http_methods(["GET", "POST"])
def signup_view(request):
    """
    View para cadastro de usuário usando CustomUserCreationForm.
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(reverse('login'))
    else:
        form = CustomUserCreationForm()

    return render(request, 'registration/signup.html', {'form': form})
