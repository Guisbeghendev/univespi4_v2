# fichatecnica_app/urls.py

from django.urls import path
from . import views

app_name = 'fichatecnica_app'

urlpatterns = [
    # Rota API para buscar a ficha técnica de um produto em uma cidade específica
    # O produto é passado como slug (NORMALIZADO) e a cidade é passada pelo ID do IBGE.
    path('api/ficha/<str:product_slug>/<int:city_id>/', views.get_ficha_api, name='get_ficha_api'),
]