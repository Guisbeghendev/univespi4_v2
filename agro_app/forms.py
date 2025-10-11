from django import forms
# É crucial garantir que os modelos abaixo (Profile, Terreno, PlanoPlantio)
# e a lista de escolhas (UNIT_CHOICES) estejam corretamente importados do seu models.py
from .models import Profile, Terreno, UNIT_CHOICES, PlanoPlantio


# ==============================================================================
# Formulário de Perfil
# ==============================================================================
class ProfileForm(forms.ModelForm):
    """
    Formulário para o modelo Profile, incluindo campos personalizados
    para localização.
    """
    # Lista estática de países
    COUNTRY_CHOICES = [
        ('Brasil', 'Brasil'),
        ('EUA', 'Estados Unidos'),
        ('Argentina', 'Argentina'),
        ('Outro', 'Outro')
    ]

    # CORREÇÃO CRÍTICA: O campo foi renomeado de 'country' para 'pais'
    # para corresponder ao campo do modelo, permitindo que o ModelForm salve
    # o valor automaticamente, sem precisar de lógica extra no views.py.
    pais = forms.ChoiceField(
        choices=COUNTRY_CHOICES,
        required=False,
        label='País',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    # CORREÇÃO: Os campos 'estado', 'cidade' e 'cultivo_principal' estão definidos
    # no modelo como CharField e serão tratados como selects no template.
    # No entanto, eles PRECISAM ser sobrescritos aqui com o forms.CharField (ou forms.TextInput
    # para 'cultivo_principal') para evitar que o Django tente renderizá-los com o SELECT padrão
    # do ModelForm, já que você os está manipulando via JS/AJAX no template.

    estado = forms.CharField(label='Estado', required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    cidade = forms.CharField(label='Cidade', required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    # O campo 'cultivo_principal' também é um CharField no modelo e um select no HTML.
    # Você já o sobrescreveu com TextInput no widgets abaixo, o que é suficiente.

    class Meta:
        model = Profile
        # CORREÇÃO: O campo 'country' foi trocado por 'pais' para mapear corretamente o modelo.
        fields = ['first_name', 'last_name', 'pais', 'estado', 'cidade', 'birth_date', 'contact', 'cultivo_principal']
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact': forms.TextInput(attrs={'class': 'form-control'}),
            'cultivo_principal': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'first_name': 'Nome',
            'last_name': 'Sobrenome',
            'birth_date': 'Data de Nascimento',
            'contact': 'Contato (Email/Telefone)',
            'cultivo_principal': 'Principal Cultivo',
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
        # Usando nomes que parecem estar corretos no models.py
        fields = ['nome', 'area_total', 'unidade_area']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Lote Fundos'}),
            'area_total': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 15.5'}),
            'unidade_area': forms.Select(choices=UNIT_CHOICES, attrs={'class': 'form-control'}),
        }
        labels = {
            'nome': 'Nome do Terreno',
            'area_total': 'Tamanho (Área)',
            'unidade_area': 'Unidade de Medida',
        }


# ==============================================================================
# Formulário de Seleção de Terreno para o Plano de Cultivo
# ==============================================================================
class PlanoCultivoSelectTerrenoForm(forms.Form):
    """
    Formulário para a primeira etapa do Plano de Cultivo: selecionar um Terreno.
    O queryset é dinâmico e filtrado pelo usuário logado.
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
            # CORREÇÃO CRÍTICA: O filtro deve usar 'proprietario' (ForeignKey para User no Terreno), não 'user'.
            self.fields['terreno'].queryset = Terreno.objects.filter(proprietario=user).order_by('nome')


# ==============================================================================
# Formulário para o Modelo PlanoPlantio
# ==============================================================================
class PlanoPlantioForm(forms.ModelForm):
    """
    Formulário para salvar o Plano de Cultivo final.
    """

    class Meta:
        model = PlanoPlantio
        # CORRIGIDO: Usando os campos reais do seu modelo PlanoPlantio
        fields = [
            'terreno',
            'produto',
            'data_inicio',
            'data_colheita_prevista',
        ]

        widgets = {
            # 'terreno' e 'produto' (anteriormente 'cultura') são HiddenInput,
            # pois serão preenchidos via contexto/view e não diretamente pelo usuário.
            # O 'produto' é um FK para ProdutoAgricola, então deve ser um ModelChoiceField se não for HiddenInput.
            # Como é HiddenInput, está OK.
            'terreno': forms.HiddenInput(),
            'produto': forms.HiddenInput(),
            'data_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_colheita_prevista': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

        labels = {
            # O nome do plano de cultivo não é um campo no model, usamos os rótulos dos campos reais.
            'data_inicio': 'Data de Início do Plantio',
            'data_colheita_prevista': 'Data de Colheita Prevista',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # CORREÇÃO: Os campos 'localizacao' e 'area' não existem no seu modelo PlanoPlantio.
        # Portanto, o código para excluí-los deve ser removido.
        # if 'localizacao' in self.fields:
        #     del self.fields['localizacao']
        # if 'area' in self.fields:
        #     del self.fields['area']
        pass # Não há exclusões necessárias no modelo final