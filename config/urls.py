from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from catalogo.views import toggle_variante
from pedidos import views 

urlpatterns = [
    path('admin/toggle-variante/<int:variante_id>/', toggle_variante, name='toggle_variante'),
    path('admin/', admin.site.urls),

    # 1. RUTA DE INICIO
    path('', views.catalogo_general, name='menu'), 

    # 2. RUTAS DE CARRITO
    path('agregar/<int:variante_id>/', views.agregar_carrito, name='agregar_carrito'),
    path('sumar/<int:variante_id>/', views.sumar_plato, name='sumar_plato'),
    path('restar/<int:variante_id>/', views.restar_plato, name='restar_plato'),
    path('eliminar/<int:variante_id>/', views.eliminar_carrito, name='eliminar_carrito'),
    path('limpiar/', views.limpiar_carrito, name='limpiar_carrito'),
    path('carrito/', views.ver_carrito, name='ver_carrito'),
    path('toggle-status/<int:variante_id>/', views.toggle_variante_status, name='toggle_variante_status'),

    # --- 3. NUEVA RUTA AJAX (¡ESTA ES LA CLAVE!) ---
    # Esta ruta es la que usa JavaScript para pedir solo los platos sin recargar
    path('ajax/platos/<slug:marca_slug>/', views.ajax_platos_by_marca, name='ajax_platos_marca'),

    # 4. RUTA DEL CATÁLOGO POR MARCA (Navegación normal)
    path('<slug:marca_slug>/', views.catalogo_por_marca, name='catalogo_marca'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)