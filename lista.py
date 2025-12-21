import os

ignore = {'venv', '.git', '__pycache__', 'staticfiles', 'media'}

for root, dirs, files in os.walk('.'):
    # Filtrar carpetas ignoradas
    dirs[:] = [d for d in dirs if d not in ignore]
    level = root.replace('.', '').count(os.sep)
    indent = ' ' * 4 * (level)
    print(f'{indent}{os.path.basename(root)}/')
    subindent = ' ' * 4 * (level + 1)
    for f in files:
        print(f'{subindent}{f}')
    if level >= 2: # No profundizar demasiado para no saturar
        dirs[:] = []