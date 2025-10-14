from django import forms


# ATENÇÃO: Nenhuma outra classe de formulário (PlanoPlantioForm, EtapaPlantioForm, etc.)
# foi incluída, pois não há elementos em seu HTML/JS que as definam ou as utilizem.
# Este formulário representa a única informação coletada e usada pelo bloco7.js
# antes do redirecionamento: o ID do Terreno.

class TerrenoSelecaoForm(forms.Form):
    """
    Formulário para representar a seleção do Terreno.

    A lógica do front-end (bloco7.js) coleta o ID do terreno selecionado e
    inicia o wizard através de um redirecionamento com este ID como query parameter.
    O campo é oculto (HiddenInput), pois o valor é setado e usado via JavaScript.
    """
    terreno_id_selecionado = forms.CharField(
        label="ID do Terreno",
        max_length=50,
        required=True,
        # O campo é HiddenInput, pois o valor final é manipulado pelo JS.
        widget=forms.HiddenInput()
    )
