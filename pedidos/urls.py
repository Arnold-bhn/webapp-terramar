from django.urls import path
from . import views
from pedidos.views import toggle_variante_status # <--- Importa la vista nueva
urlpatterns = [
    path('carrito/', views.ver_carrito, name='ver_carrito'),
    
    # Estandarizamos el nombre del parámetro a 'variante_id'
    path('agregar/<int:variante_id>/', views.agregar_carrito, name='agregar_carrito'),
    path('sumar/<int:variante_id>/', views.sumar_plato, name='sumar_plato'),
    path('restar/<int:variante_id>/', views.restar_plato, name='restar_plato'),
    path('eliminar/<int:variante_id>/', views.eliminar_carrito, name='eliminar_carrito'),

    path('limpiar/', views.limpiar_carrito, name='limpiar_carrito'),
    path('toggle-variante/<int:variante_id>/', toggle_variante_status, name='toggle_variante'),
]