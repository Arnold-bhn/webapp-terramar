from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User, Group
from .models import Marca, ConfiguracionVisual, Sede, Mesa, PerfilEmpleado, Cliente

# Configuración de Textos del Panel
# 1. Configuración General del Panel
#admin.site.site_header = "Terramar Admin"
#admin.site.site_title = "Portal de Gestión"
#admin.site.index_title = "Panel de Control"
#admin.site.unregister(Group) # Opcional: Para limpiar la vista
# NOTA: Cambiamos 'ModelAdmin' (de Unfold) por 'admin.ModelAdmin' (Estándar)

# 2. Integración de Usuarios (Ver Empleado/Cliente dentro del Usuario)
class EmpleadoInline(admin.StackedInline):
    model = PerfilEmpleado
    can_delete = False
    verbose_name_plural = 'Rol de Empleado'

class ClienteInline(admin.StackedInline):
    model = Cliente
    can_delete = False
    verbose_name_plural = 'Datos de Cliente (Fidelización)'

class UserAdmin(BaseUserAdmin):
    inlines = (EmpleadoInline, ClienteInline)

# Reemplazamos el admin de usuarios original
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# 3. Administración de Marca e Identidad
@admin.register(Marca)
class MarcaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activo', 'color_coorporativo')
    list_editable = ('activo',)

@admin.register(ConfiguracionVisual)
class VisualAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'marca', 'activo', 'efecto_especial', 'color_principal')
    list_editable = ('activo', 'efecto_especial') # Edición rápida del switch
    list_filter = ('marca', 'efecto_especial')
    
    fieldsets = (
        ('Gestión', {'fields': ('marca', 'nombre', 'activo')}),
        ('Apariencia', {'fields': ('color_principal', 'color_secundario', 'color_fondo', 'efecto_especial')}),
        ('Textos', {'fields': ('mensaje_barra', 'mensaje_despedida')}),
    )

# 4. Administración Operativa (Sedes y Mesa)
@admin.register(Sede)
class SedeAdmin(admin.ModelAdmin):
    # Esto habilitará la edición rápida tipo Excel en la lista
    list_display = ('nombre', 'estado_actual', 'tiempo_extra_saturacion', 'tiempo_delivery_base')
    list_editable = ('estado_actual', 'tiempo_extra_saturacion')
    list_filter = ('estado_actual',)

@admin.register(Mesa)
class MesaAdmin(admin.ModelAdmin):
    list_display = ('numero', 'sede', 'estado', 'capacidad')
    list_filter = ('sede', 'estado')
    search_fields = ('numero',)
    #list_editable = ('estado',)

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'dni', 'telefono', 'nivel')
    search_fields = ('dni', 'usuario__username')