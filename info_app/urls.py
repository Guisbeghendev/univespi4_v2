from django.urls import path
from . import views

app_name = 'info_app'

urlpatterns = [
    # Rota principal para a página de consulta de dados agropecuários (Onde fica o Bloco 3)
    path('consulta/', views.info_consulta, name='info_consulta'),

    # ----------------------------------------------------------------------
    # Rotas de API para AJAX
    # ----------------------------------------------------------------------

    # API para carregar dinamicamente o select de 'Cultivo' (produto)
    # Ex: /info/api/products/123456/
    path('api/products/<int:city_id>/', views.get_products_for_filter, name='api_products_for_filter'),

    # API para buscar os dados COMPLETOS da Ficha Técnica (Resultado final da pesquisa)
    # CORREÇÃO: product_id alterado para product_name (string) para aceitar 'LARANJA', 'BORRACHA', etc.
    # Ex: /info/api/ficha/LARANJA/123456/ (product_name / city_id)
    path('api/ficha/<str:product_name>/<int:city_id>/', views.get_ficha_tecnica_data, name='api_ficha_tecnica_data'),
]
