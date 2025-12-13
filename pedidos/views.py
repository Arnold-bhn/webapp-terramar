from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .carrito import Carrito
from catalogo.models import Variante # IMPORTANTE: Importamos desde catalogo
from django.contrib.admin.views.decorators import staff_member_required

# --- VISTA DEL CARRITO ---
def ver_carrito(request):
    carrito = Carrito(request)
    
    # --- LÓGICA RECUPERADA: DETECTAR AGOTADOS ---
    hay_agotados = False
    
    # Obtenemos los IDs de los productos en el carrito
    ids = carrito.carrito.keys()
    
    # Consultamos a la base de datos para ver su estado ACTUAL
    # Usamos select_related('plato') para optimizar y no hacer muchas consultas
    variantes_en_carrito = Variante.objects.filter(id__in=ids).select_related('plato')
    
    for variante in variantes_en_carrito:
        # Preguntamos si está disponible (gracias al fix que hiciste en models.py)
        if not variante.esta_disponible:
            hay_agotados = True
            break # Con encontrar uno agotado es suficiente para bloquear
            
    return render(request, 'pedidos/carrito_detalle.html', {
        'carrito': carrito,
        'hay_agotados': hay_agotados # <--- Pasamos la bandera al HTML
    })

# --- AGREGAR (Desde el Menú) ---
def agregar_carrito(request, variante_id):
    carrito = Carrito(request)
    variante = get_object_or_404(Variante, id=variante_id)

    # 1. VALIDACIÓN DE DISPONIBILIDAD (Tu lógica de insumos/manual)
    # Como no tienes un stock numérico (ej: 10), validamos si el plato sigue activo
    if not variante.plato.esta_disponible:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'error',
                'message': '¡Lo sentimos! Este plato se acaba de agotar.'
            })
        return redirect('menu')

    # 2. AGREGAR AL CARRITO
    carrito.agregar(variante.id)

    # 3. RESPUESTA AJAX (Para que se actualicen los numeritos sin recargar)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Obtenemos la cantidad actual en el carrito para devolverla
        item = carrito.carrito.get(str(variante.id), {'cantidad': 0})
        return JsonResponse({
            'status': 'ok',
            'cant_total': len(carrito),
            'cant_producto': item['cantidad']
        })

    return redirect('menu')

# --- SUMAR (+1 en el Carrito) ---
def sumar_plato(request, variante_id):
    carrito = Carrito(request)
    variante = get_object_or_404(Variante, id=variante_id)

    # Validamos disponibilidad nuevamente por si se acabó mientras navegaba
    if not variante.plato.esta_disponible:
         return JsonResponse({
             'status': 'error', 
             'message': 'Plato ya no disponible'
         })

    carrito.agregar(variante.id)
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        item = carrito.carrito.get(str(variante.id))
        return JsonResponse({
            'status': 'ok',
            'cantidad': item['cantidad'],
            'subtotal': item['cantidad'] * float(variante.precio), # Calculo rápido para JS
            'total_global': float(carrito.get_total_precio()),
            'total_items': len(carrito),
            'eliminado': False
        })
    return redirect('ver_carrito')

# --- RESTAR (-1 en el Carrito) ---
def restar_plato(request, variante_id):
    carrito = Carrito(request)
    variante = get_object_or_404(Variante, id=variante_id)
    
    carrito.restar(variante.id)
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        item = carrito.carrito.get(str(variante_id))
        eliminado = item is None # Si ya no existe, es que se eliminó
        
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
    """Revisa si queda algún producto agotado en el carrito"""
    ids = carrito.carrito.keys()
    # Importante: select_related para eficiencia
    variantes = Variante.objects.filter(id__in=ids).select_related('plato')
    for v in variantes:
        if not v.esta_disponible:
            return True # Aún hay al menos uno agotado
    return False # El carrito está limpio

# --- ELIMINAR (Bote de basura) ---
def eliminar_carrito(request, variante_id):
    carrito = Carrito(request)
    variante = get_object_or_404(Variante, id=variante_id) 
    
    carrito.eliminar(variante.id)
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
         # 1. Calculamos si, tras eliminar, sigue habiendo problemas
         sigue_bloqueado = check_hay_agotados(carrito)

         return JsonResponse({
            'status': 'ok',
            'total_global': float(carrito.get_total_precio()),
            'total_items': len(carrito),
            'eliminado': True,
            'hay_agotados': sigue_bloqueado # <--- ENVIAMOS ESTE DATO NUEVO
        })
    return redirect('ver_carrito')

# --- LIMPIAR TODO ---
def limpiar_carrito(request):
    carrito = Carrito(request)
    carrito.limpiar()
    return redirect('menu')


@staff_member_required # Solo administradores pueden usar esto
def toggle_variante_status(request, variante_id):
    variante = get_object_or_404(Variante, id=variante_id)
    # Invertimos el estado: Si es True pasa a False, y viceversa
    variante.activo = not variante.activo 
    variante.save()
    
    # Nos devuelve a la página anterior (la lista del admin)
    return redirect(request.META.get('HTTP_REFERER', 'admin:index'))