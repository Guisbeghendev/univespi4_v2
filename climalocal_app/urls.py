# climalocal_app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Esta URL será acessada, por exemplo, como /clima/dados?city=Bauru
    path('dados', views.weather_api_endpoint, name='clima_dados'),
]