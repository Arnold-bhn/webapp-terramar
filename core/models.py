from django.db import models
from django.contrib.auth.models import User
# ==============================================================================
# 1. IDENTIDAD Y DISEÑO (MARCA BLANCA)
# ==============================================================================
class Marca(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True, help_text="Identificador para URL (Ej: terramar)")
    color_coorporativo = models.CharField(max_length=7, default="#003366")
    activo = models.BooleanField(default=True)
    #logo = models.ImageField(upload_to='marcas/', blank=True, null=True)
    def __str__(self):
        return self.nombre

class ConfiguracionVisual(models.Model):
    nombre = models.CharField(max_length=50, help_text="Ej: Tema Verano 2025")
    marca = models.ForeignKey(Marca, on_delete=models.CASCADE, related_name='temas')
    activo = models.BooleanField(default=False, help_text="Al activar este, se desactivan los demás automáticamente")

    # --- Personalización Visual ---
    color_principal = models.CharField(max_length=7, default="#003366", help_text="Barra superior y botones principales")
    color_secundario = models.CharField(max_length=7, default="#FF6B4A", help_text="Ofertas y botones de acción")
    color_fondo = models.CharField(max_length=7, default="#F4F7F6", help_text="Fondo de la página")

    # --- Mensajes ---
    mensaje_barra = models.CharField(max_length=200, default="Bienvenido", help_text="Texto arriba del todo")
    mensaje_despedida = models.CharField(max_length=200, default="¡Gracias por tu compra!", help_text="Mensaje al finalizar")

    # --- Efectos Especiales ---
    EFECTOS = [
        ('NINGUNO', 'Sin efectos (Limpio)'),
        ('NIEVE', '❄️ Caída de Nieve (Navidad)'),
        ('CONFETI', '🎉 Lluvia de Confeti (Aniversario)'),
        ('OSCURO', '🌙 Modo Oscuro (Elegante)'),
        ('PERU', '🇵🇪 Modo Patrio'),
    ]
    efecto_especial = models.CharField(max_length=20, choices=EFECTOS, default='NINGUNO')
    #banner_promo = models.ImageField(upload_to='campanas/', blank=True, null=True)

    def save(self, *args, **kwargs):
        # Si activo este tema, apago todos los demás de la misma marca
        if self.activo:
            ConfiguracionVisual.objects.filter(marca=self.marca).update(activo=False)
        super().save(*args, **kwargs)

    def __str__(self):
        estado = "🟢 EN USO" if self.activo else "⚪ Guardado"
        return f"{self.nombre} - {estado}"

# ==============================================================================
# 2. ESTRUCTURA OPERATIVA (FRANQUICIA)
# ==============================================================================
class Sede(models.Model):
    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=200)
    telefono = models.CharField(max_length=20)
    #Semaforo
    ESTADOS_OPERATIVOS = [
        ('NORMAL', 'Operacion Normal'), #verde
        ('SATURADO', 'Alta Demanda (+Tiempo)'), #Amarillo
        ('PAUSA', 'Pausa (No recibir pedidos)'), #Naranja
        ('CERRADO', 'Cierre Total'), #Rojo
    ]
    estado_actual = models.CharField(max_length=20, choices=ESTADOS_OPERATIVOS, default='NORMAL')
    #Tiempos por sede
    tiempo_delivery_base = models.IntegerField(default=30, help_text="Tiempo base promedio en esta zona")
    tiempo_extra_saturacion = models.IntegerField(default=45)
    
    def __str__(self):
        return f"{self.nombre} ({self.estado_actual})"


# MODELO DE MESAS (Por SEDE)
class Mesa(models.Model):
    sede = models.ForeignKey(Sede, on_delete=models.CASCADE, related_name="mesas")
    numero = models.CharField(max_length=20) 
    capacidad = models.IntegerField(default=4)
    qr_hash = models.CharField(max_length=100, blank=True, null=True, help_text="Código único para el QR")

    ESTADOS_MESA = [
        ('LIBRE', 'Libre'),
        ('OCUPADA', 'Ocupada'),
        ('PAGANDO','Pagando'),
    ]

    estado = models.CharField(max_length=20, choices=ESTADOS_MESA, default='LIBRE')
    
    def __str__(self):
        return f"{self.sede.nombre} - {self.numero}"
    
# ==============================================================================
# 3. USUARIOS Y ROLES (SEGURIDAD)
# ==============================================================================
class PerfilEmpleado(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='empleado')
    sede = models.ForeignKey(Sede, on_delete=models.SET_NULL, null=True, blank=True)
    
    ROLES = [
        ('ADMIN_GLOBAL', '👑 Super Admin (Dueño)'),
        ('ADMIN_SEDE', '👔 Gerente de Local'),
        ('CAJERO', '💻 Cajero'),
        ('COCINA', '🍳 Chef / Cocina'),
        ('MOZO', '📝 Mesero'),
    ]
    rol = models.CharField(max_length=20, choices=ROLES, default='MOZO')
    pin_acceso = models.CharField(max_length=4, blank=True, null=True, help_text="PIN para Tablet")

    def __str__(self):
        return f"{self.usuario.get_full_name()} ({self.get_rol_display()})"

class Cliente(models.Model):

    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil_cliente')
    dni = models.CharField(max_length=8, unique=True, blank=True, null=True)
    telefono = models.CharField(max_length=15)
    puntos_acumulados = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    NIVELES = [('BRONCE', '🥉 Nuevo'), ('PLATA', '🥈 Frecuente'), ('ORO', '🥇 VIP')]
    nivel = models.CharField(max_length=10, choices=NIVELES, default='BRONCE')

    def __str__(self):
        return f"{self.usuario.first_name} ({self.nivel})"

class DireccionCliente(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='direcciones')
    nombre = models.CharField(max_length=50) # Casa, Oficina
    direccion = models.CharField(max_length=200)
    referencia = models.CharField(max_length=200, blank=True)
    
    def __str__(self):
        return f"{self.nombre}: {self.direccion}"