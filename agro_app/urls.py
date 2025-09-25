from django.urls import path
from . import views

app_name = 'agro_app'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('api/get-states/', views.get_states, name='get_states'),
    path('api/get-cities/<int:state_id>/', views.get_cities, name='get_cities'),
    path('api/get-products-by-city/<str:city_name>/', views.get_products_by_city, name='get_products_by_city'),
    path('api/get-products-by-city-by-id/<int:city_id>/', views.get_products_by_city_by_id, name='get_products_by_city_by_id'),
    path('api/get-detailed-data/<str:city_name>/<str:product_name>/', views.get_detailed_data_by_product_and_city, name='get_detailed_data'),
]
