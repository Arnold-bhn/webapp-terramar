import os

# Configuración: Carpetas y archivos que NO queremos ver (para no saturar)
IGNORAR_CARPETAS = {'venv', 'env', '__pycache__', '.git', '.idea', '.vscode', 'media', 'static', 'migrations'}
IGNORAR_EXTENSIONES = {'.pyc', '.sqlite3', '.jpg', '.png', '.jpeg', '.css', '.js'}

def mostrar_proyecto():
    ruta_base = os.getcwd()
    print(f"--- LEYENDO PROYECTO EN: {ruta_base} ---")

    for raiz, carpetas, archivos in os.walk(ruta_base):
        # Filtrar carpetas que no queremos leer
        carpetas[:] = [d for d in carpetas if d not in IGNORAR_CARPETAS]

        for archivo in archivos:
            # Ignorar archivos basura o imágenes
            if any(archivo.endswith(ext) for ext in IGNORAR_EXTENSIONES):
                continue
            
            ruta_completa = os.path.join(raiz, archivo)
            ruta_relativa = os.path.relpath(ruta_completa, ruta_base)

            print(f"\n\n{'='*30}")
            print(f"ARCHIVO: {ruta_relativa}")
            print(f"{'='*30}\n")

            try:
                with open(ruta_completa, 'r', encoding='utf-8') as f:
                    contenido = f.read()
                    print(contenido)
            except Exception as e:
                print(f"[No se pudo leer el contenido: {e}]")

if __name__ == "__main__":
    mostrar_proyecto()