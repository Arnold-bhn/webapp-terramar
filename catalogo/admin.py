from django.contrib import admin
from .models import InsumoCritico, Categoria, Plato, Variante, GrupoOpciones, Opcion, Inclusion
from django.utils.safestring import mark_safe
from django.urls import reverse

# ==========================================
# 1. GESTIÓN DE INSUMOS Y CATEGORÍAS
# ==========================================
@admin.register(InsumoCritico)
class InsumoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'sede', 'disponible')
    list_editable = ('disponible',)

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'marca', 'orden')
    list_editable = ('orden',)

# ==========================================
# 2. GESTIÓN DE GRUPOS DE OPCIONES
# ==========================================
class OpcionInline(admin.TabularInline):
    """
    Las opciones (Papas, Camote) sí se ven mejor en tabla pequeña
    """
    model = Opcion
    extra = 1

@admin.register(GrupoOpciones)
class GrupoOpcionesAdmin(admin.ModelAdmin):
    inlines = [OpcionInline]
    list_display = ('nombre', 'seleccion_multiple', 'obligatorio', 'activo')
    search_fields = ['nombre']

# ==========================================
# 3. GESTIÓN DE PLATOS Y VARIANTES (MODO BLOQUE)
# ==========================================

# CAMBIO CLAVE AQUÍ: Usamos StackedInline en lugar de TabularInline
class VarianteInline(admin.StackedInline):
    model = Variante
    extra = 0
    
    # filter_horizontal se ve MUCHO mejor en StackedInline (ocupa todo el ancho)
    filter_horizontal = ('grupos_opciones', 'inclusiones') 
    
    fields = (
        ('nombre', 'precio', 'activo'), # Estos 3 en una sola fila para ahorrar espacio vertical
        'grupos_opciones',             # Esto en su propia fila grande
        'inclusiones',
    )
    
    show_change_link = True

@admin.register(Plato)
class PlatoAdmin(admin.ModelAdmin):
    # Mantenemos tu semáforo visual en la lista principal
    list_display = ('nombre_completo', 'categoria', 'orden', 'activo_manual', 'control_variantes')
    list_filter = ('marca', 'categoria')
    list_editable = ('orden', 'activo_manual')
    search_fields = ('nombre',)
    
    filter_horizontal = ('insumos_clave',)
    
    # Aquí cargamos las variantes en bloques grandes
    inlines = [VarianteInline]

    @admin.display(description='Plato', ordering='nombre')
    def nombre_completo(self, obj):
        return str(obj)

    # --- SEMÁFORO VISUAL (Tu requerimiento anterior) ---
    def control_variantes(self, obj):
        html_parts = []
        
        for variante in obj.variantes.all():
            if variante.activo:
                color = "#198754" # Verde
                opacity = "1"
            else:
                color = "#dc3545" # Rojo
                opacity = "0.6"
            
            # Protección por si no existe la URL aún
            try:
                url = reverse('toggle_variante_status', args=[variante.id]) 
                href = f'href="{url}"'
            except:
                href = 'href="#" onclick="return false;"'

            boton = f"""
            <a {href} style="
                display: inline-block; padding: 4px 8px; margin: 2px;
                background-color: {color}; color: white; text-decoration: none;
                border-radius: 4px; font-size: 11px; font-weight: bold;
                opacity: {opacity}; border: 1px solid #000;
            ">
                {variante.nombre}
            </a>
            """
            html_parts.append(boton)
        
        if not html_parts:
            return "-"
        return mark_safe("".join(html_parts))
    
    control_variantes.short_description = "Variantes (Click cambiar)"

# Registro individual de variantes (opcional, pero útil)
@admin.register(Variante)
class VarianteAdmin(admin.ModelAdmin):
    list_display = ('obtener_nombre_completo', 'precio', 'activo')
    list_editable = ('activo', 'precio') 
    list_filter = ('activo', 'plato__marca', 'plato__categoria')
    search_fields = ('nombre', 'plato__nombre')
    filter_horizontal = ('grupos_opciones', 'inclusiones') 

    @admin.display(description='Producto')
    def obtener_nombre_completo(self, obj):
        return f"{obj.plato.nombre} - {obj.nombre}"
    

@admin.register(Inclusion)
class InclusionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activo')
    list_editable = ('activo',)
    search_fields = ('nombre',)