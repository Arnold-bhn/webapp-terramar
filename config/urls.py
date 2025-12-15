from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Importamos TODAS las vistas de pedidos (incluyendo las de catálogo y modal)
from pedidos import views 

urlpatterns = [
    # Administración y Toggle de estado (usa la vista de pedidos)
    path('admin/toggle-variante/<int:variante_id>/', views.toggle_variante_status, name='toggle_variante_status'),
    path('admin/', admin.site.urls),

    # 1. RUTA DE INICIO
    path('', views.catalogo_general, name='menu'), 

    # 2. RUTAS DE CARRITO
    path('agregar/<int:variante_id>/', views.agregar_carrito, name='agregar_carrito'),
    path('sumar/<str:item_key>/', views.sumar_plato, name='sumar_plato'), 
    path('restar/<str:item_key>/', views.restar_plato, name='restar_plato'),
    path('eliminar/<str:item_key>/', views.eliminar_carrito, name='eliminar_carrito'),
    path('limpiar/', views.limpiar_carrito, name='limpiar_carrito'),
    path('carrito/', views.ver_carrito, name='ver_carrito'),

    # --- RUTA DE CHECKOUT ---
    path('checkout/', views.iniciar_pago, name='checkout'), 
    
    # --- RUTA PARA EL MODAL (Usa views.modal_opciones de pedidos) ---
    path('modal-opciones/<int:variante_id>/', views.modal_opciones, name='cargar_modal_opciones'),

    # 3. RUTAS AJAX
    path('ajax/platos/<slug:marca_slug>/', views.ajax_platos_by_marca, name='ajax_platos_marca'),

    # 4. RUTA DEL CATÁLOGO POR MARCA
    path('<slug:marca_slug>/', views.catalogo_por_marca, name='catalogo_marca'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)