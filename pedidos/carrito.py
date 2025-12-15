# pedidos/carrito.py

import hashlib
from decimal import Decimal
from django.conf import settings
from catalogo.models import Variante, Opcion 

class Carrito:
    def __init__(self, request):
        self.session = request.session
        # Usamos settings.CART_SESSION_ID (debe estar definido en settings.py)
        self.carrito = self.session.get(settings.CART_SESSION_ID) 
        if not self.carrito:
            self.carrito = self.session[settings.CART_SESSION_ID] = {}
        self.request = request

    def _generar_item_key(self, variante_id, opciones_ids=None, notas=''):
        """Genera una clave única (item_key) para el ítem,
            combinando ID, opciones y notas."""
            
        if opciones_ids is None:
            opciones_ids = []
            
        # 1. Asegurar orden y convertir a string para hashing consistente
        # Se asegura que la variante_id sea string
        data_to_hash = (
            str(variante_id), 
            tuple(str(opcion_id) for opcion_id in sorted(opciones_ids)), # Asegura orden y string
            notas.strip().lower()
        )
        
        # 2. Generar el hash
        hash_object = hashlib.md5(str(data_to_hash).encode())
        hash_hex = hash_object.hexdigest()
        
        # 3. Formato final: ID_VARIANTE-HASH_OPCIONES
        return f"{variante_id}-{hash_hex}"

    def agregar(self, variante_id, cantidad=1, precio_unitario=None, opciones_ids=None, notas=''):
        """Agrega un ítem usando item_key."""
            
        item_key = self._generar_item_key(variante_id, opciones_ids, notas)
        
        if item_key not in self.carrito:
            if precio_unitario is None:
                # Si es un nuevo ítem, el precio unitario es obligatorio
                raise ValueError("Precio unitario es requerido para un nuevo ítem.")
            
            # Crear el nuevo ítem
            self.carrito[item_key] = {
                'variante_id': variante_id, 
                'cantidad': 0,
                'precio_unitario': str(precio_unitario), # Guardar como string
                'opciones': opciones_ids if opciones_ids else [],
                'notas': notas.strip()
            }
        
        # Si ya existe, actualiza el precio (solo en caso de ser llamado desde agregar_carrito)
        elif precio_unitario is not None:
             self.carrito[item_key]['precio_unitario'] = str(precio_unitario)

        self.carrito[item_key]['cantidad'] += cantidad
        self.guardar()

    def restar(self, item_key):
        """Resta una unidad del ítem del carrito, o lo elimina si la cantidad es 1."""
        if item_key in self.carrito:
            self.carrito[item_key]['cantidad'] -= 1
            
            if self.carrito[item_key]['cantidad'] <= 0:
                self.eliminar(item_key)
            else:
                self.guardar()

    def eliminar(self, item_key):
        """Elimina completamente el ítem del carrito, usando el item_key."""
        if item_key in self.carrito:
            del self.carrito[item_key]
            self.guardar()

    def guardar(self):
        """Marca la sesión como modificada para que se guarde."""
        self.session.modified = True

    def limpiar(self):
        """Elimina el carrito de la sesión."""
        if self.carrito:
            del self.session[settings.CART_SESSION_ID]
            self.guardar()

    # --- MÉTODOS DE CÁLCULO Y LECTURA ---
    
    def __len__(self):
        """Devuelve el número total de ítems (productos) en el carrito, contando la cantidad."""
        return sum(item.get('cantidad', 0) for item in self.carrito.values())
        
    def get_total_items(self):
        """Alias para __len__ para claridad. (ESTE ES EL MÉTODO FALTANTE)"""
        return len(self)

    def get_total_precio(self):
        """Calcula el costo total de todos los ítems en el carrito."""
        total = Decimal(0)
        for item in self.carrito.values():
            precio_str = item.get('precio_unitario', '0.00')
            cantidad = item.get('cantidad', 0)
            
            try:
                precio = Decimal(precio_str)
                total += precio * cantidad
            except (ValueError, TypeError):
                # Manejo de error si el precio no es convertible a Decimal
                pass 
                
        return total

    def iterar_detalles(self):
        """
        Itera sobre los ítems del carrito y adjunta el objeto Variante,
        y carga los detalles de las Opciones en una consulta eficiente.
        """
        # Se usa .get() para evitar KeyError si un item se corrompe y no tiene 'variante_id'
        variante_ids = set(item.get('variante_id') for item in self.carrito.values() if item.get('variante_id'))
        variantes = Variante.objects.filter(id__in=variante_ids).select_related('plato')
        variantes_dict = {v.id: v for v in variantes}

        # 1. Recolectar todos los IDs de opciones en el carrito
        all_opcion_ids = set()
        for item_data in self.carrito.values():
            all_opcion_ids.update(item_data.get('opciones', []))
            
        # 2. Obtener todos los objetos Opcion en una sola consulta
        opciones = Opcion.objects.filter(id__in=all_opcion_ids).values('id', 'nombre', 'precio_extra')
        opciones_dict = {o['id']: o for o in opciones}

        for item_key, item_data in self.carrito.items():
            # --- VALIDACIÓN DE SEGURIDAD (Para evitar NoReverseMatch) ---
            variante_id = item_data.get('variante_id')
            if not item_key or not variante_id or variante_id not in variantes_dict:
                continue 
            # --------------------------------------------------------

            producto = variantes_dict[variante_id]
            precio_unitario = Decimal(item_data.get('precio_unitario', '0.00'))
            
            # 3. Adjuntar la información de las opciones para la plantilla
            opciones_detalle = []
            for opcion_id in item_data.get('opciones', []):
                opcion = opciones_dict.get(opcion_id)
                if opcion:
                    opciones_detalle.append({
                        'nombre': opcion['nombre'],
                        'precio_extra': opcion['precio_extra']
                    })

            yield {
                'key': item_key, # Clave para la plantilla (item.key)
                'producto': producto,
                'cantidad': item_data.get('cantidad', 0), 
                'precio_unitario': precio_unitario, # Precio unitario (base + opciones)
                'subtotal': precio_unitario * item_data.get('cantidad', 0),
                'opciones_detalle': opciones_detalle,
                'notas': item_data.get('notas', '')
            }

    def get_variante_ids(self):
        """Devuelve una lista de los IDs de las variantes originales para checkear disponibilidad."""
        return list(set(item.get('variante_id') for item in self.carrito.values() if item.get('variante_id')))
        
    def get_cantidad_de_variante(self, variante_id):
        """Devuelve la cantidad total de UNA variante (sin importar las opciones)
            para el badge en el menú.
        """
        total_qty = 0
        for item in self.carrito.values():
            if item.get('variante_id') == variante_id: 
                total_qty += item.get('cantidad', 0) 
        return total_qty