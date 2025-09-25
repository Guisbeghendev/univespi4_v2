from django.shortcuts import render, redirect
from .forms import CustomUserCreationForm  # <--- Importe seu novo formulário

def index(request):
    """
    Renderiza a página inicial do site.
    """
    return render(request, 'index.html')

def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST) # <--- Use o novo formulário
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = CustomUserCreationForm() # <--- Use o novo formulário
    return render(request, 'registration/signup.html', {'form': form})