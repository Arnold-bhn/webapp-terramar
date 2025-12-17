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
        Genera los items del carrito usando objetos directos para evitar KeyError.
        """
        # 1. Obtener IDs de variantes
        variante_ids = [item['variante_id'] for item in self.carrito.values() if item.get('variante_id')]
        
        # Traemos las variantes con su plato
        variantes = Variante.objects.filter(id__in=variante_ids).select_related('plato')
        variantes_dict = {v.id: v for v in variantes}

        # 2. Obtener IDs de todas las opciones en el carrito
        all_opcion_ids = []
        for item in self.carrito.values():
            opciones_ids = item.get('opciones', [])
            if opciones_ids:
                all_opcion_ids.extend(opciones_ids)
        
        # 3. Traer las opciones CON su grupo (OBJETOS COMPLETOS, NO VALORES)
        # Usamos select_related('grupo') para optimizar y evitar consultas extra
        if all_opcion_ids:
            opciones_db = Opcion.objects.filter(id__in=all_opcion_ids).select_related('grupo')
            opciones_dict = {op.id: op for op in opciones_db}
        else:
            opciones_dict = {}

        # 4. Iterar sobre el carrito de sesión
        for key, item in self.carrito.items():
            variante_id = item.get('variante_id')
            
            # Si la variante ya no existe en BD, saltamos
            if not variante_id or variante_id not in variantes_dict:
                continue

            producto = variantes_dict[variante_id]
            
            # Calcular precios (asegurando tipos de datos)
            precio_base = Decimal(str(item['precio_unitario']))
            cantidad = int(item['cantidad'])
            subtotal = precio_base * cantidad

            # 5. Construir la lista de opciones para el template
            # Usamos el nombre plural 'opciones_detalles' para coincidir con tu HTML
            lista_opciones = []
            
            ids_opciones_item = item.get('opciones', [])
            if ids_opciones_item:
                for op_id in ids_opciones_item:
                    op_id_int = int(op_id)
                    # Verificamos si existe en el diccionario recuperado de la BD
                    if op_id_int in opciones_dict:
                        op_obj = opciones_dict[op_id_int]
                        
                        # AQUÍ ESTABA EL ERROR: Ahora accedemos al objeto de forma segura
                        nombre_grupo = op_obj.grupo.nombre if op_obj.grupo else ''
                        
                        lista_opciones.append({
                            'nombre': op_obj.nombre,
                            'precio': op_obj.precio_extra,
                            'grupo': nombre_grupo
                        })

            yield {
                'key': key,
                'producto': producto,
                'cantidad': cantidad,
                'precio_unitario': precio_base,
                'subtotal': subtotal,
                'opciones_detalles': lista_opciones, # Variable en PLURAL como en tu HTML
                'notas': item.get('notas', '')
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