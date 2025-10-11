from django import forms
# CORRIGIDO: Importa os modelos e constantes do aplicativo principal (agro_app)
# Assumindo que Terreno, UNIT_CHOICES e PlanoPlantio estão disponíveis para importação
# O Terreno está definido no models.py que você enviou.
from agro_app.models import Terreno, UNIT_CHOICES, PlanoPlantio  # Ajuste a importação se Terreno estiver em outro lugar


# ==============================================================================
# Formulário de Terreno
# ==============================================================================
class TerrenoForm(forms.ModelForm):
    """
    Formulário para criar e editar o modelo Terreno, corrigido para usar os nomes de campo
    exatos do modelo: 'nome', 'estado', 'cidade'.
    (O campo 'area_hectares' foi removido para resolver o FieldError.)
    """
    # Sobrescrevemos os campos 'estado' e 'cidade' para adicionar widgets customizados
    # e IDs, mas mantemos os nomes de campo exatos para que o ModelForm os reconheça.
    estado = forms.CharField(
        label='Estado',
        required=True,
        # O ID deve refletir o nome do campo no modelo para consistência: 'id_estado'
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_estado', 'data-url-cities': '/api/cities/'})
    )

    cidade = forms.CharField(
        label='Cidade',
        required=True,
        # O ID deve refletir o nome do campo no modelo para consistência: 'id_cidade'
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_cidade'})
    )

    # O campo 'unit' (unidade de medida) foi removido daqui porque não existe no modelo Terreno.
    # Caso você precise dele, adicione-o no modelo Terreno.

    class Meta:
        model = Terreno
        # CAMPOS CORRIGIDOS para corresponder exatamente ao modelo Terreno, excluindo 'area_hectares':
        fields = ['nome', 'estado', 'cidade']

        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Lote Fundos'}),
            # 'area_hectares' foi removido
        }
        labels = {
            'nome': 'Nome do Terreno',
            # 'area_hectares' foi removido
            # 'estado' e 'cidade' já têm labels definidos acima
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
            # CORRIGIDO: O Terreno se relaciona ao User pelo campo 'proprietario'
            self.fields['terreno'].queryset = Terreno.objects.filter(proprietario=user)
