import os

# --- CONFIGURACIÓN ---
# Carpetas que NO queremos leer (para no llenar de basura)
carpetas_ignoradas = {
    'venv', '.git', '__pycache__', 'migrations', 'media', 'static', 'staticfiles', '.idea', '.vscode'
}

# Archivos específicos que NO queremos
archivos_ignorados = {
    'db.sqlite3', 'manage.py', '.env', 'exportar_codigo.py', '.DS_Store'
}

# Extensiones de archivos que SÍ queremos leer
extensiones_validas = {'.py', '.html', '.css', '.js'}

nombre_archivo_salida = 'codigo_completo_para_revisar.txt'

def exportar_proyecto():
    print(f"Generando {nombre_archivo_salida}...")
    
    with open(nombre_archivo_salida, 'w', encoding='utf-8') as salida:
        # Recorremos todas las carpetas desde el directorio actual
        for raiz, carpetas, archivos in os.walk("."):
            # Modificamos la lista 'carpetas' en el lugar para que os.walk no entre en las ignoradas
            carpetas[:] = [d for d in carpetas if d not in carpetas_ignoradas]
            
            for archivo in archivos:
                # Verificar extensiones y archivos ignorados
                _, ext = os.path.splitext(archivo)
                if ext in extensiones_validas and archivo not in archivos_ignorados:
                    ruta_completa = os.path.join(raiz, archivo)
                    
                    # Escribimos un separador visual y el nombre del archivo
                    separador = "=" * 60
                    encabezado = f"\n\n{separador}\nARCHIVO: {ruta_completa}\n{separador}\n"
                    salida.write(encabezado)
                    
                    try:
                        with open(ruta_completa, 'r', encoding='utf-8') as f:
                            contenido = f.read()
                            salida.write(contenido)
                    except Exception as e:
                        salida.write(f"[Error leyendo archivo: {e}]")

    print(f"¡Listo! Revisa el archivo '{nombre_archivo_salida}'.")

if __name__ == "__main__":
    exportar_proyecto()