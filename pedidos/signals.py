from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Sum
from .models import DetallePedido

@receiver([post_save, post_delete], sender=DetallePedido)
def actualizar_total_pedido(sender, instance, **kwargs):
    pedido = instance.pedido
    # Suma todos los subtotales de este pedido
    resultado = pedido.detalles.aggregate(total_calculado=Sum('subtotal'))
    pedido.total = resultado['total_calculado'] or 0.00
    pedido.save()