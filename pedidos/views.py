from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db import models 
from .carrito import Carrito # Importación LOCAL del archivo carrito.py
from catalogo.models import Variante, Categoria, Opcion 
from core.models import Marca 
from django.contrib.admin.views.decorators import staff_member_required
from decimal import Decimal 
from django.template.loader import render_to_string 
import json 
from django.views.decorators.http import require_POST

# --- FUNCIONES AUXILIARES ---

def check_hay_agotados(carrito):
    """Revisa si queda algún item agotado en el carrito."""
    
    ids = carrito.get_variante_ids()
    
    agotados_variantes = Variante.objects.filter(id__in=ids).filter(
        models.Q(activo=False) | 
        models.Q(plato__activo_manual=False) | 
        models.Q(plato__insumos_clave__disponible=False) 
    ).distinct().values_list('id', flat=True)

    agotados_ids = set(agotados_variantes)
    
    for item in carrito.carrito.values():
        if item.get('variante_id') in agotados_ids:
            return True
    return False

def generar_carrito_data_js(carrito):
    """
    Genera el diccionario {variante_id: cantidad} para que JavaScript lo lea.
    """
    carrito_data = {}
    for item in carrito.carrito.values():
        variante_id = item['variante_id']
        cantidad = item['cantidad']
        carrito_data[str(variante_id)] = carrito_data.get(str(variante_id), 0) + cantidad
    # Retornamos el objeto serializado a JSON string
    return json.dumps(carrito_data)


# --- VISTAS DEL CATÁLOGO (Carga Inicial y Retorno del Carrito) ---

