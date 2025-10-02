from django.urls import path
from . import views

app_name = 'agro_app'

urlpatterns = [
    # Rotas API e Principais (Rotas Originais)
    path('', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('api/get-states/', views.get_states, name='get_states'),
    path('api/get-cities/<int:state_id>/', views.get_cities, name='get_cities'),
    path('api/get-products-by-city/<str:city_name>/', views.get_products_by_city, name='get_products_by_city'),
    path('api/get-products-by-city-by-id/<int:city_id>/', views.get_products_by_city_by_id,
         name='get_products_by_city_by_id'),
    path('api/get-detailed-data/<str:city_name>/<str:product_name>/', views.get_detailed_data_by_product_and_city,
         name='get_detailed_data'),

    # NOVAS Rotas de Gerenciamento de Terrenos
    path('terreno/create/', views.create_terreno, name='create_terreno'),
    path('terreno/edit/<int:pk>/', views.edit_terreno, name='edit_terreno'),
    path('terreno/delete/<int:pk>/', views.delete_terreno, name='delete_terreno'),

    # NOVAS Rotas para o Plano de Cultivo
    path('plano/create/', views.create_plano, name='create_plano'),
    path('plano/create/terreno/<int:terreno_id>/product/', views.select_product_plano, name='select_product_plano'),

    # NOVA ROTA: Rota para salvar o plano de cultivo finalizado (POST)
    path('plano/save/<int:terreno_id>/', views.save_plano, name='save_plano'),

    path('api/plano-data/<int:terreno_id>/<str:product_id>/', views.get_plano_data_details,
         name='get_plano_data_details'),
]