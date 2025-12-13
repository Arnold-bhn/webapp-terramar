from django.contrib import admin
from .models import InsumoCritico, Categoria, Plato, Variante
# Register your models here.
# Esto permite poner los precios DENTRO de la pantalla del Plato
class VarianteInline(admin.TabularInline):
    model = Variante
    extra = 1

@admin.register(InsumoCritico)
class InsumoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'sede', 'disponible')
    list_editable = ('disponible',) # Switch rápido
    list_filter = ('sede',)

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'marca', 'orden', 'activo')
    list_editable = ('orden', 'activo')
    list_filter = ('marca',)

@admin.register(Plato)
class PlatoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'activo_manual')
    list_filter = ('marca', 'categoria')
    list_editable = ('activo_manual',)
    search_fields = ('nombre',)
    inlines = [VarianteInline] # Aquí insertamos la tabla de precios
    filter_horizontal = ('insumos_clave',)

# Registramos Variante suelta también por si necesitamos buscar precios específicos
@admin.register(Variante)
class VarianteAdmin(admin.ModelAdmin):
    list_display = ('plato', 'nombre', 'precio')
    search_fields = ('plato__nombre',)

