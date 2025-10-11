from django.urls import path
from . import views

app_name = 'fichatecnica_app'

urlpatterns = [
    path('api/ficha/<str:product_slug>/<int:city_id>/', views.get_ficha_api, name='get_ficha_api'),
]
