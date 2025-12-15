from django.db import models
from core.models import Marca, Sede
# Create your models here.

# Gestion de Stokc Crítico
class InsumoCritico(models.Model):
    sede = models.ForeignKey(Sede, on_delete=models.CASCADE, related_name='insumos')
    nombre = models.CharField(max_length=50, help_text="Ej: Pescado, Limón, Gas")
    disponible = models.BooleanField(default=True, help_text="Desmarcar para apagar todos los platos relacionados")

    def __str__(self):
        estado = "✅" if self.disponible else "❌ AGOTADO"
        return f"{self.nombre} ({self.sede.nombre}) - {estado}"

# Categorias (Entradas, Bebidas, Fondos, etc)
class Categoria(models.Model):
    marca = models.ForeignKey(Marca, on_delete=models.CASCADE, related_name='categorias')
    nombre = models.CharField(max_length=50)
    nombre_singular = models.CharField(
        max_length=50, 
        blank=True, 
        null=True, 
        help_text="Ej: 'Chicharron' (para que salga 'Chicharron de Pollo')"
    )
    #imagen = models.ImageField(upload_to='categorias/', blank=True, null=True)
    orden = models.IntegerField(default=0, help_text="1 sale primero, 2 después ...")
    activo = models.BooleanField(default=True)
    class Meta:
        ordering = ['orden']
    def __str__(self):
        return f"{self.marca.nombre} - {self.nombre}"
    
# Platos
class Plato(models.Model):
    marca = models.ForeignKey(Marca, on_delete=models.CASCADE, related_name='platos')
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='platos')
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, help_text="Descripción para la web")
    imagen = models.ImageField(upload_to='platos/', blank=True, null=True)
    activo_manual = models.BooleanField(default=True, help_text="Apagar este plato manualmente")
    # Si se acaba el 'Insumo Crítico', el plato se apaga solo
    insumos_clave = models.ManyToManyField(InsumoCritico, blank=True)
    orden = models.IntegerField(default=0, help_text="1 sale primero, 2 después...")
    # --- CONFIGURACIÓN DE ORDENAMIENTO ---
    class Meta:
        # Ordena primero por 'orden' (ascendente) y luego por 'nombre' (si tienen el mismo número)
        ordering = ['orden', 'nombre']
    def __str__(self):
        # 1. Intentamos usar el singular (si el admin lo escribió)
        if self.categoria.nombre_singular:
            prefijo = self.categoria.nombre_singular
        else:
            # 2. Si no, usamos el plural por defecto
            prefijo = self.categoria.nombre
            
        return f"{prefijo} de {self.nombre}"
    
    # --- AQUÍ ESTÁ LA MAGIA (El Portero) ---
    @property
    def esta_disponible(self):
        """
        Devuelve True SOLO si:
        1. El interruptor manual está encendido (activo_manual=True)
        2. Y ADEMÁS, no hay ningún insumo crítico marcado como agotado.
        """
        # 1. Revisar interruptor manual
        if not self.activo_manual:
            return False
            
        # 2. Revisar insumos automáticos
        # Buscamos si existe algun insumo vinculado que tenga disponible=False
        hay_insumos_agotados = self.insumos_clave.filter(disponible=False).exists()
        
        if hay_insumos_agotados:
            return False # Bloqueamos el paso
            
        return True # Todo ok, pase usted



# --- NUEVAS CLASES PARA EL SISTEMA DE OPCIONES ---

class GrupoOpciones(models.Model):
    """
    Define un grupo de elecciones. Ej: 'Guarniciones', 'Salsas', 'Término de la carne'.
    """
    nombre = models.CharField(max_length=100, verbose_name="Nombre del Grupo (Ej: Guarniciones)")
    
    # Lógica de Selección
    seleccion_multiple = models.BooleanField(
        default=False, 
        verbose_name="¿Permitir varios?",
        help_text="Check = Checkboxes (Varios). Sin check = Radio Buttons (Solo uno)."
    )
    obligatorio = models.BooleanField(
        default=False, 
        verbose_name="¿Es obligatorio?",
        help_text="El cliente NO podrá agregar al carrito sin elegir esto."
    )
    minimo = models.PositiveIntegerField(default=0, verbose_name="Mínimo a elegir")
    maximo = models.PositiveIntegerField(default=1, verbose_name="Máximo a elegir")
    
    activo = models.BooleanField(default=True)

    def __str__(self):
        tipo = "Multi" if self.seleccion_multiple else "Unico"
        req = "Obligatorio" if self.obligatorio else "Opcional"
        return f"{self.nombre} [{tipo} - {req}]"

    class Meta:
        verbose_name = "Grupo de Opciones"
        verbose_name_plural = "Grupos de Opciones"


class Opcion(models.Model):
    """
    Cada ítem seleccionable. Ej: 'Papas', 'Camote', 'Mayonesa'.
    """
    grupo = models.ForeignKey(GrupoOpciones, on_delete=models.CASCADE, related_name='opciones')
    nombre = models.CharField(max_length=100)
    precio_extra = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, 
        help_text="Costo adicional (0.00 si es gratis)"
    )
    activo = models.BooleanField(default=True)

    def __str__(self):
        if self.precio_extra > 0:
            return f"{self.nombre} (+ S/{self.precio_extra})"
        return self.nombre


# --- TU CLASE VARIANTE ACTUALIZADA ---

class Variante(models.Model):
    plato = models.ForeignKey(Plato, on_delete=models.CASCADE, related_name='variantes')
    nombre = models.CharField(max_length=50, default="Estándar", help_text="Ej: Personal, Fuente, Vaso")
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    
    # === NUEVA CONEXIÓN AQUÍ ===
    grupos_opciones = models.ManyToManyField(
        GrupoOpciones, 
        blank=True, 
        verbose_name="Personalización disponible"
    )
    # ===========================

    activo = models.BooleanField(default=True, verbose_name="¿Disponible?", help_text="Desmarcar si se agotó solo esta presentación")
    
    def __str__(self):
        return f"{self.plato.nombre} - {self.nombre} (S/ {self.precio})"

    @property
    def esta_disponible(self):
        return self.activo and self.plato.esta_disponible
    # En catalogo/models.py, dentro de class Variante(...):

    def tiene_opciones(self):
        return self.grupos_opciones.filter(activo=True).exists()