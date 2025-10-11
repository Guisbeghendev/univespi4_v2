from django import forms
from agro_app.models import PlanoPlantio, EtapaPlantio, Terreno, Produto
from django.contrib.auth import get_user_model

User = get_user_model()


class PlanoPlantioForm(forms.ModelForm):
    """
    Formulário para a criação e edição do Plano de Plantio principal.
    """

    class Meta:
        model = PlanoPlantio
        # Excluímos 'proprietario' pois será preenchido automaticamente pela view
        # Excluímos 'status' e 'rendimento_final' pois são preenchidos por lógica
        exclude = ('proprietario', 'status', 'rendimento_final', 'unidade_rendimento')

        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Soja Safra 2025'}),
            # O Terreno será filtrado para mostrar apenas os terrenos do usuário logado
            'terreno': forms.Select(attrs={'class': 'form-control'}),
            'produto': forms.Select(attrs={'class': 'form-control'}),
            'data_inicio': forms.DateInput(attrs={'class': 'form-control date-picker', 'type': 'date'}),
            'data_colheita_prevista': forms.DateInput(attrs={'class': 'form-control date-picker', 'type': 'date'}),
        }
        labels = {
            'nome': 'Nome do Plano',
            'terreno': 'Terreno para o Plantio',
            'produto': 'Cultura Principal',
            'data_inicio': 'Data de Início (Plantio/Preparo)',
            'data_colheita_prevista': 'Previsão de Colheita',
        }

    def __init__(self, *args, **kwargs):
        # A view deve passar o usuário logado no argumento 'user'
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Filtra o campo 'terreno' para exibir apenas os terrenos pertencentes ao usuário
        if self.user:
            self.fields['terreno'].queryset = Terreno.objects.filter(proprietario=self.user)
            # Torna o campo 'terreno' obrigatório (se o usuário existir)
            self.fields['terreno'].required = True

        # Garante que o campo produto exiba apenas produtos
        self.fields['produto'].queryset = Produto.objects.all()


class EtapaPlantioForm(forms.ModelForm):
    """
    Formulário para a criação e edição das etapas do Plano de Plantio.
    """

    class Meta:
        model = EtapaPlantio
        # Excluímos 'plano' e 'concluida' pois serão preenchidos pela view/lógica
        exclude = ('plano', 'concluida', 'data_conclusao')

        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Aplicação de Ureia'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'data_prevista': forms.DateInput(attrs={'class': 'form-control date-picker', 'type': 'date'}),
            'insumo_usado': forms.TextInput(attrs={'class': 'form-control'}),
            'quantidade_insumo': forms.NumberInput(attrs={'class': 'form-control'}),
            'unidade_insumo': forms.Select(attrs={'class': 'form-control'}),
            'custo_total': forms.NumberInput(attrs={'class': 'form-control'}),
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