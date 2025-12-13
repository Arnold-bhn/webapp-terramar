from pathlib import Path
import os

# 1. Calculamos la ruta base (igual que en settings.py)
BASE_DIR = Path(__file__).resolve().parent

# 2. Calculamos la ruta donde DEBERÍA estar el archivo
ruta_esperada = BASE_DIR / 'templates' / 'catalogo' / 'menu.html'

print("-" * 50)
print("DIAGNÓSTICO DE RUTAS")
print("-" * 50)
print(f"1. Estoy ejecutándome en: {BASE_DIR}")
print(f"2. Busco el archivo en:   {ruta_esperada}")
print("-" * 50)

# 3. Verificamos si existe
if ruta_esperada.exists():
    print("✅ ¡ÉXITO! El archivo EXISTE y Python lo puede ver.")
    print("El problema debe estar en settings.py (revisa el Paso 1).")
else:
    print("❌ ERROR: Python NO encuentra el archivo ahí.")
    print("Posibles causas:")
    print("   a) No creaste la carpeta 'templates' en la raíz.")
    print("   b) No creaste la subcarpeta 'catalogo'.")
    print("   c) El archivo se llama 'menu.html.txt' o 'Menu.html'.")
    
    # Vamos a ver qué hay realmente
    ruta_templates = BASE_DIR / 'templates'
    if ruta_templates.exists():
        print(f"\nContenido de la carpeta templates: {os.listdir(ruta_templates)}")
        ruta_cat = ruta_templates / 'catalogo'
        if ruta_cat.exists():
             print(f"Contenido de templates/catalogo: {os.listdir(ruta_cat)}")
    else:
        print("\n⚠️ La carpeta 'templates' NO EXISTE en la raíz.")
print("-" * 50)