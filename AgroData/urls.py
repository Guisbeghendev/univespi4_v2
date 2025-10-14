"""
URL configuration for AgroData project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('home.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('dashboard/', include('agro_app.urls')),
    path('ficha/', include('fichatecnica_app.urls')),
    path('clima/', include('climalocal_app.urls')),
    path('info/', include('info_app.urls')),
    path('api/terrenos/', include('terreno_app.urls', namespace='terreno_app')),
    path('plano/', include('planodeplantio_app.urls', namespace='plano')),

]
