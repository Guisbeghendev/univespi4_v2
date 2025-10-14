from django.urls import path
from . import views

# Define o namespace do aplicativo. É obrigatório para o uso de {% url 'info_app:...' %}
app_name = 'info_app'

urlpatterns = [
    # Rota principal que carrega o template HTML (onde o JS roda)
    path('consulta/', views.info_consulta, name='info_consulta'),

    # ----------------------------------------------------------------------
    # Rotas de API para o JavaScript consumir
    # ----------------------------------------------------------------------

    # 1. Busca todos os estados (não precisa de argumentos dinâmicos)
    path('api/states/', views.get_all_states, name='api_states'),

    # 2. Busca cidades de um estado específico (usa o ID do estado)
    path('api/cities/<int:state_id>/', views.get_cities_for_state, name='api_cities'),

    # 3. Busca produtos disponíveis em uma cidade (usa o ID da cidade)
    path('api/products/<int:city_id>/', views.get_products_for_filter, name='api_products_for_filter'),

    # 4. Busca os dados da Ficha Técnica (usa o nome do produto e o ID da cidade)
    path('api/ficha/<str:product_name>/<int:city_id>/', views.get_ficha_tecnica_data, name='api_ficha_tecnica_data'),
]
