# Define as rotas URL para o aplicativo planodeplantio_app (Django App).

from django.urls import path
from . import views

# O 'app_name' é crucial para usar a função 'reverse' e referenciar as rotas
app_name = 'plano'

urlpatterns = [
    # 1. VISÃO GERAL (LISTAGEM)
    path('', views.listar_planos, name='listar_planos'),

    # 2. CRIAÇÃO DE PLANO
    # CORRIGIDO: O nome da view foi alterado de 'criar_plano_plantio' para 'criar_plano' (conforme views.py)
    path('criar/', views.criar_plano, name='criar_plano_plantio'),

    # 3. DETALHAMENTO DO PLANO E SUAS ETAPAS (Ex: /plano/b2a7.../)
    # CORREÇÃO: Usando 'uuid' e views.detalhe_plano
    path('<uuid:plano_id>/', views.detalhe_plano, name='detalhe_plano'),

    # 4. EDIÇÃO DO PLANO PRINCIPAL (Ex: /plano/b2a7.../editar/)
    # CORREÇÃO: Usando 'uuid'
    path('<uuid:plano_id>/editar/', views.editar_plano, name='editar_plano'),

    # 5. EXCLUSÃO DO PLANO (Ex: /plano/b2a7.../excluir/)
    # CORRIGIDO: O nome da view foi alterado de 'excluir_plano' para 'deletar_plano' (conforme views.py)
    path('<uuid:plano_id>/excluir/', views.deletar_plano, name='excluir_plano'),

    # --- ROTAS PARA ETAPAS ---

    # 6. CRIAÇÃO DE ETAPA (Relacionada a um plano específico)
    # CORRIGIDO: O nome da view foi alterado de 'criar_etapa' para 'adicionar_etapa' (conforme views.py)
    # Ex: /plano/b2a7.../etapa/adicionar/
    path('<uuid:plano_id>/etapa/adicionar/', views.adicionar_etapa, name='adicionar_etapa'),

    # 7. EDIÇÃO DE ETAPA ESPECÍFICA
    # CORREÇÃO: Usando 'uuid' para plano_id e etapa_id
    # Ex: /plano/b2a7.../etapa/8f3c.../editar/
    path('<uuid:plano_id>/etapa/<uuid:etapa_id>/editar/', views.editar_etapa, name='editar_etapa'),

    # 8. MARCAR ETAPA COMO CONCLUÍDA (Ação rápida)
    # CORREÇÃO: Usando 'uuid' para plano_id e etapa_id
    # Ex: /plano/b2a7.../etapa/8f3c.../concluir/
    path('<uuid:plano_id>/etapa/<uuid:etapa_id>/concluir/', views.concluir_etapa, name='concluir_etapa'),

    # 9. EXCLUSÃO DE ETAPA
    # CORRIGIDO: O nome da view foi alterado de 'excluir_etapa' para 'deletar_etapa' (conforme views.py)
    # Ex: /plano/b2a7.../etapa/8f3c.../excluir/
    path('<uuid:plano_id>/etapa/<uuid:etapa_id>/excluir/', views.deletar_etapa, name='excluir_etapa'),

    # 10. Rota de API (Mantida, se for usada por JS para buscar dados)
    path('api/terrenos/', views.api_terrenos, name='api_terrenos'),
]
