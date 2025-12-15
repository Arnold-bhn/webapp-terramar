import os

# Lista EXACTA de los archivos que necesito revisar
archivos_clave = [
    # 1. Configuración general
    'config/settings.py',
    'config/urls.py',
    
    # 2. Catálogo (Productos)
    'catalogo/models.py',
    'catalogo/views.py',
    
    # 3. Pedidos y Carrito (La lógica crítica)
    'pedidos/models.py',
    'pedidos/views.py',
    'pedidos/carrito.py',             # Muy importante
    'pedidos/context_processors.py',  # Muy importante
    'pedidos/urls.py',
    'pedidos/cart_tags.py',           # Para ver tus filtros personalizados
    
    # 4. Core (Si tienes usuarios o utilidades)
    'core/models.py',
]

nombre_archivo_salida = 'codigo_revision.txt'

def exportar_seleccion():
    print(f"Recopilando archivos clave en {nombre_archivo_salida}...")
    
    with open(nombre_archivo_salida, 'w', encoding='utf-8') as salida:
        for ruta_relativa in archivos_clave:
            # Verificamos si el archivo existe antes de intentar leerlo
            if os.path.exists(ruta_relativa):
                separador = "=" * 60
                encabezado = f"\n\n{separador}\nARCHIVO: {ruta_relativa}\n{separador}\n"
                salida.write(encabezado)
                
                try:
                    with open(ruta_relativa, 'r', encoding='utf-8') as f:
                        contenido = f.read()
                        salida.write(contenido)
                    print(f"✔ Agregado: {ruta_relativa}")
                except Exception as e:
                    salida.write(f"\n[Error leyendo archivo: {e}]\n")
            else:
                print(f"❌ No encontrado (saltando): {ruta_relativa}")

    print(f"\n¡Listo! Sube el archivo '{nombre_archivo_salida}' al chat.")

if __name__ == "__main__":
    exportar_seleccion()