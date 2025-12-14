from django.urls import path
from . import views

urlpatterns = [
    # 1. Ruta base: Si entras a /pedidos/ te redirige a la primera marca
    path('', views.catalogo_general, name='menu'),

    # 2. Operaciones del carrito (AJAX)
    path('agregar/<int:variante_id>/', views.agregar_carrito, name='agregar_carrito'),
    path('sumar/<int:variante_id>/', views.sumar_plato, name='sumar_plato'),
    path('restar/<int:variante_id>/', views.restar_plato, name='restar_plato'),
    path('eliminar/<int:variante_id>/', views.eliminar_carrito, name='eliminar_carrito'),
    path('limpiar/', views.limpiar_carrito, name='limpiar_carrito'),
    path('carrito/', views.ver_carrito, name='ver_carrito'),

    # 3. Toggle para activar/desactivar platos (Admin)
    path('toggle-status/<int:variante_id>/', views.toggle_variante_status, name='toggle_variante_status'),

    # 4. Ruta de la marca (IMPORTANTE: va al final para no tapar las otras)
    # Usamos <str:> en lugar de <slug:> para permitir espacios ("A Fuego")
    path('<slug:marca_slug>/', views.catalogo_por_marca, name='catalogo_marca'),
    path('ajax/platos/<slug:marca_slug>/', views.ajax_platos_by_marca, name='ajax_platos_marca'),
] 

