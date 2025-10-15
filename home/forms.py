from django.contrib.auth.forms import UserCreationForm
from django import forms

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        labels = {
            'username': 'Nome de Usuário',
            # A linha 'password': 'Senha' foi removida.
            'password2': 'Confirme a Senha',
        }
        help_texts = {
            'username': 'Obrigatório. 150 caracteres ou menos. Apenas letras, dígitos e @/./+/-/_.',
        }