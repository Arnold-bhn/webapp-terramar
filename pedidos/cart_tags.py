from django import template
from pedidos.carrito import Carrito # Asegúrate de que esta ruta sea correcta

register = template.Library()

@register.filter
def cantidad_en_carrito(variante, request):
    # Lógica para obtener el carrito y devolver la cantidad de esta variante
    carrito = Carrito(request)
    return carrito.carrito.get(str(variante.id), {}).get('cantidad', 0)