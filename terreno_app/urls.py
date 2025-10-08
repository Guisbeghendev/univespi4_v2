from django.urls import path
from . import views

# Define o namespace 'terreno_app' usado nos templates para evitar conflitos de nomes
app_name = 'terreno_app'

urlpatterns = [
    # URL para criar um novo terreno
    path('criar/', views.create_terreno, name='create_terreno'),

    # URL para editar um terreno existente, usando a Primary Key (pk)
    path('editar/<int:pk>/', views.edit_terreno, name='edit_terreno'),

    # URL para excluir um terreno existente, usando a Primary Key (pk)
    path('excluir/<int:pk>/', views.delete_terreno, name='delete_terreno'),
]
