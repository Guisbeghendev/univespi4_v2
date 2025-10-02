from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# Opções de Unidade de Medida para o Terreno
UNIT_CHOICES = (
    ('HA', 'Hectare (ha)'),
    ('M2', 'Metros Quadrados (m²)'),
)


# ==============================================================================
# Modelos Existentes
# ==============================================================================

# Modelo para o Plano de Plantio (ATUALIZADO)
class PlanoPlantio(models.Model):
    # Relaciona o plano de plantio com um usuário
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)

    # ALTERAÇÃO CRÍTICA: Relaciona o plano de plantio com um terreno específico
    terreno = models.ForeignKey('Terreno', on_delete=models.CASCADE, verbose_name="Terreno Selecionado")

    nome_plantacao = models.CharField(max_length=200, verbose_name="Nome do Plano")
    cultura = models.CharField(max_length=100, verbose_name="Cultura Escolhida (Nome Normalizado do Produto)")

    # Campos originais ajustados: tornados opcionais (blank/null) pois a localização
    # e a área serão primariamente derivadas do Terreno, mas mantidos para compatibilidade.
    localizacao = models.CharField(max_length=200, blank=True, null=True, verbose_name="Localização (Cidade/Estado)")
    area = models.DecimalField(max_digits=10, decimal_places=2, help_text="Área em hectares", blank=True, null=True)

    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Plano de Cultivo"
        verbose_name_plural = "Planos de Cultivo"

    def __str__(self):
        # String de representação atualizada para incluir o Terreno
        return f"{self.nome_plantacao} de {self.cultura} no Terreno: {self.terreno.name}"


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


# Modelo de Profile
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True, verbose_name="Cidade (IBGE ID ou Nome)")
    state = models.CharField(max_length=100, blank=True, null=True, verbose_name="Estado (IBGE ID ou Nome)")
    country = models.CharField(max_length=100, blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    contact = models.CharField(max_length=100, blank=True, null=True)
    cultivo_principal = models.CharField(max_length=100, blank=True, null=True,
                                         verbose_name="Cultivo Principal (Nome Normalizado)")

    def __str__(self):
        return f"Perfil de {self.user.username if self.user else 'Usuário sem link'}"


# Signals para garantir que um perfil é criado sempre que um novo usuário é criado
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()


# ==============================================================================
# MODELO TERRENO (CORRIGIDO: 'size' para 'area')
# ==============================================================================

class Terreno(models.Model):
    """
    Modelo para representar um terreno gerenciado pelo usuário.
    """
    # Relação: Um usuário pode ter muitos terrenos.
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='terrenos')

    # Nome para identificar o terreno
    name = models.CharField(max_length=255, verbose_name="Nome do Terreno")

    # CORREÇÃO: Renomeado de 'size' para 'area' para coincidir com o template.
    area = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Área")

    # Unidade de medida do tamanho
    unit = models.CharField(
        max_length=2,
        choices=UNIT_CHOICES,
        default='HA',
        verbose_name="Unidade de Medida"
    )

    class Meta:
        verbose_name = "Terreno"
        verbose_name_plural = "Terrenos"
        ordering = ['name']

    def __str__(self):
        # Usando 'area' e 'unit'
        return f'{self.name} ({self.area} {self.unit}) de {self.user.username}'