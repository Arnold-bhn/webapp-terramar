from .carrito import Carrito

def carrito_actual(request):
    return {'carrito': Carrito(request)}