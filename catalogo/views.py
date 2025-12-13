from django.shortcuts import render
from .models import Categoria, Plato
from pedidos.carrito import Carrito

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