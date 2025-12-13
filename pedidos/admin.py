from django.contrib import admin
from .models import Pedido, DetallePedido
# Register your models here.

class DetalleInline(admin.TabularInline):
    model = DetallePedido
    extra = 0
    readonly_fields = ('subtotal',) # Que nadie edite el subtotal a mano

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('id', 'sede', 'nombre_contacto', 'estado', 'total', 'fecha_creacion')
    list_filter = ('sede', 'estado', 'fecha_creacion')
    search_fields = ('nombre_contacto', 'id')
    inlines = [DetalleInline] # Muestra los platos dentro del pedido
