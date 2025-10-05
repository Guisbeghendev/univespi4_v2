from django.urls import path
from . import views

app_name = 'agro_app'

urlpatterns = [
    # Dashboard Principal
    path('', views.dashboard, name='dashboard'),

    # Views de Perfil
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),

    # URLs de API do IBGE e Produto (Usadas no AJAX do Edit Profile)
    path('api/states/', views.get_states, name='get_states'),
    path('api/cities/<int:state_id>/', views.get_cities, name='get_cities'),

    # URL de API para buscar produtos por cidade (ID)
    path('api/products/by_id/<int:city_id>/', views.get_products_by_city_by_id, name='get_products_by_city_by_id'),
]