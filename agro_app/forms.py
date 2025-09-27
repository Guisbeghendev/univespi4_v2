from django import forms
from .models import Profile, Terreno, UNIT_CHOICES # Importa o novo modelo Terreno e as escolhas de Unidade


class ProfileForm(forms.ModelForm):
    # Lista estática de países
    COUNTRY_CHOICES = [
        ('Brasil', 'Brasil'),
        ('EUA', 'Estados Unidos'),
        ('Argentina', 'Argentina'),
        ('Outro', 'Outro')
    ]

    country = forms.ChoiceField(
        choices=COUNTRY_CHOICES,
        required=False,
        label='País',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    # Campos que se tornarão dropdowns dinâmicos
    state = forms.CharField(label='Estado', required=False)
    city = forms.CharField(label='Cidade', required=False)

    class Meta:
        model = Profile
        fields = ['first_name', 'last_name', 'country', 'state', 'city', 'birth_date', 'contact', 'cultivo_principal']
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
        }

# ==============================================================================
# NOVO: Formulário de Terreno (CORRIGIDO)
# ==============================================================================
class TerrenoForm(forms.ModelForm):
    """
    Formulário para criar e editar o modelo Terreno.
    """
    class Meta:
        model = Terreno
        # CORRIGIDO: 'size' mudado para 'area'
        fields = ['name', 'area', 'unit']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Lote Fundos'}),
            # CORRIGIDO: 'size' mudado para 'area'
            'area': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 15.5'}),
            'unit': forms.Select(choices=UNIT_CHOICES, attrs={'class': 'form-control'}),
        }
        labels = {
            'name': 'Nome do Terreno',
            # CORRIGIDO: 'size' mudado para 'area'
            'area': 'Tamanho',
            'unit': 'Unidade',
        }
