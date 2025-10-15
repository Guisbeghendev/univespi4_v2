from django.contrib.auth.forms import UserCreationForm
from django import forms


class CustomUserCreationForm(UserCreationForm):
    # O UserCreationForm já trata dos campos username, password, password2

    class Meta(UserCreationForm.Meta):
        # A forma mais segura de listar os campos ao herdar
        fields = ('username', 'password', 'password2')

        labels = {
            'username': 'Nome de Usuário',
            # Deixe o label da senha FORA, pois ele é a causa do erro
            'password2': 'Confirme a Senha',
        }
        help_texts = {
            'username': 'Obrigatório. 150 caracteres ou menos. Apenas letras, dígitos e @/./+/-/_.',
        }