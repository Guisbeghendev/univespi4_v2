from django import forms
from agro_app.models import Terreno
# from agro_app.models import UNIT_CHOICES
# Importação mantida, se for usada em outro lugar
# from agro_app.forms import PlanoCultivoSelectTerrenoForm


# ==============================================================================
# NOVAS CONSTANTES: Unidades de Medida para ÁREA (Apenas as solicitadas)
# ==============================================================================
AREA_UNIT_CHOICES = [
    ('M2', 'Metro Quadrado (m²)'),
    ('HA', 'Hectare (ha)'),
    ('ALQ', 'Alqueire'), # Se necessário detalhar, use ALQ_SP, ALQ_MG, etc.
]


# ==============================================================================
# Formulário de Terreno
# ==============================================================================
class TerrenoForm(forms.ModelForm):
    """
    Formulário para criar e editar o modelo Terreno, corrigido para usar
    somente as unidades de área.
    """
    # Lista estática de países
    COUNTRY_CHOICES = [
        ('Brasil', 'Brasil'),
        ('EUA', 'Estados Unidos'),
        ('Argentina', 'Argentina'),
        ('Outro', 'Outro')
    ]

    # Campo: País
    pais = forms.ChoiceField(
        choices=COUNTRY_CHOICES,
        required=False,
        label='País',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    # Sobrescrevemos os campos de localização
    estado = forms.CharField(label='Estado', required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Selecione um estado'}))
    cidade = forms.CharField(label='Cidade', required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Selecione uma cidade'}))

    class Meta:
        model = Terreno
        fields = ['nome', 'pais', 'estado', 'cidade', 'area_total', 'unidade_area']

        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Lote Fundos'}),
            'area_total': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 15.5'}),
            # CORREÇÃO CRÍTICA: Usando AREA_UNIT_CHOICES em vez de UNIT_CHOICES
            'unidade_area': forms.Select(choices=AREA_UNIT_CHOICES, attrs={'class': 'form-control'}),
        }
        labels = {
            'nome': 'Nome do Terreno',
            'area_total': 'Tamanho (Área)',
            'unidade_area': 'Unidade de Medida',
        }