from django.urls import path
from . import views

# Define o namespace da aplicação
app_name = 'plano'

urlpatterns = [
    # -----------------------------------------------------------
    # API PONTO DE ENTRADA (USADA PELO BLOCO7.JS)
    # -----------------------------------------------------------

    # 1. API para listagem de terrenos do usuário (para o select inicial)
    path('terrenos/', views.api_terrenos, name='api_terrenos'),

    # 2. Ponto de entrada do Wizard: Cria o RASCUNHO do Plano e redireciona (GET)
    path('iniciar/', views.iniciar_wizard, name='iniciar_wizard'),

    # -----------------------------------------------------------
    # WIZARD - ETAPA 1: SELEÇÃO DE CULTIVO
    # -----------------------------------------------------------

    # 3. View da Etapa 1 do Wizard (Procedimento)
    path('<int:plano_id>/etapa1/', views.etapa1_plano, name='etapa1_plano'),

    # 4. API para buscar os dados da Ficha Técnica (data_service)
    path('ficha/buscar/', views.api_buscar_ficha, name='api_buscar_ficha'),

    # 5. API para salvar os dados da Etapa 1 no PlanoPlantio
    path('<int:plano_id>/etapa1/salvar/', views.api_salvar_etapa1, name='api_salvar_etapa1'),

    # -----------------------------------------------------------
    # FASE 2: PÁGINA FINAL DE VISUALIZAÇÃO (planofinal.html)
    # -----------------------------------------------------------

    # 6. View de visualização e finalização (o destino após a Etapa 1)
    path('<int:plano_id>/final/', views.planofinal_plano, name='planofinal_plano'),
]