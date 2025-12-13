from django.db import models
from django.core.validators import MinValueValidator
from core.models import Sede, Mesa, Cliente, PerfilEmpleado
from catalogo.models import Variante # El producto con precio
# Create your models here.
class Pedido(models.Model):
    """
    EL TICKET DE VENTA (CABECERA)
    """
    # 1. Contexto
    sede = models.ForeignKey(Sede, on_delete=models.CASCADE, related_name='pedidos')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    # 2. Cliente (Híbrido)
    # Si es cliente fiel, usamos este campo:
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True)
    # Si es invitado (o para el nombre en el ticket), usamos estos:
    nombre_contacto = models.CharField(max_length=100, default="Invitado")
    telefono_contacto = models.CharField(max_length=20, blank=True)
    # 3. Datos de Entrega
    TIPOS = [('MESA', 'Mesa'), ('DELIVERY', 'Delivery'), ('RECOJO', 'Para Llevar')]
    tipo_servicio = models.CharField(max_length=20, choices=TIPOS, default='MESA')
    mesa = models.ForeignKey(Mesa, on_delete=models.SET_NULL, null=True, blank=True)
    direccion_entrega = models.CharField(max_length=200, blank=True)
    # 4. Dinero y Estado
    ESTADOS = [
        ('PENDIENTE', '🟡 Pendiente'),
        ('CONFIRMADO', '🟠 En Cocina'),
        ('LISTO', '🔵 Listo para Servir'),
        ('ENTREGADO', '🟢 Finalizado'),
        ('CANCELADO', '🔴 Anulado')
    ]
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    metodo_pago = models.CharField(max_length=50, default='EFECTIVO')
    def __str__(self):
        return f"Pedido #{self.id} - {self.nombre_contacto}"

class DetallePedido(models.Model):
    """
    LOS PLATOS DEL PEDIDO (ITEMS)
    """
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='detalles')
    variante = models.ForeignKey(Variante, on_delete=models.PROTECT) # El plato y precio específico
    cantidad = models.PositiveIntegerField(default=1)
    # Guardamos el precio del momento (snapshot) por si sube mañana
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    notas = models.CharField(max_length=200, blank=True, help_text="Ej: Sin picante")
    def save(self, *args, **kwargs):
        # Auto-calculo del subtotal de esta línea
        self.subtotal = self.precio_unitario * self.cantidad
        super().save(*args, **kwargs)
    def __str__(self):
        return f"{self.cantidad}x {self.variante.plato.nombre}"
    