def catalogo_general(request):
    """Carga la primera marca al entrar a la web."""
    marca_actual = Marca.objects.filter(activo=True).order_by('id').first()
    lista_marcas = list(Marca.objects.filter(activo=True).order_by('id')) 
    categorias = []
    carrito = Carrito(request) 
    
    if marca_actual:
        categorias = Categoria.objects.filter(
            marca=marca_actual,
            activo=True
        ).prefetch_related('platos', 'platos__variantes').order_by('orden')
        
    context = {
        'marca_actual': marca_actual,
        'todas_marcas': lista_marcas,
        'categorias': categorias,
        'cart_count': carrito.get_total_items(),
        'carrito': carrito,
        # CLAVE: Inyectamos el JSON string de las cantidades para persistencia en JS
        'carrito_data_json': generar_carrito_data_js(carrito), 
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

    carrito = Carrito(request) 
    context = {
        'marca_actual': marca_actual,
        'todas_marcas': lista_marcas, 
        'categorias': categorias,
        'cart_count': carrito.get_total_items(),
        'carrito': carrito,
        'carrito_data_json': generar_carrito_data_js(carrito),
    }
    return render(request, 'catalogo/menu.html', context)

# --- VISTA AJAX (Carga Dinámica al cambiar de pestaña) ---

def ajax_platos_by_marca(request, marca_slug):
    """Devuelve el HTML de los platos y los datos del carrito para actualizar badges."""
    marca_actual = get_object_or_404(Marca, slug=marca_slug)
    carrito = Carrito(request) 

    categorias = Categoria.objects.filter(
        marca=marca_actual,
        activo=True
    ).prefetch_related('platos', 'platos__variantes').order_by('orden')

    context = {
        'categorias': categorias, 
        'carrito': carrito, 
    }
    platos_html = render_to_string('catalogo/platos_list.html', context, request=request)
    
    # Preparamos los datos del carrito para JavaScript
    carrito_data_str = generar_carrito_data_js(carrito)
    
    return JsonResponse({
        'html': platos_html,
        'cart_count': carrito.get_total_items(),
        'carrito_data': json.loads(carrito_data_str), 
    })


# --- VISTAS DE CARRITO Y MODAL ---

def modal_opciones(request, variante_id):
    """Vista para cargar el modal con opciones y precio base."""
    variante = get_object_or_404(Variante.objects.prefetch_related('inclusiones', 'grupos_opciones__opciones'), id=variante_id)
    
    #grupos = variante.grupos_opciones.filter(activo=True).prefetch_related('opciones')

    context = {
        'variante': variante,
        'grupos': variante.grupos_opciones.filter(activo=True),
        'inclusiones': variante.inclusiones.filter(activo=True),
    }
    return render(request, 'catalogo/modal_opciones.html', context)


def agregar_carrito(request, variante_id):
    # 1. Validación de Cantidad
    try:
        cantidad = int(request.POST.get('cantidad', 1))
    except (ValueError, TypeError):
        cantidad = 1

    if cantidad > 10:
        return JsonResponse({'status': 'error', 'message': 'Cantidad excesiva (máx 10).'})
    if cantidad <= 0:
        return JsonResponse({'status': 'error', 'message': 'La cantidad debe ser mayor a 0.'})

    carrito = Carrito(request)
    variante = get_object_or_404(Variante, id=variante_id)

    if not variante.esta_disponible:
        # En lugar de preguntar si es XMLHttpRequest, devolvemos error siempre
        # porque esta vista es para una acción de botón
        return JsonResponse({'status': 'error', 'message': 'No disponible'}, status=400)

    if request.method == 'POST':
        # --- VALIDACIÓN DE OBLIGATORIOS ---
        grupos_obligatorios = variante.grupos_opciones.filter(obligatorio=True, activo=True)
        for grupo in grupos_obligatorios:
            field_name = f'grupo_{grupo.id}'
            if not request.POST.get(field_name):
                # CAMBIO: Siempre devolver JSON si falta algo
                return JsonResponse({
                    'status': 'error', 
                    'message': f'Debes seleccionar: {grupo.nombre}'
                }, status=400)

        # 3. Recopilar y Validar Opciones
        opciones_ids = []
        for key in request.POST:
            if key.startswith('grupo_'):
                valores = request.POST.getlist(key)
                for val in valores:
                    if val.isdigit(): # Validación rápida antes de convertir
                        opciones_ids.append(int(val))
        
        notas = request.POST.get('notas', '').strip()[:200]
        
        # 4. Cálculo de Precio (Lado del Servidor)
        precio_final = variante.precio 
        
        if opciones_ids:
            opciones_validas = Opcion.objects.filter(
                id__in=opciones_ids,
                grupo__variante=variante,
                activo=True
            )
            
            # Verificación de integridad de IDs
            if opciones_validas.count() != len(set(opciones_ids)):
                return JsonResponse({'status': 'error', 'message': 'Selección de opciones no válida.'})

            extra = opciones_validas.aggregate(total=models.Sum('precio_extra'))['total'] or 0
            precio_final += extra
        
        # 5. AGREGAR AL CARRITO (¡Aquí se usa la cantidad!)
        carrito.agregar(
            variante_id=variante.id, 
            cantidad=cantidad,           # <--- FALTABA ESTO
            precio_unitario=precio_final, 
            opciones_ids=opciones_ids, 
            notas=notas
        )

    # 6. Respuesta AJAX
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'ok',
            'cant_total': carrito.get_total_items(),
            'html_ticket': render_to_string('pedidos/carrito_sidebar.html', {'carrito': carrito}, request=request),
            'cant_producto': carrito.get_cantidad_de_variante(variante.id),
            'variante_id': variante.id
        })

    return redirect('menu')


def ver_carrito(request):
    """Vista de detalle del carrito."""
    carrito = Carrito(request)
    hay_agotados = check_hay_agotados(carrito)
                
    return render(request, 'pedidos/carrito_detalle.html', {
        'carrito': carrito,
        'hay_agotados': hay_agotados
    })

@require_POST
def sumar_plato(request, item_key):
    carrito = Carrito(request)
    item_data = carrito.carrito.get(item_key)
    if not item_data:
        return JsonResponse({'status': 'error', 'message': 'Item no encontrado en carrito.'})
    
    variante_id = item_data['variante_id']
    variante = get_object_or_404(Variante, id=variante_id)

    if not variante.esta_disponible:
        return JsonResponse({'status': 'error', 'message': 'No disponible'})

    carrito.agregar(
        variante_id=variante_id, 
        cantidad=1, 
        precio_unitario=Decimal(item_data['precio_unitario']),
        opciones_ids=item_data['opciones'], 
        notas=item_data['notas']
    )
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        item = carrito.carrito.get(item_key)
        cantidad = item['cantidad']
        precio_unitario = Decimal(item['precio_unitario'])
        subtotal = precio_unitario * cantidad

        # --- AGREGADO SOLO LO NECESARIO ---
        html_ticket = render_to_string('pedidos/carrito_sidebar.html', {'carrito': carrito}, request=request)
        # Obtenemos la cantidad total de esta variante específica para el "badge negrito"
        cant_producto = carrito.get_cantidad_de_variante(variante_id)
        # ----------------------------------
        return JsonResponse({
            'status': 'ok',
            'cantidad': cantidad,
            'subtotal': float(subtotal), 
            'total_global': float(carrito.get_total_precio()),
            'total_items': carrito.get_total_items(),
            'eliminado': False,
            'html_ticket': html_ticket, 
            'variante_id': variante_id,
            'cant_producto': cant_producto
        })
    return redirect('ver_carrito')

