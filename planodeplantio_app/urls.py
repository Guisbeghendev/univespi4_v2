from django.urls import path
from . import views

# Define o namespace da aplicação
app_name = 'plano'

urlpatterns = [
    # -----------------------------------------------------------
    # API PONTO DE ENTRADA (USADA PELO BLOCO7.JS)
    # -----------------------------------------------------------

    # 1. API para listagem de terrenos do usuário (para o select inicial)
    # Rota: /api/terrenos/ (CORRIGIDO: Removido 'api/')
    # Rota final esperada se incluído como: path('plano/api/', include('...'))
    # **SUGESTÃO DE MELHORIA: se o prefixo 'api' for incluído no project/urls.py**
    path('terrenos/', views.api_terrenos, name='api_terrenos'),

    # 2. Ponto de entrada do Wizard: Cria o RASCUNHO do Plano e redireciona (GET)
    # Rota: /api/planos/iniciar/ (CORRIGIDO: Simplificado para a palavra-chave)
    path('iniciar/', views.iniciar_wizard, name='iniciar_wizard'),

    # -----------------------------------------------------------
    # WIZARD - ETAPA 1: SELEÇÃO DE CULTIVO E DATAS
    # -----------------------------------------------------------

    # 3. View da Etapa 1 do Wizard (Procedimento)
    # Rota: /planos/{plano_id}/etapa1/ (CORRIGIDO: Removido '/planos/')
    path('<int:plano_id>/etapa1/', views.etapa1_plano, name='etapa1_plano'),

    # 4. API para buscar os dados da Ficha Técnica (data_service)
    # Rota: /api/ficha/buscar/ (CORRIGIDO: Removido 'api/')
    path('ficha/buscar/', views.api_buscar_ficha, name='api_buscar_ficha'),

    # 5. API para salvar os dados da Etapa 1 no PlanoPlantio
    # Rota: /api/planos/{plano_id}/etapa1/salvar/ (CORRIGIDO: Removido 'api/planos/')
    path('<int:plano_id>/etapa1/salvar/', views.api_salvar_etapa1, name='api_salvar_etapa1'),

    # -----------------------------------------------------------
    # FUTURAS ETAPAS (A SEREM IMPLEMENTADAS)
    # -----------------------------------------------------------

    # Exemplo: Próxima etapa do Procedimento
    # path('<int:plano_id>/etapa2/', views.etapa2_plano, name='etapa2_plano'),
]