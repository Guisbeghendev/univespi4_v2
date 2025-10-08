from django import forms
# CORRIGIDO: Importa os modelos e constantes do aplicativo principal (agro_app)
from agro_app.models import Terreno, UNIT_CHOICES, PlanoPlantio


# ==============================================================================
# Formulário de Terreno
# ==============================================================================
class TerrenoForm(forms.ModelForm):
    """
    Formulário para criar e editar o modelo Terreno.
    """

    class Meta:
        model = Terreno
        fields = ['name', 'area', 'unit']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Lote Fundos'}),
            'area': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 15.5'}),
            'unit': forms.Select(choices=UNIT_CHOICES, attrs={'class': 'form-control'}),
        }
        labels = {
            'name': 'Nome do Terreno',
            'area': 'Tamanho',
            'unit': 'Unidade',
        }


# ==============================================================================
# Formulário de Seleção de Terreno para o Plano de Cultivo
# ==============================================================================
class PlanoCultivoSelectTerrenoForm(forms.Form):
    """
    Formulário para a primeira etapa do Plano de Cultivo: selecionar um Terreno.
    """
    terreno = forms.ModelChoiceField(
        queryset=Terreno.objects.none(),  # Queryset inicial vazio
        label="Selecione o Terreno para o Plano",
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user is not None:
            # Filtra os terrenos apenas para o usuário atual
            self.fields['terreno'].queryset = Terreno.objects.filter(user=user)
