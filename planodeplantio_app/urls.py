# Define as rotas URL para o aplicativo planodeplantio_app (Django App).

from django.urls import path
from . import views

# O 'app_name' é crucial para usar a função 'reverse' e referenciar as rotas
app_name = 'plano'

urlpatterns = [
    # 1. VISÃO GERAL (LISTAGEM)
    path('', views.listar_planos, name='listar_planos'),

    # --- ROTAS DO WIZARD DE CRIAÇÃO ---

    # 2. INÍCIO DO WIZARD (Etapa 1: Recebe 'terreno_id' via GET do dashboard e redireciona)
    path('iniciar/', views.iniciar_wizard, name='iniciar_wizard'),

    # 3. SELEÇÃO DE PRODUTO (Etapa 2: A view precisa do ID do terreno na URL)
    # Ex: /plano/selecao-produto/123e4567-e89b-12d3-a456-426614174000/
    path('selecao-produto/<uuid:terreno_id>/', views.selecao_produto, name='selecao_produto'),

    # 4. CRIAÇÃO DE PLANO (Etapa 3: Submissão final, recebe 'terreno_id' e 'produto_id' via GET/POST)
    # Rota simples, pois os IDs são passados via parâmetros GET na views.py
    path('criar/', views.criar_plano_plantio, name='criar_plano_plantio'),

    # --- ROTAS DE CRUD PRINCIPAIS ---

    # 5. DETALHAMENTO DO PLANO E SUAS ETAPAS (Ex: /plano/b2a7.../)
    path('<uuid:plano_id>/', views.detalhe_plano, name='detalhe_plano'),

    # 6. EDIÇÃO DO PLANO PRINCIPAL (Ex: /plano/b2a7.../editar/)
    path('<uuid:plano_id>/editar/', views.editar_plano, name='editar_plano'),

    # 7. EXCLUSÃO DO PLANO (Ex: /plano/b2a7.../excluir/)
    # O nome da rota é 'excluir_plano', mas aponta para a função 'deletar_plano'
    path('<uuid:plano_id>/excluir/', views.deletar_plano, name='excluir_plano'),

    # --- ROTAS PARA ETAPAS ---

    # 8. CRIAÇÃO DE ETAPA (Relacionada a um plano específico)
    # Ex: /plano/b2a7.../etapa/adicionar/
    path('<uuid:plano_id>/etapa/adicionar/', views.adicionar_etapa, name='adicionar_etapa'),

    # 9. EDIÇÃO DE ETAPA ESPECÍFICA
    # Ex: /plano/b2a7.../etapa/8f3c.../editar/
    path('<uuid:plano_id>/etapa/<uuid:etapa_id>/editar/', views.editar_etapa, name='editar_etapa'),

    # 10. MARCAR ETAPA COMO CONCLUÍDA (Ação rápida)
    # Ex: /plano/b2a7.../etapa/8f3c.../concluir/
    path('<uuid:plano_id>/etapa/<uuid:etapa_id>/concluir/', views.concluir_etapa, name='concluir_etapa'),

    # 11. EXCLUSÃO DE ETAPA
    # Ex: /plano/b2a7.../etapa/8f3c.../excluir/
    path('<uuid:plano_id>/etapa/<uuid:etapa_id>/excluir/', views.deletar_etapa, name='excluir_etapa'),

    # --- ROTAS DE API (AJAX) ---

    # 12. API para listar terrenos do usuário (usada na Dashboard/Wizard)
    path('api/terrenos/', views.api_terrenos, name='api_terrenos'),

    # 13. API para buscar produtos por cidade (usada no Wizard)
    path('api/produtos/<str:cidade_id>/', views.buscar_produtos_por_cidade, name='api_produtos_por_cidade'),
]
