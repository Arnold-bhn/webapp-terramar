from django.contrib import admin
from .models import InsumoCritico, Categoria, Plato, Variante
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from django.urls import reverse

# Register your models here.
# Esto permite poner los precios DENTRO de la pantalla del Plato
'''class VarianteInline(admin.TabularInline):
    model = Variante
    extra = 1
'''
# 1. Configuración de la "Tablita" dentro del Plato
class VarianteInline(admin.TabularInline):
    model = Variante
    # 'extra = 0' hace que no salgan filas vacías extra, 
    # pero si no ves nada, prueba cambiarlo a 1 para ver si aparece al menos la fila de "Agregar nuevo".
    extra = 0 
    
    # Campos que quieres ver y editar ahí mismo
    fields = ('nombre', 'precio', 'activo')
    
    # IMPORTANTE: Quitamos 'classes': ['collapse'] para que SIEMPRE se vean
    
    # Esto ayuda si tienes muchas variantes, para que no ocupen tanto espacio vertical
    show_change_link = True

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
    # 1. AGREGAMOS 'control_variantes' AQUI EN LA LISTA VISIBLE
    list_display = ('nombre_completo', 'categoria', 'orden', 'activo_manual', 'control_variantes')
    
    list_filter = ('marca', 'categoria')
    list_editable = ('orden', 'activo_manual')
    search_fields = ('nombre',)
    # inlines = [VarianteInline] # Descomenta esto si tienes tu Inline definido arriba
    filter_horizontal = ('insumos_clave',)

    @admin.display(description='Plato', ordering='nombre')
    def nombre_completo(self, obj):
        return str(obj)

    # --- AQUÍ ESTÁ TU MÉTODO ARREGLADO ---
    def control_variantes(self, obj):
        html_parts = []
        
        # Recorremos todas las variantes de este plato
        for variante in obj.variantes.all():
            if variante.activo:
                color = "#198754" # Verde (ON)
                estado = "ON"
                opacity = "1"
            else:
                color = "#dc3545" # Rojo (OFF)
                estado = "OFF"
                opacity = "0.6" # Un poco transparente si está apagado
            
            # Ahora esta línea YA FUNCIONARÁ porque creamos la URL en el Paso 2
            url = reverse('toggle_variante', args=[variante.id])
            
            boton = f"""
            <a href="{url}" style="
                display: inline-block;
                padding: 4px 8px;
                margin: 2px;
                background-color: {color};
                color: white;
                text-decoration: none;
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
                border: 1px solid #000;
                opacity: {opacity};
                box-shadow: 1px 1px 2px rgba(0,0,0,0.2);
            " title="Clic para cambiar estado">
                {variante.nombre}: {estado}
            </a>
            """
            html_parts.append(boton)
        
        if not html_parts:
            return "-"

        return mark_safe("".join(html_parts))
    
    control_variantes.short_description = "Variantes (Clic para alternar)"


# Registramos Variante suelta también por si necesitamos buscar precios específicos
@admin.register(Variante)
class VarianteAdmin(admin.ModelAdmin):
    # Columnas que verás
    list_display = ('obtener_nombre_completo', 'precio', 'activo')
    
    # ESTO ES LA MAGIA: Te permite editar el check sin entrar
    list_editable = ('activo', 'precio') 
    
    # Filtros laterales para encontrar rápido (por marca o categoría del plato padre)
    list_filter = ('activo', 'plato__marca', 'plato__categoria')
    
    # Buscador (busca por nombre de variante O nombre del plato)
    search_fields = ('nombre', 'plato__nombre')
    
    # Ordenar por plato para que salgan agrupados
    ordering = ('plato',)

    # Función para que en la lista se vea "Ceviche - Personal" y no solo "Personal"
    @admin.display(description='Producto')
    def obtener_nombre_completo(self, obj):
        return f"{obj.plato.nombre} - {obj.nombre}"