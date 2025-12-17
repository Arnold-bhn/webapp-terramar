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
    carrito = Carrito(request)
    variante = get_object_or_404(Variante, id=variante_id)

    if not variante.esta_disponible:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error','message': '¡Lo sentimos! Esta opción ya no está disponible.'})
        return redirect('menu')

    if request.method == 'POST':
        # --- BLINDAJE DE SEGURIDAD: VALIDACIÓN DE OBLIGATORIOS ---
        # Verificamos qué grupos son realmente obligatorios en la DB para esta variante
        grupos_obligatorios = variante.grupos_opciones.filter(obligatorio=True, activo=True)
        
        for grupo in grupos_obligatorios:
            field_name = f'grupo_{grupo.id}'
            # Si el ID del grupo no está en el POST o no tiene valor seleccionado
            if field_name not in request.POST or not request.POST.get(field_name):
                mensaje_error = f'Debes seleccionar una opción para: {grupo.nombre}'
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'status': 'error', 'message': mensaje_error})
                return redirect('menu')

        # 1. Recopilar opciones seleccionadas
        opciones_seleccionadas = []
        for key in request.POST:
            if key.startswith('grupo_'):
                valores = request.POST.getlist(key)
                for val in valores:
                    try:
                        opciones_seleccionadas.append(int(val))
                    except (ValueError, TypeError):
                        continue
        
        notas = request.POST.get('notas', '').strip()
        
        # 2. CÁLCULO DE PRECIO FINAL (Inmune a hacks de cliente)
        precio_final = variante.precio 
        if opciones_seleccionadas:
            resultado = Opcion.objects.filter(
                id__in=opciones_seleccionadas,
                activo=True
            ).aggregate(total_extra=models.Sum('precio_extra'))
            
            opciones_extras = resultado.get('total_extra')
            if opciones_extras:
                precio_final += opciones_extras
        
        # 3. AGREGAR AL CARRITO
        carrito.agregar(
            variante_id=variante.id, 
            precio_unitario=precio_final, 
            opciones_ids=opciones_seleccionadas, 
            notas=notas
        )

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        item_count = carrito.get_cantidad_de_variante(variante.id)
        return JsonResponse({
            'status': 'ok',
            'cant_total': carrito.get_total_items(),
            'cant_producto': item_count
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
        
        return JsonResponse({
            'status': 'ok',
            'cantidad': cantidad,
            'subtotal': float(subtotal), 
            'total_global': float(carrito.get_total_precio()),
            'total_items': carrito.get_total_items(),
            'eliminado': False
        })
    return redirect('ver_carrito')


def restar_plato(request, item_key):
    carrito = Carrito(request)
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

        return JsonResponse({
            'status': 'ok',
            'cantidad': cantidad,
            'subtotal': float(subtotal),
            'total_global': float(carrito.get_total_precio()),
            'total_items': carrito.get_total_items(),
            'eliminado': eliminado,
            'hay_agotados': hay_agotados_despues 
        })
    return redirect('ver_carrito')


def eliminar_carrito(request, item_key):
    carrito = Carrito(request)
    carrito.eliminar(item_key) 
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        sigue_bloqueado = check_hay_agotados(carrito)
        
        return JsonResponse({
            'status': 'ok',
            'total_global': float(carrito.get_total_precio()),
            'total_items': carrito.get_total_items(),
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
    """Vista de administración para cambiar el estado de disponibilidad."""
    variante = get_object_or_404(Variante, id=variante_id)
    variante.activo = not variante.activo 
    variante.save()
    return redirect(request.META.get('HTTP_REFERER', 'admin:index'))


def iniciar_pago(request):
    return render(request, 'pedidos/checkout.html', {})