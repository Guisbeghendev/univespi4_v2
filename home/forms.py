from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.forms import PasswordInput  # Adicionar esta importação


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        fields = ('username', 'password', 'password2')  # Manter esta linha

        labels = {
            'username': 'Nome de Usuário',
            # 'password' (Senha) continua fora para evitar a falha de renderização.
            'password2': 'Confirme a Senha',
        }
        help_texts = {
            'username': 'Obrigatório. 150 caracteres ou menos. Apenas letras, dígitos e @/./+/-/_.',
        }

        # NOVO: FORÇA O TIPO DE INPUT PARA PASSWORD
        widgets = {
            # O nome do campo no UserCreationForm é 'password'
            'password': PasswordInput(),
            # Garantir que password2 também use o widget correto, embora já estivesse funcionando
            'password2': PasswordInput(),
        }