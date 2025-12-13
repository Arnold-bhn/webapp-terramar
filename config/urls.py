from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Importamos la vista del menú desde la app 'catalogo'
# Asegúrate de que en catalogo/views.py la función se llame 'menu'
from catalogo import views as catalogo_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # --- ESTA ES LA LÍNEA QUE TE FALTA ---
    # Al ponerle name='menu', el redirect("menu") ya sabrá a dónde ir.
    path('', catalogo_views.menu_digital, name='menu'),
    # -------------------------------------

    # Rutas del Carrito
    path('pedidos/', include('pedidos.urls')),
]

# Configuración para ver las fotos de los platos
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)