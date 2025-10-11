from django.db import models
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

# Obtém o modelo de usuário ativo (padrão do Django ou customizado)
User = get_user_model()

# --- CONSTANTES ---
# Unidades de medida comuns para produtos agrícolas, insumos ou resultados de colheita.
UNIT_CHOICES = [
    ('KG', 'Quilograma (kg)'),
    ('TON', 'Tonelada (ton)'),
    ('L', 'Litro (L)'),
    ('SAC', 'Saca (Sac)'),
    ('UN', 'Unidade'),
]


# --- MODELO PERFIL (PROFILE) ---
# Armazena informações adicionais do usuário e o sistema de localização padrão.
class Profile(models.Model):
    """
    Modelo de perfil do usuário (AgroData).
    Relacionado 1:1 com o modelo User.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # CAMPOS REINSERIDOS PARA CORRIGIR FIELDERROR NO ProfileForm
    first_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Primeiro Nome")
    last_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Sobrenome")
    birth_date = models.DateField(blank=True, null=True, verbose_name="Data de Nascimento")
    cultivo_principal = models.CharField(max_length=100, blank=True, null=True, verbose_name="Cultivo Principal")
    contact = models.CharField(max_length=15, blank=True, null=True, verbose_name="Contato (Telefone/WhatsApp)")
    # FIM DOS CAMPOS REINSERIDOS

    # NOVO CAMPO ADICIONADO: País
    pais = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="País"
    )

    # Sistema de localização padrão do usuário, baseado em IDs do IBGE.
    estado = models.CharField(
        max_length=2,
        null=True,
        blank=True,
        verbose_name="Estado (ID IBGE)"
    )
    cidade = models.CharField(
        max_length=7,
        null=True,
        blank=True,
        verbose_name="Município (ID IBGE)"
    )

    # Campos adicionais do perfil
    telefone = models.CharField(max_length=15, blank=True, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Perfil"
        verbose_name_plural = "Perfis"

    def __str__(self):
        return f'Perfil de {self.user.username}'


# Sinal para criar/salvar automaticamente o Profile quando um User é criado/salvo
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    # Garante que, se o perfil existir, ele seja salvo
    if hasattr(instance, 'profile'):
        instance.profile.save()


# --- MODELO TERRENO (LAND/PLOT) ---
# Registra as áreas de plantio e armazena sua localização específica.
class Terreno(models.Model):
    """
    Modelo para registro de Terrenos/Áreas de Plantio.
    Relacionado com o User que possui o Terreno.
    """
    # Relacionamento com o proprietário
    proprietario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='terrenos',
        verbose_name="Proprietário"
    )

    nome = models.CharField(max_length=100, verbose_name="Nome do Terreno")

    # Campo para o valor numérico da área (permite qualquer valor)
    area_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Valor da Área"
    )
    # Campo para a unidade de medida (ex: ha, m2, alqueire)
    unidade_area = models.CharField(
        max_length=20,
        verbose_name="Unidade de Medida"
    )

    # Sistema de Localização (IDs do IBGE)
    estado = models.CharField(
        max_length=2,
        null=True,
        blank=True,
        verbose_name="Estado (ID IBGE)"
    )
    cidade = models.CharField(
        max_length=7,
        null=True,
        blank=True,
        verbose_name="Município (ID IBGE)"
    )

    data_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Terreno"
        verbose_name_plural = "Terrenos"

    def __str__(self):
        return f"{self.nome} ({self.area_total} {self.unidade_area})"


# --- MODELO PRODUTO (PLACEHOLDER) ---
# Modelo para registrar produtos agrícolas (ex: Soja, Milho).
class Produto(models.Model):
    nome = models.CharField(max_length=100, unique=True, verbose_name="Produto")

    class Meta:
        verbose_name = "Produto Agrícola"
        verbose_name_plural = "Produtos Agrícolas"

    def __str__(self):
        return self.nome


# --- MODELO CLIMA (PLACEHOLDER) ---
# Armazena dados climáticos obtidos via API para uma localização específica.
class Clima(models.Model):
    # Relacionamento com Terreno (opcional)
    terreno = models.ForeignKey(
        Terreno,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dados_climaticos'
    )

    # Localização IBGE (útil para dados genéricos não ligados diretamente a um Terreno)
    estado_ibge = models.CharField(max_length=2, verbose_name="Estado IBGE")
    cidade_ibge = models.CharField(max_length=7, verbose_name="Município IBGE")

    data_hora = models.DateTimeField(verbose_name="Data/Hora da Previsão")
    temperatura = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Temperatura (°C)")
    precipitacao = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Precipitação (mm)")

    class Meta:
        verbose_name = "Dado Climático"
        verbose_name_plural = "Dados Climáticos"

    def __str__(self):
        return f'Clima em {self.cidade_ibge} em {self.data_hora.strftime("%Y-%m-%d %H:%M")}'


# --- MODELO Plano PLANTIO (RELACIONA TERRENO E PRODUTO) ---
class PlanoPlantio(models.Model):
    terreno = models.ForeignKey(
        Terreno,
        on_delete=models.CASCADE,
        related_name='plantios',
        verbose_name="Terreno"
    )
    produto = models.ForeignKey(
        Produto,
        on_delete=models.CASCADE,
        verbose_name="Produto Plantado"
    )
    data_inicio = models.DateField(verbose_name="Data de Início")
    data_colheita_prevista = models.DateField(verbose_name="Colheita Prevista", null=True, blank=True)

    class Meta:
        verbose_name = "Plantio"
        verbose_name_plural = "Plantios"
        unique_together = ('terreno', 'produto', 'data_inicio')

    # CORREÇÃO: Parêntese de fechamento adicionado aqui
    def __str__(self):
        return f'{self.produto.nome} em {self.terreno.nome} ({self.data_inicio.year})'