@require_POST
def restar_plato(request, item_key):
    carrito = Carrito(request)
    item_antes = carrito.carrito.get(item_key)
    variante_id_antes = item_antes['variante_id'] if item_antes else None
    carrito.restar(item_key) 
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        item = carrito.carrito.get(item_key)
        eliminado = item is None
        
        if eliminado:
            cantidad = 0
            subtotal = 0
            hay_agotados_despues = check_hay_agotados(carrito)
        else:
            cantidad = item['cantidad']
            precio_unitario = Decimal(item['precio_unitario'])
            subtotal = precio_unitario * cantidad
            hay_agotados_despues = False
        
        html_ticket = render_to_string('pedidos/carrito_sidebar.html', {'carrito': carrito}, request=request)
        # Calculamos cuánto queda del producto para el "badge negrito"
        cant_producto = 0
        if variante_id_antes:
             cant_producto = carrito.get_cantidad_de_variante(variante_id_antes)
        # ----------------------------------
        return JsonResponse({
            'status': 'ok',
            'cantidad': cantidad,
            'subtotal': float(subtotal),
            'total_global': float(carrito.get_total_precio()),
            'total_items': carrito.get_total_items(),
            'eliminado': eliminado,
            'hay_agotados': hay_agotados_despues,
            'html_ticket': html_ticket,
            'variante_id': variante_id_antes,
            'cant_producto': cant_producto
        })
    return redirect('ver_carrito')

@require_POST
def eliminar_carrito(request, item_key):
    carrito = Carrito(request)
    item = carrito.carrito.get(item_key)
    variante_id = item['variante_id'] if item else None
    carrito.eliminar(item_key) 
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        sigue_bloqueado = check_hay_agotados(carrito)
        html_ticket = render_to_string('pedidos/carrito_sidebar.html', {'carrito': carrito}, request=request)
        
        # OBTENEMOS EL DICCIONARIO ACTUALIZADO DE CANTIDADES {variante_id: cantidad}
        # Usamos tu función auxiliar que ya existe
        carrito_data_str = generar_carrito_data_js(carrito) 
        cant_producto_restante = 0
        if variante_id:
            cant_producto_restante = carrito.get_cantidad_de_variante(variante_id)

        return JsonResponse({
            'status': 'ok',
            'cant_total': carrito.get_total_items(),
            'total_global': float(carrito.get_total_precio()),
            'html_ticket': html_ticket,
            'total_items': carrito.get_total_items(),
            'eliminado': True,
            'variante_id': variante_id,
            'hay_agotados': sigue_bloqueado,
            # Enviamos el diccionario real para que JS refresque todos los badges
            'carrito_data': json.loads(carrito_data_str),
            'cant_producto': cant_producto_restante

        })
    return redirect('ver_carrito')


@require_POST
def limpiar_carrito(request):
    carrito = Carrito(request)
    carrito.limpiar()
    
    # En lugar de redirect, enviamos una señal de éxito en JSON
    return JsonResponse({
        'status': 'ok',
        'message': 'Carrito vaciado correctamente'
    })

@staff_member_required 
def toggle_variante_status(request, variante_id):
    """Vista de administración para cambiar el estado de disponibilidad."""
    variante = get_object_or_404(Variante, id=variante_id)
    variante.activo = not variante.activo 
    variante.save()
    return redirect(request.META.get('HTTP_REFERER', 'admin:index'))


def iniciar_pago(request):
    return render(request, 'pedidos/checkout.html', {})