from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.forms import PasswordInput


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        # CORREÇÃO: UserCreationForm usa 'password1' e 'password2'
        fields = ('username', 'password1', 'password2')

        labels = {
            'username': 'Nome de Usuário',
            # CORREÇÃO: Definindo o label para o campo 'password1'
            'password1': 'Senha',
            'password2': 'Confirme a Senha',
        }
        help_texts = {
            'username': 'Obrigatório. 150 caracteres ou menos. Apenas letras, dígitos e @/./+/-/_.',
        }

        widgets = {
            # CORREÇÃO: O widget deve ser aplicado ao campo 'password1'
            'password1': PasswordInput(),
            'password2': PasswordInput(),
        }