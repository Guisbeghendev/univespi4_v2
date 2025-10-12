from django import forms

# Importa os modelos da aplicação consolidada (agro_app.models)
from agro_app.models import PlanoPlantio, EtapaPlantio, Terreno, Produto

# --- CLASSES DE ESTILO PARA TW ---
TAILWIND_INPUT_CLASSES = 'form-input w-full rounded-lg border-gray-300 shadow-sm focus:border-green-500 focus:ring-green-500'
TAILWIND_SELECT_CLASSES = 'form-select w-full rounded-lg border-gray-300 shadow-sm focus:border-green-500 focus:ring-green-500'


# Formulário para criar ou editar um Plano de Plantio
class PlanoPlantioForm(forms.ModelForm):
    """
    Formulário para a criação e edição do Plano de Plantio principal.
    Prepara o formulário para receber dados via o Wizard (terreno e produto pré-selecionados).
    """

    class Meta:
        model = PlanoPlantio
        # Excluímos campos preenchidos pela lógica da View ou por ação posterior.
        exclude = ('proprietario', 'status', 'rendimento_final', 'unidade_rendimento')

        widgets = {
            'nome': forms.TextInput(attrs={'class': TAILWIND_INPUT_CLASSES, 'placeholder': 'Ex: Soja Safra 2025'}),
            # Terreno e Produto serão pré-selecionados, mas ainda são inputs visíveis
            'terreno': forms.Select(attrs={'class': TAILWIND_SELECT_CLASSES, 'readonly': 'readonly'}),
            'produto': forms.Select(attrs={'class': TAILWIND_SELECT_CLASSES, 'readonly': 'readonly'}),
            'data_inicio': forms.DateInput(attrs={'type': 'date', 'class': TAILWIND_INPUT_CLASSES}),
            'data_colheita_prevista': forms.DateInput(attrs={'type': 'date', 'class': TAILWIND_INPUT_CLASSES}),
        }

        labels = {
            'nome': 'Nome do Plano',
            'terreno': 'Terreno para o Plantio',
            'produto': 'Cultura Principal',
            'data_inicio': 'Data de Início (Plantio/Preparo)',
            'data_colheita_prevista': 'Previsão de Colheita',
        }

    def __init__(self, *args, **kwargs):
        # Recebe o QuerySet de terrenos filtrado para o usuário logado, enviado pela View
        terrenos_queryset = kwargs.pop('terrenos_queryset', None)
        super().__init__(*args, **kwargs)

        # Filtra e configura o campo 'terreno'
        if terrenos_queryset is not None:
            self.fields['terreno'].queryset = terrenos_queryset

        # Garante que o campo produto exiba apenas produtos
        self.fields['produto'].queryset = Produto.objects.all()


# Formulário para criar ou editar uma Etapa de Plantio
class EtapaPlantioForm(forms.ModelForm):
    """
    Formulário para a criação e edição das etapas do Plano de Plantio.
    """

    class Meta:
        model = EtapaPlantio
        # Excluímos campos preenchidos automaticamente
        exclude = ('plano', 'concluida', 'data_conclusao')

        widgets = {
            'tipo': forms.Select(attrs={'class': TAILWIND_SELECT_CLASSES}),
            'nome': forms.TextInput(attrs={'class': TAILWIND_INPUT_CLASSES, 'placeholder': 'Ex: Aplicação de Ureia'}),
            'descricao': forms.Textarea(attrs={'rows': 3, 'class': TAILWIND_INPUT_CLASSES}),
            'data_prevista': forms.DateInput(attrs={'type': 'date', 'class': TAILWIND_INPUT_CLASSES}),
            'insumo_usado': forms.TextInput(attrs={'class': TAILWIND_INPUT_CLASSES}),
            'quantidade_insumo': forms.NumberInput(attrs={'class': TAILWIND_INPUT_CLASSES}),
            'unidade_insumo': forms.Select(attrs={'class': TAILWIND_SELECT_CLASSES}),
            'custo_total': forms.NumberInput(attrs={'class': TAILWIND_INPUT_CLASSES}),
        }

        labels = {
            'tipo': 'Tipo de Etapa',
            'nome': 'Título da Tarefa',
            'descricao': 'Detalhes da Etapa',
            'data_prevista': 'Data Prevista',
            'insumo_usado': 'Insumo/Produto Utilizado',
            'quantidade_insumo': 'Quantidade',
            'unidade_insumo': 'Unidade (Kg, L, etc.)',
            'custo_total': 'Custo Estimado (R$)',
        }
