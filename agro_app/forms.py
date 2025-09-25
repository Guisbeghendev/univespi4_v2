from django import forms
from .models import Profile


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