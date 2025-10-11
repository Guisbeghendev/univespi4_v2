# Define as rotas URL para o aplicativo planodeplantio_app (Django App).

from django.urls import path
from . import views

# O 'app_name' é crucial para usar a função 'reverse' e referenciar as rotas
app_name = 'plano'

urlpatterns = [
    # 1. Rota de API: Endpoint para o JavaScript do bloco7.html buscar a lista de terrenos do usuário em formato JSON.
    # Chamará a função 'api_terrenos' no views.py
    path('api/terrenos/', views.api_terrenos, name='api_terrenos'),

    # 2. Rota de Ação: Rota que recebe o ID do terreno selecionado e inicia a lógica de criação do plano.
    # Chamará a função 'criar_plano_plantio' no views.py
    path('criar-plano-plantio/', views.criar_plano_plantio, name='criar_plano_plantio'),
]
