from decimal import Decimal
from django.conf import settings
from catalogo.models import Variante

class Carrito:
    def __init__(self, request):
        self.session = request.session
        # USAMOS UNA SOLA CLAVE PARA LA SESIÓN
        cart = self.session.get('carrito_terramar')
        if not cart:
            cart = self.session['carrito_terramar'] = {}
        self.carrito = cart

    def agregar(self, variante_id, cantidad=1):
        variante_id = str(variante_id)
        if variante_id not in self.carrito:
            self.carrito[variante_id] = {
                'cantidad': 0,
                'precio': 0
            }
        self.carrito[variante_id]['cantidad'] += int(cantidad)
        self.guardar()

    def restar(self, variante_id):
        variante_id = str(variante_id)
        if variante_id in self.carrito:
            self.carrito[variante_id]['cantidad'] -= 1
            if self.carrito[variante_id]['cantidad'] <= 0:
                self.eliminar(variante_id)
            else:
                self.guardar()

    def eliminar(self, variante_id):
        variante_id = str(variante_id)
        if variante_id in self.carrito:
            del self.carrito[variante_id]
            self.guardar()

    def limpiar(self):
        self.session['carrito_terramar'] = {}
        self.session.modified = True

    def guardar(self):
        self.session.modified = True

    def __len__(self):
        return sum(item['cantidad'] for item in self.carrito.values())

    def get_total_precio(self):
        total = Decimal('0.00')
        ids = self.carrito.keys()
        variantes = Variante.objects.filter(id__in=ids)
        for var in variantes:
            cantidad = self.carrito[str(var.id)]['cantidad']
            total += var.precio * cantidad
        return total

    def iterar_detalles(self):
        """Devuelve los objetos completos para el HTML"""
        ids = self.carrito.keys()
        variantes = Variante.objects.filter(id__in=ids)
        cart_copy = self.carrito.copy()
        
        for var in variantes:
            cart_copy[str(var.id)]['producto'] = var
            cart_copy[str(var.id)]['subtotal'] = var.precio * cart_copy[str(var.id)]['cantidad']
            yield cart_copy[str(var.id)]