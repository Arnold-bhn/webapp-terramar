from django import template

register = template.Library()

@register.filter(name='cantidad_en_carrito')
def cantidad_en_carrito(carrito, producto_id):
    # Intentamos buscar el ID (como string) dentro del diccionario del carrito
    if not carrito or not carrito.carrito:
        return 0
    
    item = carrito.carrito.get(str(producto_id))
    if item:
        return item['cantidad']
    return 0