from django.shortcuts import render
from .models import Categoria, Plato
from pedidos.carrito import Carrito
from django.shortcuts import get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from .models import Variante

def menu_digital(request):
    """
    Vista principal: Muestra el menú completo.
    """
    # 1. Obtenemos las categorías activas
    categorias = Categoria.objects.all().prefetch_related(
        'platos', 
        'platos__insumos_clave', # <--- ESTO ES VITAL: Trae los insumos en la misma consulta
        'platos__variantes'
    )


    carrito = Carrito(request)
    
    # 2. Empaquetamos los datos para enviarlos
    context = {
        'categorias': categorias,
        'carrito': carrito,
    }
    
    # 3. Renderizamos el HTML
    return render(request, 'catalogo/menu.html', context)

@staff_member_required # Solo administradores pueden usar esto
def toggle_variante(request, variante_id):
    variante = get_object_or_404(Variante, id=variante_id)
    variante.activo = not variante.activo # Aquí invertimos el estado (On <-> Off)
    variante.save()
    
    # Nos devuelve a la página donde estábamos (el admin)
    return redirect(request.META.get('HTTP_REFERER', '/admin/'))