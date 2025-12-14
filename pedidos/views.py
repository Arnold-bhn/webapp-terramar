from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .carrito import Carrito
from catalogo.models import Variante, Categoria
from core.models import Marca 
from django.contrib.admin.views.decorators import staff_member_required

# --- VISTAS DEL CATÁLOGO ---

def catalogo_general(request):
    """Carga la primera marca al entrar a la web."""
    marca_actual = Marca.objects.filter(activo=True).order_by('id').first()
    lista_marcas = list(Marca.objects.filter(activo=True).order_by('id')) 
    categorias = []
    
    if marca_actual:
        categorias = Categoria.objects.filter(
            marca=marca_actual,
            activo=True
        ).prefetch_related('platos', 'platos__variantes').order_by('orden')
        
    context = {
        'marca_actual': marca_actual,
        'todas_marcas': lista_marcas,
        'categorias': categorias,
    }
    return render(request, 'catalogo/menu.html', context)

def catalogo_por_marca(request, marca_slug):
    """Carga completa si el usuario refresca la página con la URL de la marca."""
    marca_actual = get_object_or_404(Marca, slug=marca_slug)
    lista_marcas = list(Marca.objects.filter(activo=True).order_by('id')) 
    
    categorias = Categoria.objects.filter(
        marca=marca_actual,
        activo=True
    ).prefetch_related('platos', 'platos__variantes').order_by('orden')

    context = {
        'marca_actual': marca_actual,
        'todas_marcas': lista_marcas, 
        'categorias': categorias,
    }
    return render(request, 'catalogo/menu.html', context)

# --- VISTA AJAX (LA MAGIA) ---
def ajax_platos_by_marca(request, marca_slug):
    """
    Esta función NO devuelve la página completa. 
    Solo devuelve el HTML de los platos para insertarlo con JS.
    """
    marca_actual = get_object_or_404(Marca, slug=marca_slug)
    
    categorias = Categoria.objects.filter(
        marca=marca_actual,
        activo=True
    ).prefetch_related('platos', 'platos__variantes').order_by('orden')

    context = {
        'categorias': categorias, # Solo pasamos categorías/platos
    }
    
    # IMPORTANTE: Renderiza SOLO la lista de platos, no el menu.html completo
    return render(request, 'catalogo/platos_list.html', context)

# --- VISTAS DEL CARRITO (Se mantienen igual que tenías) ---
def ver_carrito(request):
    carrito = Carrito(request)
    hay_agotados = False
    ids = carrito.carrito.keys()
    variantes_en_carrito = Variante.objects.filter(id__in=ids).select_related('plato')
    
    for variante in variantes_en_carrito:
        if not variante.esta_disponible:
            hay_agotados = True
            break
            
    return render(request, 'pedidos/carrito_detalle.html', {
        'carrito': carrito,
        'hay_agotados': hay_agotados
    })

def agregar_carrito(request, variante_id):
    carrito = Carrito(request)
    variante = get_object_or_404(Variante, id=variante_id)

    if not variante.esta_disponible:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'error',
                'message': '¡Lo sentimos! Esta opción ya no está disponible.'
            })
        return redirect('menu')

    carrito.agregar(variante.id)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        item = carrito.carrito.get(str(variante.id), {'cantidad': 0})
        return JsonResponse({
            'status': 'ok',
            'cant_total': len(carrito),
            'cant_producto': item['cantidad']
        })

    return redirect('menu')

def sumar_plato(request, variante_id):
    carrito = Carrito(request)
    variante = get_object_or_404(Variante, id=variante_id)

    if not variante.esta_disponible:
         return JsonResponse({'status': 'error', 'message': 'No disponible'})

    carrito.agregar(variante.id)
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        item = carrito.carrito.get(str(variante.id))
        return JsonResponse({
            'status': 'ok',
            'cantidad': item['cantidad'],
            'subtotal': item['cantidad'] * float(variante.precio),
            'total_global': float(carrito.get_total_precio()),
            'total_items': len(carrito),
            'eliminado': False
        })
    return redirect('ver_carrito')

def restar_plato(request, variante_id):
    carrito = Carrito(request)
    variante = get_object_or_404(Variante, id=variante_id)
    
    carrito.restar(variante.id)
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        item = carrito.carrito.get(str(variante_id))
        eliminado = item is None
        cantidad = item['cantidad'] if not eliminado else 0
        subtotal = (cantidad * float(variante.precio)) if not eliminado else 0

        return JsonResponse({
            'status': 'ok',
            'cantidad': cantidad,
            'subtotal': subtotal,
            'total_global': float(carrito.get_total_precio()),
            'total_items': len(carrito),
            'eliminado': eliminado
        })
    return redirect('ver_carrito')

def check_hay_agotados(carrito):
    ids = carrito.carrito.keys()
    variantes = Variante.objects.filter(id__in=ids).select_related('plato')
    for v in variantes:
        if not v.esta_disponible:
            return True
    return False

def eliminar_carrito(request, variante_id):
    carrito = Carrito(request)
    variante = get_object_or_404(Variante, id=variante_id) 
    carrito.eliminar(variante.id)
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
         sigue_bloqueado = check_hay_agotados(carrito)
         return JsonResponse({
            'status': 'ok',
            'total_global': float(carrito.get_total_precio()),
            'total_items': len(carrito),
            'eliminado': True,
            'hay_agotados': sigue_bloqueado
        })
    return redirect('ver_carrito')

def limpiar_carrito(request):
    carrito = Carrito(request)
    carrito.limpiar()
    return redirect('menu')

@staff_member_required 
def toggle_variante_status(request, variante_id):
    variante = get_object_or_404(Variante, id=variante_id)
    variante.activo = not variante.activo 
    variante.save()
    return redirect(request.META.get('HTTP_REFERER', 'admin:index'))