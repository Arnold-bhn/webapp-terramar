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

# En catalogo/models.py
class Variante(models.Model):
    plato = models.ForeignKey(Plato, on_delete=models.CASCADE, related_name='variantes')
    nombre = models.CharField(max_length=50, default="Estándar", help_text="Ej: Personal, Fuente, Vaso")
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    
    # --- NUEVO CAMPO: Interruptor individual ---
    activo = models.BooleanField(default=True, verbose_name="¿Disponible?", help_text="Desmarcar si se agotó solo esta presentación")
    
    def __str__(self):
        return f"{self.plato.nombre} - {self.nombre} (S/ {self.precio})"

    # --- LÓGICA DE DISPONIBILIDAD ACTUALIZADA ---
    @property
    def esta_disponible(self):
        """
        La variante está disponible SI:
        1. Ella misma está activa (activo=True).
        2. Y SU PAPÁ (El Plato) también está disponible (tiene insumos y está activo).
        """          
        # 2. Chequeo del padre (¿Queda pescado para cocinar?)
        return self.activo and self.plato.esta_disponible
    
