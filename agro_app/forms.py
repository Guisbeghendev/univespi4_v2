from django import forms
# ATUALIZAÇÃO: Adicionado PlanoPlantio
from .models import Profile, Terreno, UNIT_CHOICES, PlanoPlantio


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
# Formulário de Terreno
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


# ==============================================================================
# Formulário de Seleção de Terreno para o Plano de Cultivo (Mantido, mas não usado diretamente no fluxo atual)
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


# ==============================================================================
# NOVO: Formulário para o Modelo PlanoPlantio
# ==============================================================================
class PlanoPlantioForm(forms.ModelForm):
    """
    Formulário para salvar o Plano de Cultivo final.
    """
    # Campo para receber o ID do produto, usado para fins de validação e rastreio.
    cultivo_id = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = PlanoPlantio
        fields = [
            'nome_plantacao',
            'cultura',  # Nome da cultura (original)
            'terreno',
            # 'localizacao' e 'area' são preenchidos pela view/modelo
        ]

        widgets = {
            'nome_plantacao': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Safra Milho 2025'}),
            # Escondidos, pois são preenchidos na view/POST
            'terreno': forms.HiddenInput(),
            'cultura': forms.HiddenInput(),
        }

        labels = {
            'nome_plantacao': 'Nome do Plano de Cultivo',
        }

    # Remove os campos opcionais do modelo que não precisam ser exibidos no form
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # removemos os campos que serao preenchidos automaticamente na view
        if 'localizacao' in self.fields:
            del self.fields['localizacao']
        if 'area' in self.fields:
            del self.fields['area']