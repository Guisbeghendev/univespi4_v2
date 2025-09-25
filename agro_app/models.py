from django.db import models
from django.contrib.auth.models import User

# Modelo para o Plano de Plantio
class PlanoPlantio(models.Model):
    # Relaciona o plano de plantio com um usuário
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    nome_plantacao = models.CharField(max_length=200)
    cultura = models.CharField(max_length=100)
    localizacao = models.CharField(max_length=200)
    area = models.DecimalField(max_digits=10, decimal_places=2, help_text="Área em hectares")
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nome_plantacao} de {self.cultura}"

# Modelo para os Dados Climáticos (importados de APIs)
class DadosClimaticos(models.Model):
    # Relaciona os dados climáticos a um plano de plantio específico
    plano_plantio = models.ForeignKey(PlanoPlantio, on_delete=models.CASCADE)
    data_hora = models.DateTimeField()
    temperatura = models.DecimalField(max_digits=5, decimal_places=2)
    umidade_ar = models.IntegerField(help_text="Umidade do ar em %")
    pressao_atmosferica = models.IntegerField(help_text="Pressão em hPa")
    velocidade_vento = models.DecimalField(max_digits=5, decimal_places=2, help_text="Velocidade em m/s")
    descricao_clima = models.CharField(max_length=100)

    def __str__(self):
        return f"Dados de clima para {self.plano_plantio.nome_plantacao} em {self.data_hora.strftime('%d/%m/%Y %H:%M')}"

# Modelo para os Dados Simulados dos Sensores
class DadosSensor(models.Model):
    # Relaciona os dados do sensor a um plano de plantio específico
    plano_plantio = models.ForeignKey(PlanoPlantio, on_delete=models.CASCADE)
    data_hora = models.DateTimeField(auto_now_add=True)
    temperatura_solo = models.DecimalField(max_digits=5, decimal_places=2)
    umidade_solo = models.IntegerField(help_text="Umidade do solo em %")

    def __str__(self):
        return f"Dados de sensor para {self.plano_plantio.nome_plantacao} em {self.data_hora.strftime('%d/%m/%Y %H:%M')}"


# moelo de profile
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    contact = models.CharField(max_length=100, blank=True, null=True)
    cultivo_principal = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"